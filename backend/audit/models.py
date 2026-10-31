from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = 'CREATE', 'Create'
        UPDATE = 'UPDATE', 'Update'
        DELETE = 'DELETE', 'Delete'
        STATUS_CHANGE = 'STATUS_CHANGE', 'Status Change'
        VERIFY = 'VERIFY', 'Verification Action'
        LOGIN = 'LOGIN', 'User Login'
        LOGOUT = 'LOGOUT', 'User Logout'
        EXPORT = 'EXPORT', 'Data Export'

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_entries',
        help_text="User who initiated this action"
    )
    action = models.CharField(
        max_length=30,
        choices=Action.choices,
        db_index=True
    )
    entity_type = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Class / Resource name (e.g., FDR, Institution, ReleaseRequest)"
    )
    entity_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Primary key identifier of the modified record"
    )
    before_state = models.JSONField(
        default=dict,
        blank=True,
        help_text="Snapshot of record fields prior to modification"
    )
    after_state = models.JSONField(
        default=dict,
        blank=True,
        help_text="Snapshot of record fields following modification"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Client IP address"
    )
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        help_text="Client browser or agent string"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['action', 'timestamp']),
        ]

    def __str__(self):
        actor_name = self.actor.username if self.actor else 'SYSTEM'
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {actor_name} -> {self.action} on {self.entity_type} #{self.entity_id}"
