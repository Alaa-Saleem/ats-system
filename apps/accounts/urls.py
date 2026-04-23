from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='accounts:login'), name='logout'),
    path('register/company/', views.register_company, name='register_company'),
    path('register/candidate/', views.register_candidate, name='register_candidate'),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('dashboard/', views.company_dashboard, name='company_dashboard'),  # رابط الداشبورد
    path('team/', views.team_management, name='team_management'),
    path('team/add/', views.add_team_member, name='add_team_member'),
    path('team/<int:user_id>/permissions/', views.edit_team_member_permissions, name='edit_team_member_permissions'),
    path('team/<int:user_id>/remove/', views.remove_team_member, name='remove_team_member'),
    path('activities/', views.activity_log_list, name='activity_log'),
]
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

urlpatterns += [
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.html',
        success_url=reverse_lazy('accounts:password_reset_done')
    ), name='password_reset'),

    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url=reverse_lazy('accounts:password_reset_complete')
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
]