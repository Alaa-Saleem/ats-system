from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("id", "company", "user", "action", "created_at")
    list_filter = ("action", "company", "created_at")
    search_fields = ("description", "user__username", "company__company_name")
