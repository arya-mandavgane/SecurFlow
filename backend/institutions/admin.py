from django.contrib import admin
from .models import Institution

@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'aicte_id', 'state', 'contact_person', 'email', 'phone', 'created_at')
    search_fields = ('name', 'aicte_id', 'state', 'email')
    list_filter = ('state',)
