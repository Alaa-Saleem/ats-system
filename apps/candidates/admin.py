from django.contrib import admin
from .models import Candidate


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'phone',
        'email',
        'current_title',
        'owner',
        'created_at',
    )
    search_fields = ('full_name', 'phone', 'email')
    list_filter = ('owner', 'created_at')
