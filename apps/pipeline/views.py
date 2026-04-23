from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
import json

from .models import PipelineStage, Application, ApplicationComment, ApplicationRating
from apps.jobs.models import Job
from apps.candidates.models import CandidateNotification
from apps.accounts.permissions import (
    is_company_staff, is_system_admin, is_company_owner,
    can_move_pipeline_stage, can_comment_on_candidate,
    can_rate_candidate, can_approve_reject_candidate
)
from apps.activities.services import log_activity
from .email_notifications import send_stage_email


class PipelineBoardView(LoginRequiredMixin, ListView):
    template_name = 'pipeline/board.html'
    context_object_name = 'stages'

    def get_queryset(self):
        if not is_company_staff(self.request.user):
            return PipelineStage.objects.none()
        return PipelineStage.objects.all().prefetch_related(
            'applications',
            'applications__candidate',
            'applications__job',
            'applications__ratings',
            'applications__comments',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if not is_company_staff(user):
            context['jobs'] = Job.objects.none()
            context['selected_job'] = None
            return context

        # Company profile
        company = user.company_profile

        # Job filter
        job_id = self.request.GET.get('job_id')
        selected_job = None
        if job_id:
            try:
                selected_job = Job.objects.get(id=job_id)
                if not is_system_admin(user) and selected_job.company != company:
                    selected_job = None
            except Job.DoesNotExist:
                pass
        context['selected_job'] = selected_job

        # Jobs list for filter dropdown
        if is_system_admin(user):
            context['jobs'] = Job.objects.filter(status='open')
            allowed_applications = Application.objects.select_related(
                'candidate', 'job', 'current_stage'
            ).prefetch_related('ratings', 'comments').annotate(
                avg_score=Avg('ratings__score')
            ).all()
        else:
            context['jobs'] = Job.objects.filter(status='open', company=company)
            allowed_applications = Application.objects.select_related(
                'candidate', 'job', 'current_stage'
            ).prefetch_related('ratings', 'comments').annotate(
                avg_score=Avg('ratings__score')
            ).filter(job__company=company)

        # Filter by selected job
        if selected_job:
            allowed_applications = allowed_applications.filter(job=selected_job)

        # Group by stage
        apps_by_stage = {}
        for application in allowed_applications:
            apps_by_stage.setdefault(application.current_stage_id, []).append(application)

        for stage in context['stages']:
            stage.stage_applications = apps_by_stage.get(stage.id, [])

        # Stats — per stage count and conversions
        stage_stats = []
        total = sum(len(apps) for apps in apps_by_stage.values())
        for stage in context['stages']:
            count = len(stage.stage_applications)
            pct = round((count / total * 100)) if total > 0 else 0
            stage_stats.append({'name': stage.name, 'count': count, 'pct': pct})

        context['stage_stats'] = stage_stats
        context['total_applications'] = total

        # Recent activities
        from apps.activities.models import ActivityLog
        if is_system_admin(user):
            context['recent_activities'] = ActivityLog.objects.order_by('-created_at')[:10]
        elif company:
            context['recent_activities'] = ActivityLog.objects.filter(company=company).order_by('-created_at')[:10]
        else:
            context['recent_activities'] = []

        # Permissions flags
        context['is_owner'] = is_company_owner(user) or is_system_admin(user)
        context['can_shortlist'] = can_move_pipeline_stage(user) # Editor
        context['can_move_stage'] = can_move_pipeline_stage(user) # Editor
        context['can_comment'] = can_comment_on_candidate(user) # Editor, Reviewer, Approver
        context['can_rate'] = can_rate_candidate(user) # Reviewer, Approver
        context['can_approve'] = can_approve_reject_candidate(user) # Approver

        return context


@login_required
@require_POST
def update_application_stage(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    if not can_move_pipeline_stage(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    stage_id = request.POST.get('stage_id')
    try:
        stage = PipelineStage.objects.get(id=stage_id)
        
        if request.user.role == "team_member" and request.user.team_role == "editor":
            terminal_stages = ["offered", "hired", "rejected", "accepted"]
            if application.current_stage.name.lower() in terminal_stages or stage.name.lower() in terminal_stages:
                return JsonResponse({'error': 'غير مصرح لك بنقل كروت من أو إلى المراحل النهائية.'}, status=403)
                
        application.current_stage = stage
        application.save(update_fields=['current_stage', 'updated_at'])
        log_activity(
            user=request.user,
            company=application.job.company,
            action='move_stage',
            description=f"{request.user.username} moved {application.candidate.full_name} to {stage.name}",
        )
        # Notify candidate
        if application.candidate.user_account:
            notif_type = 'interview' if 'interview' in stage.name.lower() or 'مقابلة' in stage.name else 'status_change'
            CandidateNotification.objects.create(
                user=application.candidate.user_account,
                application=application,
                title=f"تحديث لحالة طلبك: {application.job.title}",
                message=f"تم تغيير حالة طلب التوظيف الخاص بك إلى: {stage.name}",
                notification_type=notif_type
            )
        send_stage_email(application)
        return JsonResponse({'success': True, 'stage': stage.name})
    except PipelineStage.DoesNotExist:
        return JsonResponse({'error': 'Stage not found'}, status=404)


@login_required
@require_POST
def toggle_shortlist(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    user = request.user
    if not can_move_pipeline_stage(user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    application.is_shortlisted = not application.is_shortlisted
    application.save(update_fields=['is_shortlisted', 'updated_at'])
    action = 'shortlisted' if application.is_shortlisted else 'removed_shortlist'
    log_activity(
        user=user,
        company=application.job.company,
        action=action,
        description=f"{user.username} {'shortlisted' if application.is_shortlisted else 'removed shortlist for'} {application.candidate.full_name}",
    )
    return JsonResponse({'success': True, 'is_shortlisted': application.is_shortlisted})


@login_required
@require_POST
def add_comment(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    user = request.user
    if not can_comment_on_candidate(user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    text = request.POST.get('text', '').strip()
    if not text:
        return JsonResponse({'error': 'Empty comment'}, status=400)

    comment = ApplicationComment.objects.create(application=application, author=user, text=text)
    log_activity(
        user=user,
        company=application.job.company,
        action='comment',
        description=f"{user.username} commented on {application.candidate.full_name}: {text[:60]}",
    )
    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'author': user.get_full_name() or user.username,
            'text': comment.text,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
        }
    })


@login_required
@require_POST
def rate_application(request, app_id):
    application = get_object_or_404(Application, id=app_id)
    user = request.user
    if not can_rate_candidate(user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    try:
        score = int(request.POST.get('score', 0))
        if score < 1 or score > 5:
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid score'}, status=400)

    rating, _ = ApplicationRating.objects.update_or_create(
        application=application,
        rater=user,
        defaults={'score': score},
    )
    log_activity(
        user=user,
        company=application.job.company,
        action='rate',
        description=f"{user.username} rated {application.candidate.full_name} with {score}/5",
    )
    avg = application.avg_rating()
    return JsonResponse({'success': True, 'my_score': score, 'avg_score': avg})


@login_required
@require_POST
def mark_application_status(request, app_id, status):
    if status not in {"accept", "reject"}:
        messages.error(request, "عملية غير مدعومة.")
        return redirect("pipeline:board")

    application = get_object_or_404(
        Application.objects.select_related("job__company", "candidate"), id=app_id
    )
    if not can_approve_reject_candidate(request.user):
        messages.error(request, "غير مصرح لك بهذه العملية. بصفتك مقيم أو مشغل لا يمكنك اتخاذ القرار النهائي.")
        return redirect("pipeline:board")

    if not is_system_admin(request.user) and application.job.company != request.user.company_profile:
        messages.error(request, "غير مصرح لك بهذه العملية.")
        return redirect("pipeline:board")

    stage_name = "Accepted" if status == "accept" else "Rejected"
    stage_order = 999 if status == "accept" else 1000
    target_stage, _ = PipelineStage.objects.get_or_create(
        name=stage_name,
        defaults={"order": stage_order, "color": "#198754" if status == "accept" else "#dc3545"},
    )
    application.current_stage = target_stage
    application.save(update_fields=["current_stage", "updated_at"])

    log_activity(
        user=request.user,
        company=application.job.company,
        action="accept" if status == "accept" else "reject",
        description=f"{request.user.username} marked {application.candidate.full_name} as {stage_name}",
    )
    
    # Notify candidate
    if application.candidate.user_account:
        notif_type = 'offer' if status == 'accept' else 'rejection'
        title_msg = "تم قبول طلبك 🟢" if status == 'accept' else "تحديث بخصوص طلبك 🔴"
        body_msg = f"مبروك! تم النقل إلى مرحلة القبول النهائي لوظيفة {application.job.title}." if status == 'accept' else f"نعتذر، لم يتم اختيارك لاكمال مراحل التوظيف لوظيفة {application.job.title}."
        CandidateNotification.objects.create(
            user=application.candidate.user_account,
            application=application,
            title=title_msg,
            message=body_msg,
            notification_type=notif_type
        )
    send_stage_email(application)

    messages.success(request, f"تم تحديث حالة المرشح إلى {stage_name}.")
    return redirect("pipeline:board")


@login_required
def link_candidate_view(request):
    if not is_company_staff(request.user):
        return redirect('pipeline:board')

    company = request.user.company_profile
    if request.method == 'POST':
        from .forms import ApplicationForm
        form = ApplicationForm(request.POST, company=company)
        if form.is_valid():
            try:
                app = form.save()
                log_activity(
                    user=request.user,
                    company=app.job.company,
                    action='link_candidate',
                    description=f"{request.user.username} linked {app.candidate.full_name} to {app.job.title}",
                )
                messages.success(request, "تم ربط المرشح بالوظيفة بنجاح.")
                return redirect('pipeline:board')
            except Exception:
                messages.error(request, "المرشح مرتبط مسبقاً بهذه الوظيفة أو حدث خطأ.")
    else:
        from .forms import ApplicationForm
        form = ApplicationForm(company=company)

    return render(request, 'pipeline/link_candidate.html', {'form': form})


@login_required
def get_application_detail(request, app_id):
    """Return full application data as JSON for the card modal."""
    application = get_object_or_404(
        Application.objects.select_related(
            'candidate', 'job', 'current_stage'
        ).prefetch_related('comments__author', 'ratings__rater'),
        id=app_id
    )
    if not is_company_staff(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    user = request.user
    # Build comments list
    comments = [
        {
            'id': c.id,
            'author': c.author.get_full_name() or c.author.username if c.author else 'Unknown',
            'author_initials': (c.author.get_full_name() or c.author.username or 'U')[0].upper() if c.author else 'U',
            'text': c.text,
            'created_at': c.created_at.strftime('%Y-%m-%d %H:%M'),
        }
        for c in application.comments.all()
    ]

    # My rating
    my_rating = 0
    try:
        my_rating = application.ratings.get(rater=user).score
    except ApplicationRating.DoesNotExist:
        pass

    avg_score = application.avg_rating()

    # All stages for move dropdown
    stages = list(PipelineStage.objects.values('id', 'name', 'order'))

    cand = application.candidate

    data = {
        'id': application.id,
        'candidate': {
            'id': cand.id,
            'full_name': cand.full_name,
            'email': cand.email or '',
            'phone': cand.phone or '',
            'current_title': cand.current_title or '',
            'years_of_experience': cand.years_of_experience,
            'location': cand.location or '',
            'availability': cand.availability or '',
            'cv_file': cand.cv_file.url if cand.cv_file else None,
            'notes': cand.notes or '',
        },
        'job': {
            'id': application.job.id,
            'title': application.job.title,
        },
        'current_stage': {
            'id': application.current_stage.id,
            'name': application.current_stage.name,
        },
        'is_shortlisted': application.is_shortlisted,
        'avg_score': avg_score,
        'my_rating': my_rating,
        'comments': comments,
        'stages': stages,
        'permissions': {
            'can_shortlist': can_move_pipeline_stage(user),
            'can_move_stage': can_move_pipeline_stage(user),
            'can_comment': can_comment_on_candidate(user),
            'can_rate': can_rate_candidate(user),
            'can_approve': can_approve_reject_candidate(user),
            'is_owner': is_company_owner(user) or is_system_admin(user),
        },
        'created_at': application.created_at.strftime('%Y-%m-%d'),
    }
    return JsonResponse(data)


@login_required
def search_applications(request):
    """Quick search applications by candidate name or email."""
    if not is_company_staff(request.user):
        return JsonResponse({'results': []})

    q = request.GET.get('q', '').strip()
    job_id = request.GET.get('job_id', '')

    user = request.user
    company = user.company_profile

    if is_system_admin(user):
        qs = Application.objects.select_related('candidate', 'job', 'current_stage').all()
    else:
        qs = Application.objects.select_related('candidate', 'job', 'current_stage').filter(job__company=company)

    if job_id:
        qs = qs.filter(job_id=job_id)

    if q:
        qs = qs.filter(
            Q(candidate__full_name__icontains=q) |
            Q(candidate__email__icontains=q) |
            Q(candidate__phone__icontains=q)
        )

    results = [
        {
            'app_id': app.id,
            'candidate_name': app.candidate.full_name,
            'job_title': app.job.title,
            'stage_name': app.current_stage.name,
            'stage_id': app.current_stage.id,
        }
        for app in qs[:20]
    ]
    return JsonResponse({'results': results})
