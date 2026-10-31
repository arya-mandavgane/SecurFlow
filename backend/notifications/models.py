from django.db import models
from django.conf import settings

class Notification(models.Model):
    class Type(models.TextChoices):
        MATURITY_REMINDER = 'MATURITY_REMINDER', 'Maturity Reminder'
        STATUS_CHANGE = 'STATUS_CHANGE', 'Status Change'
        CLARIFICATION = 'CLARIFICATION', 'Clarification Request'
        VERIFICATION_UPDATE = 'VERIFICATION_UPDATE', 'Verification Update'
        RELEASE_UPDATE = 'RELEASE_UPDATE', 'Release Update'
        SYSTEM = 'SYSTEM', 'System Notification'

    class Channel(models.TextChoices):
        IN_APP = 'IN_APP', 'In-App Notification'
        EMAIL = 'EMAIL', 'Email'
        SMS = 'SMS', 'SMS'
        WHATSAPP = 'WHATSAPP', 'WhatsApp'

    class SentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SENT = 'SENT', 'Sent'
        FAILED = 'FAILED', 'Failed'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="Target recipient user"
    )
    institution = models.ForeignKey(
        'institutions.Institution',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="Target institution"
    )
    fdr = models.ForeignKey(
        'fdrs.FDR',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='notifications',
        help_text="Associated FDR if notification relates to a specific deposit"
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=30,
        choices=Type.choices,
        default=Type.SYSTEM
    )
    channel = models.CharField(
        max_length=20,
        choices=Channel.choices,
        default=Channel.IN_APP
    )
    scheduled_date = models.DateTimeField(null=True, blank=True)
    sent_status = models.CharField(
        max_length=20,
        choices=SentStatus.choices,
        default=SentStatus.PENDING
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"[{self.get_channel_display()}] {self.title} - {self.get_sent_status_display()}"


class AlertRule(models.Model):
    name = models.CharField(max_length=150)
    days_before_maturity = models.IntegerField(
        help_text="Days prior to FDR maturity when notification is triggered (e.g. 90, 60, 30, 15, 7, 0)"
    )
    alert_type = models.CharField(
        max_length=50,
        default='MATURITY_ALERT'
    )
    channel = models.CharField(
        max_length=20,
        choices=Notification.Channel.choices,
        default=Notification.Channel.EMAIL
    )
    is_active = models.BooleanField(default=True)
    email_template = models.TextField(
        blank=True,
        help_text="Email body template supporting tags like {{institution}}, {{fdr_number}}, {{days_left}}, {{maturity_date}}"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-days_before_maturity']
        verbose_name = 'Alert Rule'
        verbose_name_plural = 'Alert Rules'

    def __str__(self):
        return f"{self.name} ({self.days_before_maturity} days before maturity)"
