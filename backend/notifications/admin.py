from django.contrib import admin
from .models import Notification, AlertRule

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'institution', 'channel', 'notification_type', 'sent_status', 'is_read', 'created_at')
    list_filter = ('channel', 'notification_type', 'sent_status', 'is_read')
    search_fields = ('title', 'message', 'user__username', 'institution__name')

@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'days_before_maturity', 'channel', 'is_active')
    list_filter = ('is_active', 'channel')
