from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
import json

from .forms import JobForm, PublicJobApplicationForm
from .models import Job
from apps.accounts.permissions import can_manage_jobs, is_system_admin, forbidden_response
from apps.activities.services import log_activity
from apps.pipeline.email_notifications import (
    send_application_received_email,
    send_hr_new_application_email,
)


# ─── Helper ────────────────────────────────────────────────────────────────────

def _get_company_jobs(user):
    """Return base queryset scoped to the user's company (or all for admin)."""
    if is_system_admin(user):
        return Job.objects.all()
    if user.role in ['company_owner', 'team_member']:
        return Job.objects.filter(company=user.company)
    return Job.objects.filter(status='open')


# ─── Job List ──────────────────────────────────────────────────────────────────

@login_required
def job_list(request):
    from apps.pipeline.models import Application, PipelineStage

    jobs_qs = _get_company_jobs(request.user)

    # ── Filters ──
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    location_filter = request.GET.get('location', '')
    department_filter = request.GET.get('department', '')
    sort = request.GET.get('sort', 'newest')

    if q:
        jobs_qs = jobs_qs.filter(title__icontains=q)
    if status_filter:
        jobs_qs = jobs_qs.filter(status=status_filter)
    if location_filter:
        jobs_qs = jobs_qs.filter(location__icontains=location_filter)
    if department_filter:
        jobs_qs = jobs_qs.filter(department__icontains=department_filter)

    # ── Sort ──
    if sort == 'most_applicants':
        jobs_qs = jobs_qs.annotate(applicant_count=Count('applications')).order_by('-applicant_count')
    else:
        jobs_qs = jobs_qs.annotate(applicant_count=Count('applications')).order_by('-created_at')

    # ── Stage stats per job ──
    stages = list(PipelineStage.objects.order_by('order').values('id', 'name'))
    # Build a dict: job_id -> {stage_name: count}
    app_stage_counts = (
        Application.objects
        .filter(job__in=jobs_qs)
        .values('job_id', 'current_stage__name')
        .annotate(cnt=Count('id'))
    )
    stage_map = {}  # {job_id: {stage_name: count}}
    for row in app_stage_counts:
        stage_map.setdefault(row['job_id'], {})[row['current_stage__name']] = row['cnt']

    jobs_with_stats = []
    today = timezone.now().date()
    for job in jobs_qs:
        job_stages = stage_map.get(job.id, {})
        jobs_with_stats.append({
            'job': job,
            'applicant_count': job.applicant_count,
            'stage_stats': job_stages,
            'is_expired': job.application_deadline and job.application_deadline < today,
            'is_accepting': job.is_accepting_applications,
        })

    # ── Filter dropdowns ──
    all_jobs_base = _get_company_jobs(request.user)
    locations = all_jobs_base.exclude(location='').values_list('location', flat=True).distinct()
    departments = all_jobs_base.exclude(department='').values_list('department', flat=True).distinct()

    return render(request, 'jobs/job_list.html', {
        'jobs_with_stats': jobs_with_stats,
        'can_add_job': can_manage_jobs(request.user),
        'stages': stages,
        # filter state
        'q': q,
        'status_filter': status_filter,
        'location_filter': location_filter,
        'department_filter': department_filter,
        'sort': sort,
        'locations': locations,
        'departments': departments,
        # form for modal
        'form': JobForm(),
        'today': today,
    })


# ─── Add Job ───────────────────────────────────────────────────────────────────

