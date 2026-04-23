from django.urls import path
from . import views

app_name = 'pipeline'

urlpatterns = [
    path('', views.PipelineBoardView.as_view(), name='board'),
    path('link/', views.link_candidate_view, name='link_candidate'),
    path('application/<int:app_id>/<str:status>/', views.mark_application_status, name='mark_application_status'),

    # API endpoints
    path('api/update-stage/<int:app_id>/', views.update_application_stage, name='update_stage'),
    path('api/toggle-shortlist/<int:app_id>/', views.toggle_shortlist, name='toggle_shortlist'),
    path('api/add-comment/<int:app_id>/', views.add_comment, name='add_comment'),
    path('api/rate/<int:app_id>/', views.rate_application, name='rate_application'),
    path('api/application/<int:app_id>/', views.get_application_detail, name='application_detail'),
    path('api/search/', views.search_applications, name='search'),
]
