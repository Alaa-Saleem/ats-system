from django.urls import path
from apps.accounts.views import landing_page

app_name = "public"

urlpatterns = [
    path("", landing_page, name="landing"),
]