def _save_custom_fields(request, job):
    """Parse and save custom fields from POST data."""
    from .models import JobCustomField

    labels    = request.POST.getlist('cf_label[]')
    types     = request.POST.getlist('cf_type[]')
    options   = request.POST.getlist('cf_options[]')
    ids       = request.POST.getlist('cf_id[]')
    requireds = request.POST.getlist('cf_required[]')

    # Delete fields that were removed by the user
    existing_ids = [int(i) for i in ids if i]
    job.custom_fields.exclude(id__in=existing_ids).delete()

    for order, (label, ftype) in enumerate(zip(labels, types)):
        label = label.strip()
        if not label:
            continue
        opts  = options[order] if order < len(options) else ''
        req   = str(order) in requireds
        field_id = ids[order] if order < len(ids) and ids[order] else None

        if field_id:
            JobCustomField.objects.filter(id=field_id, job=job).update(
                label=label, field_type=ftype, options=opts,
                is_required=req, order=order
            )
        else:
            JobCustomField.objects.create(
                job=job, label=label, field_type=ftype,
                options=opts, is_required=req, order=order
            )


@login_required
def add_job(request):
    if not can_manage_jobs(request.user):
        return forbidden_response()

    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)

            # Robust company resolution
            company = (
                request.user.company
                or getattr(request.user, 'owned_company', None)
            )
            if not company:
                messages.error(request, 'لا يمكن إضافة وظيفة: حسابك غير مرتبط بشركة.')
                return render(request, 'jobs/add_job.html', {'form': form, 'custom_fields': []})

            job.company = company
            job.save()
            _save_custom_fields(request, job)
            try:
                log_activity(
                    user=request.user,
                    company=job.company,
                    action="create_job",
                    description=f"{request.user.username} created job {job.title}",
                )
            except Exception:
                pass  # log failure should never block job creation

            messages.success(request, f'تم نشر وظيفة «{job.title}» بنجاح.')
            return redirect('jobs:list')
        # Form is invalid — fall through to render with errors
    else:
        form = JobForm()

    return render(request, 'jobs/add_job.html', {'form': form, 'custom_fields': []})


# ─── Edit Job ─────────────────────────────────────────────────────────────────

@login_required
def edit_job(request, job_id):
    if not can_manage_jobs(request.user):
        return forbidden_response()

    job = get_object_or_404(Job, id=job_id)
    if not is_system_admin(request.user) and job.company != request.user.company_profile:
        return forbidden_response()

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            _save_custom_fields(request, job)
            log_activity(
                user=request.user,
                company=job.company,
                action="edit_job",
                description=f"{request.user.username} edited job {job.title}",
            )
            messages.success(request, 'تم تحديث الوظيفة بنجاح.')
            return redirect('jobs:list')

    # GET — return job data as JSON for pre-filling modal
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'id': job.id,
            'title': job.title,
            'description': job.description,
            'required_skills': job.required_skills,
            'location': job.location,
            'department': job.department,
            'job_type': job.job_type,
            'salary': str(job.salary) if job.salary else '',
            'application_deadline': job.application_deadline.isoformat() if job.application_deadline else '',
            'status': job.status,
        }
        return JsonResponse(data)

    form = JobForm(instance=job)
    custom_fields = list(job.custom_fields.all())
    return render(request, 'jobs/add_job.html', {'form': form, 'job': job, 'custom_fields': custom_fields})


# ─── Close Job ────────────────────────────────────────────────────────────────

@login_required
@require_POST
def close_job(request, job_id):
    if not can_manage_jobs(request.user):
        return forbidden_response()

    job = get_object_or_404(Job, id=job_id)
    if not is_system_admin(request.user) and job.company != request.user.company_profile:
        return forbidden_response()

    job.status = 'closed'
    job.save(update_fields=['status', 'updated_at'])
    log_activity(
        user=request.user,
        company=job.company,
        action="close_job",
        description=f"{request.user.username} closed job {job.title}",
    )
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    messages.success(request, f'تم إغلاق الوظيفة "{job.title}" بنجاح.')
    return redirect('jobs:list')


# ─── Reopen Job ───────────────────────────────────────────────────────────────

@login_required
@require_POST
def reopen_job(request, job_id):
    if not can_manage_jobs(request.user):
        return forbidden_response()

    job = get_object_or_404(Job, id=job_id)
    if not is_system_admin(request.user) and job.company != request.user.company_profile:
        return forbidden_response()

    job.status = 'open'
    job.save(update_fields=['status', 'updated_at'])
    log_activity(
        user=request.user,
        company=job.company,
        action="reopen_job",
        description=f"{request.user.username} reopened job {job.title}",
    )
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    messages.success(request, f'تم إعادة فتح الوظيفة "{job.title}".')
    return redirect('jobs:list')


