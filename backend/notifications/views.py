from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from .models import Notification, AlertRule
from .serializers import NotificationSerializer, AlertRuleSerializer
from .scanner import run_maturity_scan
from accounts.models import User
from accounts.permissions import CanVerifyFDR, IsAdminUserRole

@extend_schema_view(
    list=extend_schema(
        tags=['Notifications'],
        summary='List In-App Notifications',
        description='Lists notifications for the authenticated user or institution, with unread badge support.',
    )
)
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'is_read']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        queryset = Notification.objects.filter(channel=Notification.Channel.IN_APP)

        if user.role == User.Role.INSTITUTION:
            if user.institution_id:
                queryset = queryset.filter(institution_id=user.institution_id)
            else:
                return queryset.none()
        else:
            # Officials and Admins can see all or filter by institution
            inst_id = self.request.query_params.get('institution')
            if inst_id:
                queryset = queryset.filter(institution_id=inst_id)

        unread_only = self.request.query_params.get('unread')
        if unread_only and unread_only.lower() in ('true', '1'):
            queryset = queryset.filter(is_read=False)

        return queryset

    @extend_schema(
        tags=['Notifications'],
        summary='Mark Notification as Read',
        description='Marks an individual notification as read.'
    )
    @action(detail=True, methods=['post'], url_path='read')
    def mark_as_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save(update_fields=['is_read'])
        return Response({
            "success": True,
            "message": "Notification marked as read.",
            "data": self.get_serializer(notif).data
        })

    @extend_schema(
        tags=['Notifications'],
        summary='Mark All Notifications as Read',
        description='Marks all in-app notifications for the current institution/user as read.'
    )
    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_as_read(self, request):
        queryset = self.get_queryset().filter(is_read=False)
        updated_count = queryset.update(is_read=True)
        return Response({
            "success": True,
            "message": f"{updated_count} notifications marked as read.",
            "data": {"updated_count": updated_count}
        })

    @extend_schema(
        tags=['Notifications'],
        summary='Get Unread Notification Count',
        description='Lightweight endpoint for polling notification badge count.'
    )
    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({
            "success": True,
            "data": {"unread_count": count}
        })

    @extend_schema(
        tags=['Notifications'],
        summary='Trigger Maturity & Compliance Scan',
        description='Runs idempotent scan of all FDR maturities, updates EXPIRING_SOON/EXPIRED statuses, and dispatches reminders.'
    )
    @action(detail=False, methods=['post'], url_path='run-scan', permission_classes=[permissions.IsAuthenticated, CanVerifyFDR])
    def trigger_scan(self, request):
        results = run_maturity_scan(request=request)
        return Response({
            "success": True,
            "message": "Maturity scan completed successfully.",
            "data": results
        })


@extend_schema_view(
    list=extend_schema(tags=['Alert Rules'], summary='List Alert Rules'),
    create=extend_schema(tags=['Alert Rules'], summary='Create Alert Rule'),
    update=extend_schema(tags=['Alert Rules'], summary='Update Alert Rule'),
    destroy=extend_schema(tags=['Alert Rules'], summary='Delete Alert Rule')
)
class AlertRuleViewSet(viewsets.ModelViewSet):
    queryset = AlertRule.objects.all()
    serializer_class = AlertRuleSerializer
    permission_classes = [permissions.IsAuthenticated, CanVerifyFDR]
    ordering = ['-days_before_maturity']
