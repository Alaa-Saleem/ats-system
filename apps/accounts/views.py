from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from smtplib import SMTPException
from .forms import (
    CandidateRegisterForm,
    CompanyRegisterForm,
    TeamMemberCreateForm,
    TeamMemberPermissionForm,
)
from .models import Company, User
from apps.jobs.models import Job
from apps.activities.models import ActivityLog
from apps.activities.services import log_activity

from django.utils import timezone
from datetime import timedelta
from django.db.models import Count


# ── EMAIL VERIFICATION RE-ENABLED ─────────────────────────────────────────────
def _send_email_verification(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    verify_path = reverse("accounts:verify_email", kwargs={"uidb64": uid, "token": token})
    verify_url = request.build_absolute_uri(verify_path)
    try:
        send_mail(
            subject="Verify your email",
            message=(
                f"Hello {user.username},\n\n"
                f"Please verify your account email by opening this link:\n{verify_url}\n\n"
                "If you did not create this account, you can ignore this message."
            ),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except SMTPException:
        return False
# ─────────────────────────────────────────────────────────────────────────────


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"

    def form_valid(self, form):
        user = form.get_user()
        # ── EMAIL VERIFICATION CHECK RE-ENABLED ──────────────────────────────
        if user.role in ["company_owner", "candidate"] and not getattr(user, 'is_verified', True):
            messages.error(
                self.request,
                "يرجى تأكيد البريد الإلكتروني أولاً. تم إرسال رابط التفعيل إلى بريدك."
            )
            return redirect("accounts:login")
        # ─────────────────────────────────────────────────────────────────────
        return super().form_valid(form)

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser or getattr(user, 'role', '') == 'admin':
            return reverse('superadmin:dashboard')
        return super().get_success_url()


def landing_page(request):
    if request.user.is_authenticated:
        if request.user.is_superuser or getattr(request.user, 'role', '') == 'admin':
            return redirect('superadmin:dashboard')
        return redirect("dashboard:home")

    # Fetch jobs (including closed jobs because we want to show them as disabled)
    jobs_qs = Job.objects.select_related("company")

    # --- Filtering ---
    q = request.GET.get('q', '').strip()
    location_filter = request.GET.get('location', '')
    job_type_filter = request.GET.get('job_type', '')
    sort_filter = request.GET.get('sort', 'newest')

    if q:
        jobs_qs = jobs_qs.filter(title__icontains=q)
    if location_filter:
        jobs_qs = jobs_qs.filter(location__icontains=location_filter)
    if job_type_filter:
        jobs_qs = jobs_qs.filter(job_type=job_type_filter)

    # --- Sorting ---
    if sort_filter == 'salary_high':
        # Sort by salary ascending (assuming numeric and nulls last, but since it's sqlite we'll just order normally. Nulls can be tricky, so we order by -salary)
        jobs_qs = jobs_qs.order_by('-salary', '-created_at')
    else:
        # Default: newest first
        jobs_qs = jobs_qs.order_by('-created_at')

    # Get dropdown options
    locations = Job.objects.exclude(location='').values_list('location', flat=True).distinct()
    job_types = Job.objects.exclude(job_type='').values_list('job_type', flat=True).distinct()
    
    # Process badges context
    now = timezone.now()
    urgent_date = now.date() + timedelta(days=3)
    new_date = now - timedelta(hours=24)

    return render(request, "public/landing.html", {
        "jobs": jobs_qs[:50],  # Limit to 50 for performance
        "locations": locations,
        "job_types_list": job_types,
        "q": q,
        "location_filter": location_filter,
        "job_type_filter": job_type_filter,
        "sort_filter": sort_filter,
        "urgent_date": urgent_date,
        "new_date": new_date,
        "today_date": now.date()
    })


def register_company(request):
    if request.method == 'POST':
        form = CompanyRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'company_owner'
            user.is_owner = True
            user.is_active = True
            user.is_verified = False  # Need verification
            user.save()
            company = Company.objects.create(
                owner=user,
                company_name=f"{user.username} Company",
                description="",
                industry="",
                location="",
                phone="",
            )
            user.company = company
            user.save(update_fields=["company"])
            # ── EMAIL VERIFICATION RE-ENABLED ─────────────────────────────────
            sent = _send_email_verification(request, user)
            if sent:
                messages.success(request, "تم إنشاء الحساب. تحقق من بريدك لتفعيله ثم سجل الدخول.")
            else:
                messages.warning(
                    request,
                    "تم إنشاء الحساب، لكن فشل إرسال رسالة التفعيل بسبب إعدادات البريد. "
                    "حدّث إعدادات SMTP ثم أعد المحاولة."
                )
            # ─────────────────────────────────────────────────────────────────
            return redirect('accounts:login')
    else:
        form = CompanyRegisterForm()

    return render(request, 'accounts/register_company.html', {'form': form})


def register_candidate(request):
    if request.method == 'POST':
        form = CandidateRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'candidate'
            user.is_active = True
            user.is_verified = False  # Need verification
            user.save()
            
            # Create a global Candidate profile
            from apps.candidates.models import Candidate
            Candidate.objects.create(
                user_account=user,
                owner=user,  # Using the user themselves as the owner of their global profile
                company=None,
                full_name=form.cleaned_data.get('full_name'),
                phone=form.cleaned_data.get('phone'),
                email=user.email,
                current_title=form.cleaned_data.get('current_title', ''),
                years_of_experience=form.cleaned_data.get('years_of_experience') or None,
                location=form.cleaned_data.get('location', ''),
                cv_file=request.FILES.get('cv_file')
            )
            
            # ── EMAIL VERIFICATION RE-ENABLED ─────────────────────────────────
            sent = _send_email_verification(request, user)
            if sent:
                messages.success(request, "تم إنشاء الحساب. تحقق من بريدك لتفعيله ثم سجل الدخول.")
            else:
                messages.warning(
                    request,
                    "تم إنشاء الحساب، لكن فشل إرسال رسالة التفعيل بسبب إعدادات البريد. "
                    "حدّث إعدادات SMTP ثم أعد المحاولة."
                )
            # ─────────────────────────────────────────────────────────────────
            return redirect('accounts:login')
    else:
        form = CandidateRegisterForm()

    return render(request, 'accounts/register_candidate.html', {'form': form})


def verify_email(request, uidb64, token):
    # ── EMAIL VERIFICATION RE-ENABLED ─────────────────────────────────────────
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user and default_token_generator.check_token(user, token):
        if not getattr(user, 'is_verified', True):
            user.is_verified = True
        user.save(update_fields=["is_verified"])
        messages.success(request, "تم تأكيد البريد الإلكتروني بنجاح. يمكنك تسجيل الدخول الآن.")
    else:
        messages.error(request, "رابط التفعيل غير صالح أو منتهي الصلاحية.")
    # ─────────────────────────────────────────────────────────────────────────
    return redirect("accounts:login")

def company_dashboard(request):
    if request.user.role not in ['company_owner', 'team_member', 'admin']:
        return redirect('home')  # لو حاول مرشح الوصول للصفحة

    if request.user.role == "admin" or request.user.is_superuser:
        jobs = Job.objects.all()
    else:
        jobs = Job.objects.filter(company=request.user.company)  # عرض الوظائف المرتبطة بالشركة

    return render(request, 'accounts/company_dashboard.html', {'jobs': jobs})


@login_required
def team_management(request):
    if request.user.role not in ["company_owner", "admin"]:
        return redirect("dashboard:home")

    if request.user.role == "admin":
        members = User.objects.filter(role="team_member").select_related("company")
    else:
        members = User.objects.filter(role="team_member", company=request.user.company)

    create_form = TeamMemberCreateForm()
    return render(
        request,
        "accounts/team_management.html",
        {
            "members": members,
            "create_form": create_form,
        },
    )


@login_required
def add_team_member(request):
    if request.user.role not in ["company_owner", "admin"]:
        return redirect("dashboard:home")

    if request.method != "POST":
        return redirect("accounts:team_management")

    form = TeamMemberCreateForm(request.POST)
    if not form.is_valid():
        messages.error(request, "تعذر إنشاء العضو. تأكد من صحة البيانات.")
        return redirect("accounts:team_management")

    member = form.save(commit=False)
    member.role = "team_member"
    if not request.user.company:
        messages.error(request, "لا يمكن إضافة عضو بدون شركة مرتبطة بالمستخدم الحالي.")
        return redirect("accounts:team_management")
    member.company = request.user.company
    member.save()
    log_activity(
        user=request.user,
        company=request.user.company,
        action="team_add",
        description=f"{request.user.username} added team member {member.username}",
    )
    messages.success(request, "تم إضافة عضو الفريق بنجاح.")
    return redirect("accounts:team_management")


@login_required
def edit_team_member_permissions(request, user_id):
    if request.user.role not in ["company_owner", "admin"]:
        return redirect("dashboard:home")

    member = get_object_or_404(User, id=user_id, role="team_member")
    if request.user.role != "admin" and member.company != request.user.company:
        return redirect("dashboard:home")

    if request.method != "POST":
        return redirect("accounts:team_management")

    form = TeamMemberPermissionForm(request.POST, instance=member)
    if form.is_valid():
        form.save()
        log_activity(
            user=request.user,
            company=member.company,
            action="team_update",
            description=f"{request.user.username} updated permissions for {member.username}",
        )
        messages.success(request, "تم تحديث الصلاحيات.")
    else:
        messages.error(request, "فشل تحديث الصلاحيات.")
    return redirect("accounts:team_management")


@login_required
def remove_team_member(request, user_id):
    if request.user.role not in ["company_owner", "admin"]:
        return redirect("dashboard:home")

    member = get_object_or_404(User, id=user_id, role="team_member")
    if request.user.role != "admin" and member.company != request.user.company:
        return redirect("dashboard:home")

    if request.method != "POST":
        return redirect("accounts:team_management")

    if member.id == request.user.id:
        messages.error(request, "لا يمكنك حذف نفسك.")
        return redirect("accounts:team_management")

    member_name = member.username
    member_company = member.company
    member.delete()
    log_activity(
        user=request.user,
        company=member_company,
        action="team_remove",
        description=f"{request.user.username} removed team member {member_name}",
    )
    messages.success(request, "تم حذف عضو الفريق.")
    return redirect("accounts:team_management")


@login_required
def activity_log_list(request):
    if request.user.role not in ["company_owner", "admin"]:
        return redirect("dashboard:home")

    if request.user.role == "admin":
        logs = ActivityLog.objects.select_related("user", "company")[:100]
    else:
        logs = ActivityLog.objects.filter(company=request.user.company).select_related("user", "company")[:100]
    return render(request, "accounts/activity_log.html", {"logs": logs})

    
