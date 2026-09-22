from django.conf import settings
from django.db import models

from appointments.models import Appointment


class Prescription(models.Model):

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="prescriptions_received",
    )

    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="prescriptions_created",
    )

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name="prescription",
    )

    diagnosis = models.TextField()

    medicines = models.JSONField(
        default=list,
        help_text="List of prescribed medicines with dosage and duration.",
    )

    instructions = models.TextField(
        blank=True,
    )

    follow_up_date = models.DateField(
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
        return f"Prescription - " f"{self.patient.email} - " f"{self.doctor.email}"
