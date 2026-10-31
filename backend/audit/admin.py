from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'actor', 'action', 'entity_type', 'entity_id', 'ip_address')
    list_filter = ('action', 'entity_type')
    search_fields = ('entity_id', 'actor__username', 'ip_address')
    readonly_fields = ('actor', 'action', 'entity_type', 'entity_id', 'before_state', 'after_state', 'ip_address', 'user_agent', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
