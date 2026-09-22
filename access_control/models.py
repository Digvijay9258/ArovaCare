from django.conf import settings
from django.db import models

from users.models import User
from medical_records.models import MedicalRecord


class MedicalRecordAccess(models.Model):

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("REVOKED", "Revoked"),
        ("EXPIRED", "Expired"),
    ]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="access_grants_given",
    )

    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="access_grants_received",
    )
    record = models.ForeignKey(
        "medical_records.MedicalRecord",
        on_delete=models.CASCADE,
        related_name="access_permissions",
        null=True,
        blank=True,
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    expires_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ACTIVE")

    def __str__(self):
        return f"{self.patient.email} → " f"{self.doctor.email} ({self.status})"
