from django.db import models

class Institution(models.Model):
    name = models.CharField(max_length=255, help_text="Official name of the technical institution")
    aicte_id = models.CharField(max_length=50, unique=True, db_index=True, help_text="Unique AICTE Permanent Institute ID")
    state = models.CharField(max_length=100, db_index=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.TextField()
    contact_person = models.CharField(max_length=150, help_text="Principal / Director / Authorized Signatory")
    email = models.EmailField(help_text="Official institutional email address")
    phone = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Institution'
        verbose_name_plural = 'Institutions'

    def __str__(self):
        return f"{self.name} ({self.aicte_id})"
