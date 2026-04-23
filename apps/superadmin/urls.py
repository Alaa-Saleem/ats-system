from django.urls import path
from . import views

app_name = 'superadmin'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Companies
    path('companies/', views.companies_list, name='companies_list'),
    path('companies/<int:pk>/', views.company_detail, name='company_detail'),
    path('companies/<int:pk>/edit/', views.company_edit, name='company_edit'),
    path('companies/<int:pk>/toggle/', views.company_toggle, name='company_toggle'),
    path('companies/<int:pk>/delete/', views.company_delete, name='company_delete'),

    # Jobs
    path('jobs/', views.jobs_list, name='jobs_list'),
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('jobs/<int:pk>/close/', views.job_close, name='job_close'),
    path('jobs/<int:pk>/delete/', views.job_delete, name='job_delete'),

    # Candidates
    path('candidates/', views.candidates_list, name='candidates_list'),
    path('candidates/<int:pk>/', views.candidate_detail, name='candidate_detail'),
    path('candidates/<int:pk>/delete/', views.candidate_delete, name='candidate_delete'),

    # Applications
    path('applications/', views.applications_list, name='applications_list'),
    path('applications/<int:pk>/', views.application_detail, name='application_detail'),
    path('applications/<int:pk>/stage/', views.application_stage, name='application_stage'),
    path('applications/<int:pk>/delete/', views.application_delete, name='application_delete'),

    # Trash
    path('trash/', views.trash, name='trash'),
    path('restore/<str:model>/<int:pk>/', views.restore_item, name='restore_item'),
    path('permanent-delete/<str:model>/<int:pk>/', views.permanent_delete, name='permanent_delete'),

    # Activity Logs
    path('activity-logs/', views.activity_logs, name='activity_logs'),

    # Bulk Actions
    path('bulk-action/', views.bulk_action, name='bulk_action'),
]
