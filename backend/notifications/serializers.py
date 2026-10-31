from rest_framework import serializers
from .models import Notification, AlertRule

class NotificationSerializer(serializers.ModelSerializer):
    fdr_number = serializers.CharField(source='fdr.fdr_number', read_only=True)
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    institution_name = serializers.CharField(source='institution.name', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'institution', 'institution_name', 'fdr', 'fdr_number',
            'title', 'message', 'notification_type', 'notification_type_display',
            'channel', 'channel_display', 'scheduled_date', 'sent_status',
            'sent_at', 'is_read', 'created_at'
        ]
        read_only_fields = [
            'id', 'user', 'institution', 'fdr', 'notification_type_display',
            'channel_display', 'sent_status', 'sent_at', 'created_at'
        ]


class AlertRuleSerializer(serializers.ModelSerializer):
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)

    class Meta:
        model = AlertRule
        fields = [
            'id', 'name', 'days_before_maturity', 'alert_type',
            'channel', 'channel_display', 'is_active', 'email_template', 'created_at'
        ]
        read_only_fields = ['id', 'channel_display', 'created_at']