# ─── Job Analytics (JSON) ─────────────────────────────────────────────────────

@login_required
def job_analytics(request, job_id):
    from apps.pipeline.models import Application
    from django.db.models.functions import TruncDate

    job = get_object_or_404(Job, id=job_id)
    if not is_system_admin(request.user) and job.company != request.user.company_profile:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    applications = Application.objects.filter(job=job)
    total = applications.count()

    # Per day (last 30 days)
    from datetime import timedelta
    start = timezone.now().date() - timedelta(days=29)
    daily = (
        applications
        .filter(created_at__date__gte=start)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    daily_labels = [(start + timedelta(days=i)).isoformat() for i in range(30)]
    daily_map = {str(r['day']): r['count'] for r in daily}
    daily_data = [daily_map.get(d, 0) for d in daily_labels]

    # Per stage
    stage_counts = (
        applications
        .values('current_stage__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    stage_labels = [r['current_stage__name'] for r in stage_counts]
    stage_data = [r['count'] for r in stage_counts]

    # Source breakdown
    sources = (
        applications
        .exclude(source='')
        .values('source')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    return JsonResponse({
        'total': total,
        'daily_labels': daily_labels,
        'daily_data': daily_data,
        'stage_labels': stage_labels,
        'stage_data': stage_data,
        'sources': list(sources),
        'job_title': job.title,
    })


# ─── Job Applications ─────────────────────────────────────────────────────────

@login_required
def job_applications(request, job_id):
    from apps.pipeline.models import Application

    job = get_object_or_404(Job, id=job_id)
    if not is_system_admin(request.user) and job.company != request.user.company_profile:
        return forbidden_response()

    applications = (
        Application.objects
        .filter(job=job)
        .select_related('candidate', 'current_stage')
        .order_by('-created_at')
    )

    return render(request, 'jobs/job_applications.html', {
        'job': job,
        'applications': applications,
        'total': applications.count(),
    })


# ─── Public Apply ─────────────────────────────────────────────────────────────

def public_apply_to_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    # Check if job is accepting applications
    if not job.is_accepting_applications:
        return render(request, 'jobs/public_apply.html', {'job': job, 'closed': True})

    if request.method == "POST":
        # Check if candidate exists for this company
        phone = request.POST.get("phone")
        from apps.candidates.models import Candidate
        candidate_instance = Candidate.objects.filter(company=job.company, phone=phone).first()

        if candidate_instance:
            form = PublicJobApplicationForm(request.POST, request.FILES, instance=candidate_instance)
        else:
            form = PublicJobApplicationForm(request.POST, request.FILES)

        if form.is_valid():
            candidate = form.save(commit=False)
            if getattr(job.company, 'owner', None) is None:
                messages.error(request, "لا يمكن استقبال الطلب حالياً لأن الشركة غير مرتبطة بمالك.")
                return redirect("public:landing")
            candidate.owner = job.company.owner
            candidate.company = job.company
            if request.user.is_authenticated and request.user.role == 'candidate':
                candidate.user_account = request.user
            notes = candidate.notes or ""
            candidate.notes = f"{notes}\n\nApplied for: {job.title}".strip()
            candidate.save()

            from apps.pipeline.models import Application, PipelineStage
            
            # Check if application already exists for this exact job
            if Application.objects.filter(candidate=candidate, job=job).exists():
                messages.info(request, "لقد قمت بالتقديم على هذه الوظيفة مسبقاً.")
                return redirect("public:landing")

            first_stage, _ = PipelineStage.objects.get_or_create(
                name="Applied",
                defaults={"order": 1, "color": "#6c757d"}
            )
            new_app = Application.objects.create(
                candidate=candidate,
                job=job,
                current_stage=first_stage,
                source="Public Page"
            )

            # Save custom field answers
            from apps.pipeline.models import ApplicationAnswer
            for field in job.custom_fields.all():
                if field.field_type in ('file_upload', 'image_upload'):
                    uploaded = request.FILES.get(f'cf_file_{field.id}')
                    if uploaded:
                        ApplicationAnswer.objects.create(
                            application=new_app, field=field, file_answer=uploaded
                        )
                else:
                    answer_text = request.POST.get(f'cf_{field.id}', '').strip()
                    if answer_text:
                        ApplicationAnswer.objects.create(
                            application=new_app, field=field, text_answer=answer_text
                        )

            send_application_received_email(new_app)
            send_hr_new_application_email(new_app)

            messages.success(request, "تم استلام طلبك بنجاح.")
            return redirect("public:landing")
    else:
        form = PublicJobApplicationForm()

    return render(request, "jobs/public_apply.html", {"form": form, "job": job, "closed": False})


# ─── Candidate Job Browse ──────────────────────────────────────────────────────

@login_required
def candidate_job_browse(request):
    """Dedicated job browsing page for logged-in candidates with Easy Apply."""
    from apps.pipeline.models import Application
    from apps.candidates.models import Candidate

    jobs_qs = Job.objects.filter(status='open').select_related('company').order_by('-created_at')

    # Filters
    q = request.GET.get('q', '').strip()
    location_filter = request.GET.get('location', '')
    job_type_filter = request.GET.get('job_type', '')
    sort_filter = request.GET.get('sort', 'newest')

    if q:
        jobs_qs = jobs_qs.filter(Q(title__icontains=q) | Q(company__company_name__icontains=q))
    if location_filter:
        jobs_qs = jobs_qs.filter(location__icontains=location_filter)
    if job_type_filter:
        jobs_qs = jobs_qs.filter(job_type=job_type_filter)
    if sort_filter == 'salary_high':
        jobs_qs = jobs_qs.order_by('-salary', '-created_at')

    # IDs of jobs the candidate already applied to
    user_candidates = Candidate.objects.filter(user_account=request.user)
    applied_job_ids = set(
        Application.objects.filter(candidate__in=user_candidates).values_list('job_id', flat=True)
    )

    # Get candidate profile for easy apply prefill
    candidate_profile = user_candidates.first()

    # Dropdown filters
    locations = Job.objects.filter(status='open').exclude(location='').values_list('location', flat=True).distinct()
    job_types = Job.objects.filter(status='open').exclude(job_type='').values_list('job_type', flat=True).distinct()

    now = timezone.now()
    from datetime import timedelta
    urgent_date = now.date() + timedelta(days=3)
    new_date = now - timedelta(hours=24)

    return render(request, 'jobs/candidate_browse.html', {
        'jobs': jobs_qs[:60],
        'applied_job_ids': applied_job_ids,
        'candidate_profile': candidate_profile,
        'locations': locations,
        'job_types_list': job_types,
        'q': q,
        'location_filter': location_filter,
        'job_type_filter': job_type_filter,
        'sort_filter': sort_filter,
        'urgent_date': urgent_date,
        'new_date': new_date,
        'today_date': now.date(),
    })


# ─── Easy Apply ───────────────────────────────────────────────────────────────

@login_required
def easy_apply(request, job_id):
    """One-click apply using existing candidate profile. Supports optional edit before submit."""
    from apps.candidates.models import Candidate
    from apps.pipeline.models import Application, PipelineStage

    job = get_object_or_404(Job, id=job_id)

    if not job.is_accepting_applications:
        messages.error(request, "هذه الوظيفة لم تعد تقبل طلبات.")
        return redirect('jobs:browse')

    if request.user.role != 'candidate':
        return redirect('jobs:list')

    # Find or preview the candidate's existing profile
    candidate = Candidate.objects.filter(user_account=request.user).first()

    if request.method == 'POST':
        # Build/update the candidate record for this specific company
        company_candidate = Candidate.objects.filter(
            user_account=request.user, company=job.company
        ).first()

        full_name  = request.POST.get('full_name', '').strip()
        phone      = request.POST.get('phone', '').strip()
        email      = request.POST.get('email', '').strip()
        location   = request.POST.get('location', '').strip()
        experience = request.POST.get('years_of_experience', '')
        title      = request.POST.get('current_title', '').strip()

        if not full_name or not phone:
            messages.error(request, "الاسم ورقم الهاتف مطلوبان.")
            return render(request, 'jobs/easy_apply.html', {
                'job': job, 'candidate': candidate
            })

        if company_candidate:
            # Update the existing record found via user_account + company
            company_candidate.full_name = full_name
            company_candidate.phone = phone
            company_candidate.email = email
            company_candidate.location = location
            company_candidate.current_title = title
            if experience:
                try:
                    company_candidate.years_of_experience = int(experience)
                except ValueError:
                    pass
            if request.FILES.get('cv_file'):
                company_candidate.cv_file = request.FILES['cv_file']
            company_candidate.user_account = request.user
            company_candidate.save()
            applied_candidate = company_candidate
        else:
            if getattr(job.company, 'owner', None) is None:
                messages.error(request, "لا يمكن الاستمرار، الشركة غير مرتبطة بمالك.")
                return redirect('jobs:browse')
            cv = request.FILES.get('cv_file') or (candidate.cv_file if candidate else None)
            # Use get_or_create keyed on the unique_together fields (company, phone)
            # to gracefully handle any existing record with the same phone
            applied_candidate, created = Candidate.objects.get_or_create(
                company=job.company,
                phone=phone,
                defaults={
                    'user_account': request.user,
                    'owner': job.company.owner,
                    'full_name': full_name,
                    'email': email,
                    'location': location,
                    'current_title': title,
                    'years_of_experience': int(experience) if experience else None,
                    'cv_file': cv or '',
                }
            )
            if not created:
                # Record existed (phone collision) — update it and link to this user
                applied_candidate.full_name = full_name
                applied_candidate.email = email
                applied_candidate.location = location
                applied_candidate.current_title = title
                applied_candidate.user_account = request.user
                if experience:
                    try:
                        applied_candidate.years_of_experience = int(experience)
                    except ValueError:
                        pass
                if cv:
                    applied_candidate.cv_file = cv
                applied_candidate.save()

        # Check duplicate application
        if Application.objects.filter(candidate=applied_candidate, job=job).exists():
            messages.info(request, "لقد تقدمت لهذه الوظيفة مسبقاً!")
            return redirect('jobs:browse')

        first_stage, _ = PipelineStage.objects.get_or_create(
            name="Applied",
            defaults={"order": 1, "color": "#6c757d"}
        )
        new_app = Application.objects.create(
            candidate=applied_candidate,
            job=job,
            current_stage=first_stage,
            source="Easy Apply"
        )
        # Save custom field answers
        from apps.pipeline.models import ApplicationAnswer
        from .models import JobCustomField
        for field in job.custom_fields.all():
            if field.field_type in ('file_upload', 'image_upload'):
                uploaded = request.FILES.get(f'cf_file_{field.id}')
                if uploaded:
                    ApplicationAnswer.objects.create(
                        application=new_app, field=field, file_answer=uploaded
                    )
            else:
                answer_text = request.POST.get(f'cf_{field.id}', '').strip()
                if answer_text:
                    ApplicationAnswer.objects.create(
                        application=new_app, field=field, text_answer=answer_text
                    )
        send_application_received_email(new_app)
        send_hr_new_application_email(new_app)
        messages.success(request, f"✅ تم التقديم على وظيفة «{job.title}» بنجاح!")
        return redirect('dashboard:my_applications')

    # GET → show prefill form
    return render(request, 'jobs/easy_apply.html', {
        'job': job,
        'candidate': candidate,
    })
