"""
Super Admin Views — Full management panel for superusers only.
All views are protected by @superadmin_required.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta

from apps.accounts.models import Company, User
from apps.jobs.models import Job
from apps.candidates.models import Candidate
from apps.pipeline.models import Application, PipelineStage
from apps.activities.models import ActivityLog

from .decorators import superadmin_required


# ══════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════

@superadmin_required
def dashboard(request):
    now = timezone.now()
    today = now.date()

    # Core stats
    companies_count = Company.objects.filter(is_deleted=False).count()
    jobs_count      = Job.objects.filter(is_deleted=False).count()
    candidates_count = Candidate.objects.filter(is_deleted=False).count()
    applications_count = Application.objects.filter(is_deleted=False).count()

    # Trash counts
    trash_companies = Company.objects.filter(is_deleted=True).count()
    trash_jobs      = Job.objects.filter(is_deleted=True).count()
    trash_candidates = Candidate.objects.filter(is_deleted=True).count()
    trash_apps      = Application.objects.filter(is_deleted=True).count()
    trash_total     = trash_companies + trash_jobs + trash_candidates + trash_apps

    # Daily applications chart — last 14 days
    chart_labels = []
    chart_data   = []
    for i in range(13, -1, -1):
        day = today - timedelta(days=i)
        count = Application.objects.filter(
            is_deleted=False,
            created_at__date=day
        ).count()
        chart_labels.append(day.strftime('%d %b'))
        chart_data.append(count)

    # Recent candidates
    recent_candidates = Candidate.objects.filter(is_deleted=False).select_related('company').order_by('-created_at')[:8]

    # Recent jobs
    recent_jobs = Job.objects.filter(is_deleted=False).select_related('company').order_by('-created_at')[:8]

    # Alerts
    closing_soon = Job.objects.filter(
        is_deleted=False,
        status='open',
        application_deadline__lte=today + timedelta(days=3),
        application_deadline__gte=today,
    ).select_related('company')[:5]

    no_applicants = Job.objects.filter(
        is_deleted=False,
        status='open',
    ).annotate(app_count=Count('applications')).filter(app_count=0).select_related('company')[:5]

    # Stage distribution
    stages = PipelineStage.objects.annotate(
        count=Count('applications', filter=Q(applications__is_deleted=False))
    ).order_by('order')

    context = {
        'companies_count': companies_count,
        'jobs_count': jobs_count,
        'candidates_count': candidates_count,
        'applications_count': applications_count,
        'trash_total': trash_total,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'recent_candidates': recent_candidates,
        'recent_jobs': recent_jobs,
        'closing_soon': closing_soon,
        'no_applicants': no_applicants,
        'stages': stages,
        'active_tab': 'dashboard',
    }
    return render(request, 'superadmin/dashboard.html', context)


# ══════════════════════════════════════════════════════════════
#  COMPANIES
# ══════════════════════════════════════════════════════════════

@superadmin_required
def companies_list(request):
    qs = Company.objects.filter(is_deleted=False).annotate(
        jobs_count=Count('jobs', filter=Q(jobs__is_deleted=False))
    ).order_by('-id')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(company_name__icontains=q) | Q(industry__icontains=q))

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'superadmin/companies.html', {
        'page_obj': page,
        'q': q,
        'active_tab': 'companies',
    })


@superadmin_required
def company_detail(request, pk):
    company = get_object_or_404(Company, pk=pk, is_deleted=False)
    jobs = Job.objects.filter(company=company, is_deleted=False).annotate(
        app_count=Count('applications', filter=Q(applications__is_deleted=False))
    ).order_by('-created_at')
    return render(request, 'superadmin/company_detail.html', {
        'company': company,
        'jobs': jobs,
        'active_tab': 'companies',
    })


@superadmin_required
def company_edit(request, pk):
    company = get_object_or_404(Company, pk=pk, is_deleted=False)
    if request.method == 'POST':
        company.company_name = request.POST.get('company_name', company.company_name)
        company.industry     = request.POST.get('industry', company.industry)
        company.location     = request.POST.get('location', company.location)
        company.phone        = request.POST.get('phone', company.phone)
        company.website      = request.POST.get('website', company.website)
        company.description  = request.POST.get('description', company.description)
        company.save()
        _log_action(request.user, f"Edited company: {company.company_name}")
        messages.success(request, f"تم تحديث بيانات الشركة: {company.company_name}")
        return redirect('superadmin:company_detail', pk=pk)
    return render(request, 'superadmin/company_edit.html', {
        'company': company,
        'active_tab': 'companies',
    })


@superadmin_required
def company_toggle(request, pk):
    """Toggle disabled state — stores disabled state in a UserProfile field."""
    company = get_object_or_404(Company, pk=pk, is_deleted=False)
    if request.method == 'POST':
        owner = company.owner
        if owner:
            owner.is_active = not owner.is_active
            owner.save(update_fields=['is_active'])
            status = "مُفعَّلة" if owner.is_active else "مُعطَّلة"
            _log_action(request.user, f"Toggled company {company.company_name} → {status}")
            messages.success(request, f"تم تغيير حالة الشركة إلى: {status}")
        else:
            messages.warning(request, "لا يوجد مالك مرتبط بهذه الشركة.")
    return redirect('superadmin:companies_list')


@superadmin_required
def company_delete(request, pk):
    company = get_object_or_404(Company, pk=pk, is_deleted=False)
    if request.method == 'POST':
        company.soft_delete()
        _log_action(request.user, f"Soft-deleted company: {company.company_name}")
        messages.success(request, f"تم نقل الشركة '{company.company_name}' إلى سلة المحذوفات.")
    return redirect('superadmin:companies_list')


# ══════════════════════════════════════════════════════════════
#  JOBS
# ══════════════════════════════════════════════════════════════

@superadmin_required
def jobs_list(request):
    qs = Job.objects.filter(is_deleted=False).select_related('company').annotate(
        app_count=Count('applications', filter=Q(applications__is_deleted=False))
    ).order_by('-created_at')

    q       = request.GET.get('q', '').strip()
    status  = request.GET.get('status', '')
    company = request.GET.get('company', '')

    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(company__company_name__icontains=q))
    if status:
        qs = qs.filter(status=status)
    if company:
        qs = qs.filter(company_id=company)

    companies = Company.objects.filter(is_deleted=False).order_by('company_name')
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'superadmin/jobs.html', {
        'page_obj': page,
        'q': q,
        'status_filter': status,
        'company_filter': company,
        'companies': companies,
        'active_tab': 'jobs',
    })


@superadmin_required
def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk, is_deleted=False)
    applications = Application.objects.filter(job=job, is_deleted=False).select_related(
        'candidate', 'current_stage'
    ).order_by('-created_at')
    return render(request, 'superadmin/job_detail.html', {
        'job': job,
        'applications': applications,
        'active_tab': 'jobs',
    })


@superadmin_required
def job_close(request, pk):
    job = get_object_or_404(Job, pk=pk, is_deleted=False)
    if request.method == 'POST':
        job.status = 'closed'
        job.save(update_fields=['status'])
        _log_action(request.user, f"Closed job: {job.title}")
        messages.success(request, f"تم إغلاق الوظيفة: {job.title}")
    return redirect('superadmin:jobs_list')


@superadmin_required
def job_delete(request, pk):
    job = get_object_or_404(Job, pk=pk, is_deleted=False)
    if request.method == 'POST':
        job.soft_delete()
        _log_action(request.user, f"Soft-deleted job: {job.title}")
        messages.success(request, f"تم نقل الوظيفة '{job.title}' إلى سلة المحذوفات.")
    return redirect('superadmin:jobs_list')


# ══════════════════════════════════════════════════════════════
#  CANDIDATES
# ══════════════════════════════════════════════════════════════

@superadmin_required
def candidates_list(request):
    qs = Candidate.objects.filter(is_deleted=False).select_related('company').annotate(
        app_count=Count('applications', filter=Q(applications__is_deleted=False))
    ).order_by('-created_at')

    q       = request.GET.get('q', '').strip()
    company = request.GET.get('company', '')

    if q:
        qs = qs.filter(Q(full_name__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q))
    if company:
        qs = qs.filter(company_id=company)

    companies = Company.objects.filter(is_deleted=False).order_by('company_name')
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'superadmin/candidates.html', {
        'page_obj': page,
        'q': q,
        'company_filter': company,
        'companies': companies,
        'active_tab': 'candidates',
    })


@superadmin_required
def candidate_detail(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk, is_deleted=False)
    applications = Application.objects.filter(candidate=candidate, is_deleted=False).select_related(
        'job', 'current_stage'
    ).order_by('-created_at')
    return render(request, 'superadmin/candidate_detail.html', {
        'candidate': candidate,
        'applications': applications,
        'active_tab': 'candidates',
    })


@superadmin_required
def candidate_delete(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk, is_deleted=False)
    if request.method == 'POST':
        candidate.soft_delete()
        _log_action(request.user, f"Soft-deleted candidate: {candidate.full_name}")
        messages.success(request, f"تم نقل المرشح '{candidate.full_name}' إلى سلة المحذوفات.")
    return redirect('superadmin:candidates_list')


# ══════════════════════════════════════════════════════════════
#  APPLICATIONS
# ══════════════════════════════════════════════════════════════

@superadmin_required
def applications_list(request):
    qs = Application.objects.filter(is_deleted=False).select_related(
        'candidate', 'job', 'job__company', 'current_stage'
    ).order_by('-created_at')

    q       = request.GET.get('q', '').strip()
    stage   = request.GET.get('stage', '')
    company = request.GET.get('company', '')

    if q:
        qs = qs.filter(
            Q(candidate__full_name__icontains=q) |
            Q(job__title__icontains=q)
        )
    if stage:
        qs = qs.filter(current_stage_id=stage)
    if company:
        qs = qs.filter(job__company_id=company)

    stages    = PipelineStage.objects.all().order_by('order')
    companies = Company.objects.filter(is_deleted=False).order_by('company_name')
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'superadmin/applications.html', {
        'page_obj': page,
        'q': q,
        'stage_filter': stage,
        'company_filter': company,
        'stages': stages,
        'companies': companies,
        'active_tab': 'applications',
    })


@superadmin_required
def application_detail(request, pk):
    application = get_object_or_404(Application, pk=pk, is_deleted=False)
    stages = PipelineStage.objects.all().order_by('order')
    return render(request, 'superadmin/application_detail.html', {
        'application': application,
        'stages': stages,
        'active_tab': 'applications',
    })


@superadmin_required
def application_stage(request, pk):
    application = get_object_or_404(Application, pk=pk, is_deleted=False)
    if request.method == 'POST':
        stage_id = request.POST.get('stage_id')
        stage = get_object_or_404(PipelineStage, pk=stage_id)
        old_stage = application.current_stage.name
        application.current_stage = stage
        application.save(update_fields=['current_stage'])
        _log_action(
            request.user,
            f"Changed stage for {application.candidate.full_name}: {old_stage} → {stage.name}"
        )
        messages.success(request, f"تم تغيير المرحلة إلى: {stage.name}")
    return redirect('superadmin:application_detail', pk=pk)


@superadmin_required
def application_delete(request, pk):
    application = get_object_or_404(Application, pk=pk, is_deleted=False)
    if request.method == 'POST':
        application.soft_delete()
        _log_action(request.user, f"Soft-deleted application ID {pk}")
        messages.success(request, "تم نقل الطلب إلى سلة المحذوفات.")
    return redirect('superadmin:applications_list')


# ══════════════════════════════════════════════════════════════
#  TRASH
# ══════════════════════════════════════════════════════════════

@superadmin_required
def trash(request):
    tab = request.GET.get('tab', 'companies')

    trash_companies    = Company.objects.filter(is_deleted=True).order_by('-deleted_at')
    trash_jobs         = Job.objects.filter(is_deleted=True).select_related('company').order_by('-deleted_at')
    trash_candidates   = Candidate.objects.filter(is_deleted=True).select_related('company').order_by('-deleted_at')
    trash_applications = Application.objects.filter(is_deleted=True).select_related(
        'candidate', 'job', 'current_stage'
    ).order_by('-deleted_at')

    return render(request, 'superadmin/trash.html', {
        'trash_companies': trash_companies,
        'trash_jobs': trash_jobs,
        'trash_candidates': trash_candidates,
        'trash_applications': trash_applications,
        'active_tab': 'trash',
        'current_tab': tab,
        'trash_total': (
            trash_companies.count() + trash_jobs.count() +
            trash_candidates.count() + trash_applications.count()
        ),
    })


@superadmin_required
def restore_item(request, model, pk):
    """Generic restore: model is one of company|job|candidate|application."""
    if request.method != 'POST':
        return redirect('superadmin:trash')

    MODEL_MAP = {
        'company': Company,
        'job': Job,
        'candidate': Candidate,
        'application': Application,
    }
    ModelClass = MODEL_MAP.get(model)
    if not ModelClass:
        messages.error(request, "نموذج غير معروف.")
        return redirect('superadmin:trash')

    obj = get_object_or_404(ModelClass, pk=pk, is_deleted=True)
    obj.restore()
    _log_action(request.user, f"Restored {model} ID {pk}")
    messages.success(request, "تمت الاستعادة بنجاح.")
    return redirect('superadmin:trash')


@superadmin_required
def permanent_delete(request, model, pk):
    """Permanently delete from DB. No recovery."""
    if request.method != 'POST':
        return redirect('superadmin:trash')

    MODEL_MAP = {
        'company': Company,
        'job': Job,
        'candidate': Candidate,
        'application': Application,
    }
    ModelClass = MODEL_MAP.get(model)
    if not ModelClass:
        messages.error(request, "نموذج غير معروف.")
        return redirect('superadmin:trash')

    obj = get_object_or_404(ModelClass, pk=pk, is_deleted=True)
    obj.delete()
    _log_action(request.user, f"Permanently deleted {model} ID {pk}")
    messages.success(request, "تم الحذف النهائي بنجاح.")
    return redirect('superadmin:trash')


# ══════════════════════════════════════════════════════════════
#  ACTIVITY LOGS
# ══════════════════════════════════════════════════════════════

@superadmin_required
def activity_logs(request):
    qs = ActivityLog.objects.select_related('user', 'company').order_by('-created_at')

    action  = request.GET.get('action', '')
    company = request.GET.get('company', '')
    q       = request.GET.get('q', '').strip()

    if action:
        qs = qs.filter(action=action)
    if company:
        qs = qs.filter(company_id=company)
    if q:
        qs = qs.filter(Q(description__icontains=q) | Q(user__username__icontains=q))

    action_choices = ActivityLog.ACTION_CHOICES
    companies = Company.objects.filter(is_deleted=False).order_by('company_name')
    paginator = Paginator(qs, 30)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'superadmin/activity_logs.html', {
        'page_obj': page,
        'action_filter': action,
        'company_filter': company,
        'q': q,
        'action_choices': action_choices,
        'companies': companies,
        'active_tab': 'activity_logs',
    })


# ══════════════════════════════════════════════════════════════
#  BULK ACTIONS
# ══════════════════════════════════════════════════════════════

@superadmin_required
def bulk_action(request):
    if request.method != 'POST':
        return redirect('superadmin:dashboard')

    action = request.POST.get('action')
    model  = request.POST.get('model')
    ids    = request.POST.getlist('selected_ids')

    if not ids:
        messages.warning(request, "لم تحدد أي عناصر.")
        return redirect(request.META.get('HTTP_REFERER', 'superadmin:dashboard'))

    MODEL_MAP = {
        'company': Company,
        'job': Job,
        'candidate': Candidate,
        'application': Application,
    }
    ModelClass = MODEL_MAP.get(model)
    if not ModelClass:
        messages.error(request, "نموذج غير صالح.")
        return redirect('superadmin:dashboard')

    qs = ModelClass.objects.filter(pk__in=ids)

    if action == 'soft_delete':
        for obj in qs:
            if not obj.is_deleted:
                obj.soft_delete()
        _log_action(request.user, f"Bulk soft-deleted {len(ids)} {model}(s)")
        messages.success(request, f"تم نقل {len(ids)} عناصر إلى سلة المحذوفات.")

    elif action == 'restore':
        for obj in qs:
            if obj.is_deleted:
                obj.restore()
        _log_action(request.user, f"Bulk restored {len(ids)} {model}(s)")
        messages.success(request, f"تم استعادة {len(ids)} عناصر.")

    elif action == 'permanent_delete':
        qs.delete()
        _log_action(request.user, f"Bulk permanently deleted {len(ids)} {model}(s)")
        messages.success(request, f"تم الحذف النهائي لـ {len(ids)} عناصر.")

    elif action == 'close_jobs' and model == 'job':
        qs.update(status='closed')
        _log_action(request.user, f"Bulk closed {len(ids)} jobs")
        messages.success(request, f"تم إغلاق {len(ids)} وظيفة.")

    return redirect(request.META.get('HTTP_REFERER', 'superadmin:dashboard'))


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

def _log_action(user, description):
    """Create a simple activity log for superadmin actions."""
    try:
        company = getattr(user, 'company', None) or Company.objects.first()
        if company:
            ActivityLog.objects.create(
                user=user,
                company=company,
                action='move_stage',  # reuse existing action type
                description=f"[SuperAdmin] {description}",
            )
    except Exception:
        pass
