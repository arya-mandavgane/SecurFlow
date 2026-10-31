from django.contrib import admin
from .models import FDR, FDRDocument

class FDRDocumentInline(admin.TabularInline):
    model = FDRDocument
    extra = 0
    readonly_fields = ('checksum', 'file_size', 'upload_timestamp')

@admin.register(FDR)
class FDRAdmin(admin.ModelAdmin):
    list_display = ('fdr_number', 'institution', 'bank_name', 'amount', 'maturity_date', 'status', 'lien_marked_aicte', 'created_at')
    list_filter = ('status', 'bank_name', 'lien_marked_aicte')
    search_fields = ('fdr_number', 'bank_name', 'institution__name', 'institution__aicte_id')
    inlines = [FDRDocumentInline]

@admin.register(FDRDocument)
class FDRDocumentAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'fdr', 'file_type', 'file_size', 'upload_timestamp')
    list_filter = ('file_type',)
