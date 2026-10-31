from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        INSTITUTION = 'INSTITUTION', 'Institution User'
        OFFICIAL = 'OFFICIAL', 'AICTE Official'
        ADMIN = 'ADMIN', 'System Administrator'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.INSTITUTION,
        help_text="Role determining permissions and access tier across the portal."
    )
    institution = models.ForeignKey(
        'institutions.Institution',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='users',
        help_text="Associated technical institution (for INSTITUTION role users)."
    )
    phone_number = models.CharField(max_length=20, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_institution(self) -> bool:
        return self.role == self.Role.INSTITUTION

    @property
    def is_official(self) -> bool:
        return self.role == self.Role.OFFICIAL

    @property
    def is_admin_user(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
