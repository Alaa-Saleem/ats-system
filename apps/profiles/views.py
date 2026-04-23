from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash, get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils.translation import gettext as _

from apps.accounts.models import Company
from apps.candidates.models import Candidate
from .forms import (
    PersonalInfoForm, CandidateProfessionalForm,
    CandidateDocumentsForm, CompanyInfoForm, StaffRoleForm,
)

User = get_user_model()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_global_candidate(user):
    """Return the user's global (no-company) candidate profile, or None."""
    return Candidate.objects.filter(user_account=user, company=None).first()


def _completion_hints(user):
    """Return list of suggestion strings for incomplete fields."""
    hints = []
    if not user.avatar:           hints.append(_("أضف صورة شخصية"))
    if not user.get_full_name():  hints.append(_("أضف اسمك الكامل"))
    if not user.phone:            hints.append(_("أضف رقم هاتفك"))
    if not user.location:         hints.append(_("أضف موقعك الجغرافي"))
    if not user.bio:              hints.append(_("أضف نبذة عنك"))
    if user.role == 'candidate':
        cand = _get_global_candidate(user)
        if cand:
            if not cand.cv_file:       hints.append(_("أضف سيرتك الذاتية (CV)"))
            if not cand.skills:        hints.append(_("أضف مهاراتك"))
            if not cand.current_title: hints.append(_("أضف مسمّاك الوظيفي"))
    return hints


# ─── Edit Profile (main tabbed view) ─────────────────────────────────────────

@login_required
def edit_profile(request):
    user = request.user
    candidate = _get_global_candidate(user)
    company   = user.company_profile

    # Build tab visibility flags
    is_candidate     = user.role == 'candidate'
    is_company_admin = user.role == 'company_owner'
    is_staff         = user.role == 'team_member'
    is_superadmin    = user.is_superuser or user.role == 'admin'

    active_tab = request.GET.get('tab', 'personal')

    # Initialise forms (GET)
    personal_form     = PersonalInfoForm(instance=user)
    password_form     = PasswordChangeForm(user)
    professional_form = CandidateProfessionalForm(instance=candidate) if candidate else None
    documents_form    = CandidateDocumentsForm(instance=candidate) if candidate else None
    company_form      = CompanyInfoForm(instance=company) if is_company_admin and company else None
    staff_form        = StaffRoleForm(instance=user) if is_staff else None

    if request.method == 'POST':
        form_type = request.POST.get('form_type', '')

        # ── Personal ──────────────────────────────────────────────────────────
        if form_type == 'personal':
            personal_form = PersonalInfoForm(request.POST, request.FILES, instance=user)
            if personal_form.is_valid():
                personal_form.save()
                messages.success(request, "✅ تم تحديث البيانات الشخصية بنجاح.")
                return redirect(f"{request.path}?tab=personal")
            active_tab = 'personal'

        # ── Delete avatar ──────────────────────────────────────────────────────
        elif form_type == 'delete_avatar':
            if user.avatar:
                user.avatar.delete(save=True)
            messages.success(request, "تم حذف الصورة الشخصية.")
            return redirect(f"{request.path}?tab=personal")

        # ── Professional (candidate) ───────────────────────────────────────────
        elif form_type == 'professional' and candidate:
            professional_form = CandidateProfessionalForm(request.POST, instance=candidate)
            if professional_form.is_valid():
                professional_form.save()
                messages.success(request, "✅ تم تحديث البيانات المهنية بنجاح.")
                return redirect(f"{request.path}?tab=professional")
            active_tab = 'professional'

        # ── Documents (candidate) ─────────────────────────────────────────────
        elif form_type == 'documents' and candidate:
            documents_form = CandidateDocumentsForm(request.POST, request.FILES, instance=candidate)
            if documents_form.is_valid():
                documents_form.save()
                messages.success(request, "✅ تم تحديث المستندات بنجاح.")
                return redirect(f"{request.path}?tab=documents")
            active_tab = 'documents'

        # ── Company ───────────────────────────────────────────────────────────
        elif form_type == 'company' and is_company_admin and company:
            company_form = CompanyInfoForm(request.POST, request.FILES, instance=company)
            if company_form.is_valid():
                company_form.save()
                messages.success(request, "✅ تم تحديث بيانات الشركة بنجاح.")
                return redirect(f"{request.path}?tab=company")
            active_tab = 'company'

        # ── Staff role ────────────────────────────────────────────────────────
        elif form_type == 'staff' and is_staff:
            staff_form = StaffRoleForm(request.POST, instance=user)
            if staff_form.is_valid():
                staff_form.save()
                messages.success(request, "✅ تم تحديث المسمى الوظيفي.")
                return redirect(f"{request.path}?tab=role")
            active_tab = 'role'

        # ── Password ──────────────────────────────────────────────────────────
        elif form_type == 'password':
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                pw_user = password_form.save()
                update_session_auth_hash(request, pw_user)
                messages.success(request, "✅ تم تغيير كلمة المرور بنجاح.")
                return redirect(f"{request.path}?tab=account")
            active_tab = 'account'

        # ── Delete account ────────────────────────────────────────────────────
        elif form_type == 'delete_account' and not is_superadmin:
            confirm = request.POST.get('confirm_delete', '').strip()
            if confirm == user.username:
                user.is_active = False
                user.save(update_fields=['is_active'])
                from django.contrib.auth import logout
                logout(request)
                messages.info(request, "تم تعطيل حسابك.")
                return redirect('accounts:login')
            else:
                messages.error(request, "تأكيد الحذف غير صحيح — يرجى كتابة اسم المستخدم بدقة.")
                active_tab = 'account'

    context = {
        'active_tab':        active_tab,
        'personal_form':     personal_form,
        'password_form':     password_form,
        'professional_form': professional_form,
        'documents_form':    documents_form,
        'company_form':      company_form,
        'staff_form':        staff_form,
        'candidate':         candidate,
        'company':           company,
        'is_candidate':      is_candidate,
        'is_company_admin':  is_company_admin,
        'is_staff':          is_staff,
        'is_superadmin':     is_superadmin,
        'completion':        user.profile_completion,
        'hints':             _completion_hints(user),
        'public_url':        _public_url(request, user),   # full absolute URL
    }
    return render(request, 'profiles/edit_profile.html', context)


