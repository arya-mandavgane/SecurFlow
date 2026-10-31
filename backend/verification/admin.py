from django.contrib import admin
from .models import VerificationRecord

@admin.register(VerificationRecord)
class VerificationRecordAdmin(admin.ModelAdmin):
    list_display = ('fdr', 'official', 'status', 'is_automated_draft', 'timestamp')
    list_filter = ('status', 'is_automated_draft')
    search_fields = ('fdr__fdr_number', 'official__username', 'remarks')
