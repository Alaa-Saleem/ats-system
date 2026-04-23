from django.urls import path
from . import views

app_name = 'candidates'

urlpatterns = [
    path('', views.candidate_list, name='list'),
    path('create/', views.add_candidate, name='create'),
    path('<int:pk>/', views.candidate_detail, name='detail'),
    path('<int:pk>/edit/', views.edit_candidate, name='edit'),
    path('<int:pk>/delete/', views.delete_candidate, name='delete'),
]
