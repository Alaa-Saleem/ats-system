from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import CandidateForm
from .models import Candidate
from apps.accounts.permissions import (
    can_view_sensitive_candidate_data,
    is_company_staff,
    is_system_admin,
    forbidden_response,
)
from apps.activities.services import log_activity

@login_required
def add_candidate(request):
    if not is_company_staff(request.user):
        return forbidden_response()

    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            # تعيين الـ owner (المستخدم الحالي) للمرشح
            candidate = form.save(commit=False)  # لا تحفظ الآن
            candidate.owner = request.user  # ربط الـ owner بالمستخدم الحالي
            candidate.company = request.user.company
            candidate.save()  # الآن احفظه
            log_activity(
                user=request.user,
                company=candidate.company,
                action="create_candidate",
                description=f"{request.user.username} created candidate {candidate.full_name}",
            )
            return redirect('candidates:create')  # إعادة التوجيه
    else:
        form = CandidateForm()
    return render(request, 'candidates/add_candidate.html', {'form': form})

@login_required
def candidate_list(request):
    if not is_company_staff(request.user):
        return forbidden_response()

    from apps.jobs.models import Job

    if is_system_admin(request.user):
        candidates = Candidate.objects.all()
        jobs_for_filter = (
            Job.objects
            .filter(applications__isnull=False)
            .distinct()
            .order_by('title')
        )
    else:
        candidates = Candidate.objects.filter(company=request.user.company)
        jobs_for_filter = (
            Job.objects
            .filter(company=request.user.company, applications__candidate__company=request.user.company)
            .distinct()
            .order_by('title')
        )

    selected_job_id = (request.GET.get('job_id') or '').strip()
    if selected_job_id:
        candidates = candidates.filter(applications__job_id=selected_job_id).distinct()

    return render(
        request,
        'candidates/candidate_list.html',
        {
            'candidates': candidates,
            'jobs_for_filter': jobs_for_filter,
            'selected_job_id': selected_job_id,
            'hide_sensitive': not can_view_sensitive_candidate_data(request.user),
        },
    )

@login_required
def edit_candidate(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)  # استرجاع المرشح بناءً على الـ ID
    if not is_system_admin(request.user) and candidate.company != request.user.company:
        return forbidden_response()

    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            form.save()
            return redirect('candidates:list')  # بعد التعديل يتم إعادة التوجيه إلى قائمة المرشحين
    else:
        form = CandidateForm(instance=candidate)

    return render(request, 'candidates/edit_candidate.html', {'form': form, 'candidate': candidate})

@login_required
def delete_candidate(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    if not is_system_admin(request.user) and candidate.company != request.user.company:
        return forbidden_response()

    if request.method == 'POST':
        candidate.delete()
        return redirect('candidates:list')  # بعد الحذف يتم إعادة التوجيه إلى قائمة المرشحين

    return render(request, 'candidates/delete_candidate.html', {'candidate': candidate})

@login_required
def candidate_detail(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    if not is_system_admin(request.user) and candidate.company != request.user.company:
        return forbidden_response()

    from apps.pipeline.models import Application
    latest_application = (
        Application.objects
        .filter(candidate=candidate)
        .select_related('job', 'current_stage')
        .prefetch_related('custom_answers__field')
        .order_by('-created_at')
        .first()
    )

    context = {
        'candidate': candidate,
        'application': latest_application,
        'application_answers': (
            latest_application.custom_answers.all() if latest_application else []
        ),
        'hide_sensitive': not can_view_sensitive_candidate_data(request.user),
        'can_comment': request.user.role in ["admin", "company_owner"] or request.user.can_comment,
        'can_rate': request.user.role in ["admin", "company_owner"] or request.user.can_rate,
        'can_accept_reject': request.user.role in ["admin", "company_owner"],
    }
    return render(request, 'candidates/candidate_detail.html', context)

