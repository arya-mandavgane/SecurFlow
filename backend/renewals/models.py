from django.db import models

class RenewalRecord(models.Model):
    class RenewalType(models.TextChoices):
        RENEWAL = 'RENEWAL', 'Direct Renewal (Same Bank/Deposit)'
        REPLACEMENT = 'REPLACEMENT', 'Replacement FDR (New Deposit/Bank)'

    original_fdr = models.ForeignKey(
        'fdrs.FDR',
        on_delete=models.CASCADE,
        related_name='renewal_as_original',
        help_text="The prior FDR that expired or is nearing maturity"
    )
    new_fdr = models.ForeignKey(
        'fdrs.FDR',
        on_delete=models.CASCADE,
        related_name='renewal_as_new',
        help_text="The newly submitted replacement or renewed FDR"
    )
    renewal_type = models.CharField(
        max_length=20,
        choices=RenewalType.choices,
        default=RenewalType.RENEWAL
    )
    reason = models.TextField(blank=True, help_text="Reason for renewal or replacement")
    renewal_date = models.DateField(help_text="Effective date of renewal")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Renewal Record'
        verbose_name_plural = 'Renewal Records'

    def __str__(self):
        return f"{self.get_renewal_type_display()}: #{self.original_fdr.fdr_number} -> #{self.new_fdr.fdr_number}"
