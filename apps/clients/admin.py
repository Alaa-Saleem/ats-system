from django.contrib import admin
from .models import Client, ClientContact

class ClientContactInline(admin.TabularInline):
    model = ClientContact
    extra = 1

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'industry', 'phone', 'email', 'owner', 'created_at']
    list_filter = ['industry', 'owner']
    search_fields = ['name', 'phone', 'email']
    inlines = [ClientContactInline]

@admin.register(ClientContact)
class ClientContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'client', 'title', 'phone', 'email', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['name', 'client__name', 'email']
