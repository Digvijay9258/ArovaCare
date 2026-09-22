import secrets

from django.conf import settings
from django.db import models


class EmergencyCard(models.Model):

    patient = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="emergency_card",
    )

    # Secure random token used by the emergency QR
    emergency_token = models.CharField(
        max_length=128,
        unique=True,
        editable=False,
    )

    is_active = models.BooleanField(default=True)

    allergies = models.TextField(blank=True)

    current_medications = models.TextField(blank=True)

    emergency_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):

        if not self.emergency_token:
            self.emergency_token = secrets.token_urlsafe(48)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Emergency Card - {self.patient.email}"
