from django.conf import settings
from django.db import models


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        APPOINTMENT = "APPOINTMENT", "Appointment"
        CONSULTATION = "CONSULTATION", "Consultation"
        PRESCRIPTION = "PRESCRIPTION", "Prescription"
        MESSAGE = "MESSAGE", "Message"
        ACCESS_REQUEST = "ACCESS_REQUEST", "Access Request"
        CONSENT = "CONSENT", "Consent"
        SYSTEM = "SYSTEM", "System"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
    )

    title = models.CharField(max_length=255)

    message = models.TextField()

    is_read = models.BooleanField(default=False)

    # Optional reference to an object related to the notification.
    # We keep this generic so notifications can point to appointments,
    # consultations, messages, etc. without creating hard dependencies.
    reference_id = models.PositiveBigIntegerField(
        null=True,
        blank=True,
    )

    reference_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    read_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["recipient", "is_read"],
                name="notif_recipient_read_idx",
            ),
            models.Index(
                fields=["recipient", "-created_at"],
                name="notif_recipient_date_idx",
            ),
            models.Index(
                fields=["notification_type"],
                name="notif_type_idx",
            ),
        ]

    def __str__(self):
        return f"{self.title} - {self.recipient}"
 