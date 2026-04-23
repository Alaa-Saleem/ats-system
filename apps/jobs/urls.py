from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.job_list, name='list'),
    path('add/', views.add_job, name='add'),
    path('<int:job_id>/edit/', views.edit_job, name='edit'),
    path('<int:job_id>/close/', views.close_job, name='close'),
    path('<int:job_id>/reopen/', views.reopen_job, name='reopen'),
    path('<int:job_id>/analytics/', views.job_analytics, name='analytics'),
    path('<int:job_id>/applications/', views.job_applications, name='applications'),
    path('<int:job_id>/public-apply/', views.public_apply_to_job, name='public_apply'),
    path('<int:job_id>/easy-apply/', views.easy_apply, name='easy_apply'),
    path('browse/', views.candidate_job_browse, name='browse'),
]