def _public_url(request, user):
    """Return the full shareable absolute URL for this user's public profile."""
    from django.urls import reverse, NoReverseMatch
    try:
        if user.role == 'candidate':
            rel = reverse('profiles:public_candidate', kwargs={'username': user.username})
            return request.build_absolute_uri(rel)
        if user.role == 'company_owner':
            company = user.company_profile
            if company and company.slug:
                rel = reverse('profiles:public_company', kwargs={'slug': company.slug})
                return request.build_absolute_uri(rel)
    except NoReverseMatch:
        pass
    return None


# ─── Public Candidate Page ────────────────────────────────────────────────────

def public_candidate(request, username):
    user = get_object_or_404(User, username=username, is_active=True, role='candidate')
    candidate = Candidate.objects.filter(user_account=user, company=None).first()
    skills = []
    if candidate and candidate.skills:
        skills = [s.strip() for s in candidate.skills.split(',') if s.strip()]
    return render(request, 'profiles/public_candidate.html', {
        'profile_user': user,
        'candidate':    candidate,
        'skills':       skills,
    })


# ─── Public Company Page ──────────────────────────────────────────────────────

def public_company(request, slug):
    from apps.jobs.models import Job
    company = get_object_or_404(Company, slug=slug, is_deleted=False)
    jobs = Job.objects.filter(company=company, status='open').order_by('-created_at')
    return render(request, 'profiles/public_company.html', {
        'company': company,
        'jobs':    jobs,
    })


# ─── Avatar delete via AJAX ───────────────────────────────────────────────────

@login_required
@require_POST
def delete_avatar(request):
    user = request.user
    if user.avatar:
        user.avatar.delete(save=True)
    return JsonResponse({'ok': True})
