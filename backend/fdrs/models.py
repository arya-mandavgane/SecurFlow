from django.db import models
from django.conf import settings

class FDR(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        VERIFIED = 'VERIFIED', 'Verified'
        REJECTED = 'REJECTED', 'Rejected'
        NEEDS_CLARIFICATION = 'NEEDS_CLARIFICATION', 'Needs Clarification'
        ACTIVE = 'ACTIVE', 'Active'
        EXPIRING_SOON = 'EXPIRING_SOON', 'Expiring Soon'
        EXPIRED = 'EXPIRED', 'Expired'
        RENEWED = 'RENEWED', 'Renewed'
        RELEASE_REQUESTED = 'RELEASE_REQUESTED', 'Release Requested'
        RELEASED = 'RELEASED', 'Released'

    institution = models.ForeignKey(
        'institutions.Institution',
        on_delete=models.CASCADE,
        related_name='fdrs',
        help_text="Institution submitting the FDR"
    )
    fdr_number = models.CharField(max_length=100, db_index=True, help_text="Unique FDR identifier printed on document")
    bank_name = models.CharField(max_length=150, db_index=True, help_text="Issuing commercial or nationalized bank")
    branch = models.CharField(max_length=150, help_text="Bank branch issuing the FDR")
    amount = models.DecimalField(max_digits=14, decimal_places=2, help_text="Fixed deposit amount in INR")
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Annual interest rate percentage")
    issue_date = models.DateField(help_text="FDR issuance date")
    maturity_date = models.DateField(db_index=True, help_text="FDR maturity date")
    lien_marked_aicte = models.BooleanField(
        default=False,
        help_text="Whether lien/pledge in favour of AICTE is officially noted"
    )
    purpose_approval_cycle = models.CharField(
        max_length=150,
        help_text="AICTE Approval Cycle or Purpose (e.g., Approval 2024-25, New Institution, Course Extension)"
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.SUBMITTED,
        db_index=True,
        help_text="Current state in the FDR lifecycle"
    )
    extracted_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured JSON extracted by OCR service including confidence scores"
    )
    parent_fdr = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='renewals',
        help_text="Parent FDR if this entry is a renewed or replacement deposit"
    )
    remarks = models.TextField(blank=True, help_text="General notes or clarifications")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Fixed Deposit Receipt'
        verbose_name_plural = 'Fixed Deposit Receipts'
        indexes = [
            models.Index(fields=['fdr_number', 'bank_name']),
            models.Index(fields=['status', 'maturity_date']),
        ]

    def __str__(self):
        return f"{self.fdr_number} - {self.bank_name} (₹{self.amount:,}) [{self.get_status_display()}]"


class FDRDocument(models.Model):
    class DocType(models.TextChoices):
        FDR_COPY = 'FDR_COPY', 'FDR Original / Copy'
        BANK_LETTER = 'BANK_LETTER', 'Bank Lien / Pledge Letter'
        RENEWAL_ADVICE = 'RENEWAL_ADVICE', 'Bank Renewal Advice'
        RELEASE_NOC = 'RELEASE_NOC', 'Release NOC / Confirmation'
        OTHER = 'OTHER', 'Other Supporting Document'

    fdr = models.ForeignKey(
        FDR,
        on_delete=models.CASCADE,
        related_name='documents',
        help_text="Linked FDR record"
    )
    file = models.FileField(upload_to='fdr_documents/%Y/%m/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(
        max_length=30,
        choices=DocType.choices,
        default=DocType.FDR_COPY
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='uploaded_documents'
    )
    checksum = models.CharField(max_length=64, blank=True, help_text="SHA-256 integrity checksum")
    file_size = models.BigIntegerField(default=0, help_text="File size in bytes")
    mime_type = models.CharField(max_length=100, blank=True)
    upload_timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-upload_timestamp']
        verbose_name = 'FDR Document'
        verbose_name_plural = 'FDR Documents'

    def __str__(self):
        return f"{self.file_name} ({self.get_file_type_display()})"
