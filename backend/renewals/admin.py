from django.contrib import admin
from .models import RenewalRecord

@admin.register(RenewalRecord)
class RenewalRecordAdmin(admin.ModelAdmin):
    list_display = ('original_fdr', 'new_fdr', 'renewal_type', 'renewal_date', 'created_at')
    list_filter = ('renewal_type',)
    search_fields = ('original_fdr__fdr_number', 'new_fdr__fdr_number')
