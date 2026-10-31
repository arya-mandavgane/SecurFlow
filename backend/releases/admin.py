from django.contrib import admin
from .models import ReleaseRequest

@admin.register(ReleaseRequest)
class ReleaseRequestAdmin(admin.ModelAdmin):
    list_display = ('fdr', 'requested_by', 'status', 'refund_order_number', 'decision_date', 'created_at')
    list_filter = ('status',)
    search_fields = ('fdr__fdr_number', 'refund_order_number', 'requested_by__username')
