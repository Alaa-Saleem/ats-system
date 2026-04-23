from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from apps.candidates.models import Candidate
from apps.clients.models import Client
from apps.jobs.models import Job
from apps.accounts.permissions import is_system_admin
from apps.activities.models import ActivityLog
from apps.pipeline.models import Application

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'

    def dispatch(self, request, *args, **kwargs):
        # Super admins go directly to their own control center
        if request.user.is_authenticated and (
            request.user.is_superuser or getattr(request.user, 'role', '') == 'admin'
        ):
            from django.urls import reverse
            return redirect(reverse('superadmin:dashboard'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_admin = is_system_admin(self.request.user)
        user_company = self.request.user.company
        role = self.request.user.role
        context["role"] = role
        context["is_admin"] = is_admin

        try:
            candidates_qs = Candidate.objects.all() if is_admin else Candidate.objects.filter(company=user_company)
            context['candidates_count'] = candidates_qs.count()
        except:
            context['candidates_count'] = 0
            
        try:
            clients_qs = Client.objects.all() if self.request.user.is_superuser else Client.objects.none()
            context['clients_count'] = clients_qs.count()
        except:
            context['clients_count'] = 0
            
        try:
            jobs_qs = Job.objects.filter(status='open') if is_admin else Job.objects.filter(status='open', company=user_company)
            context['jobs_count'] = jobs_qs.count()
        except:
            context['jobs_count'] = 0

        context["can_manage_clients"] = self.request.user.is_superuser
        context["can_manage_candidates"] = role in ["admin", "company_owner", "team_member"]
        context["can_manage_jobs"] = role in ["admin", "company_owner"]
        context["can_access_pipeline"] = role in ["admin", "company_owner", "team_member"]
        
        if role == "candidate":
            user_candidates = Candidate.objects.filter(user_account=self.request.user)
            applications = Application.objects.filter(candidate__in=user_candidates).select_related('job', 'current_stage')
            context['total_applications'] = applications.count()
            
            # Stats breakdown
            in_review, interviews, rejected = 0, 0, 0
            upcoming_interviews = []
            
            for app in applications:
                s_name = app.current_stage.name.lower()
                if 'reject' in s_name or 'مرفوض' in s_name:
                    rejected += 1
                elif 'interview' in s_name or 'مقابلة' in s_name:
                    interviews += 1
                    upcoming_interviews.append(app)
                elif 'accept' not in s_name and 'hired' not in s_name and 'offer' not in s_name:
                    in_review += 1
                    
            context['in_review_count'] = in_review
            context['interviews_count'] = interviews
            context['rejected_count'] = rejected
            context['upcoming_interviews'] = upcoming_interviews[:3]
            
            # Recommended Jobs
            locations = [c.location for c in user_candidates if c.location]
            from django.db.models import Q
            if locations:
                q_loc = Q()
                for loc in locations:
                    q_loc |= Q(location__icontains=loc)
                context['recommended_jobs'] = Job.objects.filter(q_loc, status='open').exclude(id__in=applications.values_list('job_id', flat=True))[:4]
            else:
                context['recommended_jobs'] = Job.objects.filter(status='open').exclude(id__in=applications.values_list('job_id', flat=True)).order_by('-created_at')[:4]
                
            # Notifications
            from apps.candidates.models import CandidateNotification
            context['notifications'] = CandidateNotification.objects.filter(user=self.request.user).order_by('-created_at')[:5]
            context['unread_notifications'] = CandidateNotification.objects.filter(user=self.request.user, is_read=False).count()
            
        else:
            if is_admin:
                context["recent_activities"] = ActivityLog.objects.select_related("user", "company")[:10]
                context["latest_candidates"] = Candidate.objects.select_related("company").order_by("-created_at")[:8]
                context["shortlisted_count"] = Application.objects.filter(current_stage__name__iexact="shortlisted").count()
            else:
                context["recent_activities"] = ActivityLog.objects.filter(company=user_company).select_related("user", "company")[:10]
                context["latest_candidates"] = Candidate.objects.filter(company=user_company).order_by("-created_at")[:8]
                context["shortlisted_count"] = Application.objects.filter(
                    job__company=user_company,
                    current_stage__name__iexact="shortlisted",
                ).count()
            
        return context

# Candidate App routes
from django.views.generic import ListView
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse

class MyApplicationsView(LoginRequiredMixin, ListView):
    template_name = 'dashboard/candidate_applications.html'
    context_object_name = 'applications'
    
    def get_queryset(self):
        if self.request.user.role != 'candidate':
            return Application.objects.none()
        return Application.objects.filter(
            candidate__user_account=self.request.user
        ).select_related('job', 'current_stage').order_by('-created_at')
        
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from apps.candidates.models import CandidateNotification
        ctx['unread_notifications'] = CandidateNotification.objects.filter(user=self.request.user, is_read=False).count()
        return ctx

def mark_notifications_read(request):
    if request.user.is_authenticated and request.user.role == 'candidate':
        from apps.candidates.models import CandidateNotification
        CandidateNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"success": True})

