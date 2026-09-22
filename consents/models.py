from django.conf import settings
from django.db import models


class Consent(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        REVOKED = "REVOKED", "Revoked"
        EXPIRED = "EXPIRED", "Expired"

    class ConsentType(models.TextChoices):
        MEDICAL_RECORD = "MEDICAL_RECORD", "Medical Record"
        CONSULTATION = "CONSULTATION", "Consultation"
        PRESCRIPTION = "PRESCRIPTION", "Prescription"
        FULL_ACCESS = "FULL_ACCESS", "Full Access"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="consents_given",
    )

    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="consents_received",
    )

    record = models.ForeignKey(
        "medical_records.MedicalRecord",
        on_delete=models.CASCADE,
        related_name="consents",
        null=True,
        blank=True,
    )

    consent_type = models.CharField(
        max_length=30,
        choices=ConsentType.choices,
        default=ConsentType.MEDICAL_RECORD,
    )

    purpose = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    granted_at = models.DateTimeField(
        auto_now_add=True,
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return (
            f"{self.patient.email} → "
            f"{self.doctor.email} "
            f"({self.consent_type} - {self.status})"
        )
