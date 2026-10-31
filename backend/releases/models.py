from django.db import models
from django.conf import settings

class ReleaseRequest(models.Model):
    class Status(models.TextChoices):
        REQUESTED = 'REQUESTED', 'Requested'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        MORE_INFO_NEEDED = 'MORE_INFO_NEEDED', 'More Info Needed'
        RELEASED = 'RELEASED', 'Released'

    fdr = models.ForeignKey(
        'fdrs.FDR',
        on_delete=models.CASCADE,
        related_name='release_requests',
        help_text="FDR for which lien release / refund is requested"
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='raised_release_requests',
        help_text="Institution user who submitted the request"
    )
    reason = models.TextField(help_text="Justification for release (e.g. completion of obligation, course closure, replacement)")
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.REQUESTED,
        db_index=True
    )
    official_remarks = models.TextField(blank=True, help_text="Remarks by AICTE official evaluating the release")
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='decided_releases'
    )
    decision_date = models.DateTimeField(null=True, blank=True)
    refund_order_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="AICTE release order dispatch / refund voucher number"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Release Request'
        verbose_name_plural = 'Release Requests'

    def __str__(self):
        return f"Release #{self.id} for FDR {self.fdr.fdr_number} [{self.get_status_display()}]"
