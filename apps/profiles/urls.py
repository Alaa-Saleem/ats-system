from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    # Private
    path('',        views.edit_profile,   name='edit'),
    path('edit/',   views.edit_profile,   name='edit_profile'),
    path('avatar/delete/', views.delete_avatar, name='delete_avatar'),

    # Public shareable pages
    path('c/<str:username>/',     views.public_candidate, name='public_candidate'),
    path('company/<slug:slug>/',  views.public_company,   name='public_company'),
]
