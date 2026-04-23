from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('my-applications/', views.MyApplicationsView.as_view(), name='my_applications'),
    path('notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),
]
