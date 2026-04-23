from django.contrib import admin
from .models import PipelineStage, Application

@admin.register(PipelineStage)
class PipelineStageAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'color')
    ordering = ('order',)

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'job', 'current_stage', 'created_at')
    list_filter = ('current_stage', 'job')
    search_fields = ('candidate__full_name', 'job__title')
