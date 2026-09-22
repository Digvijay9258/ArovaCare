from django.conf import settings
from django.db import models
import uuid


class SecuritySession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="security_sessions",
    )

    session_token_id = models.CharField(
        max_length=255,
        unique=True,
    )

    device_name = models.CharField(
        max_length=255,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    last_activity = models.DateTimeField(
        auto_now=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    logged_out_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    @staticmethod
    def generate_session_id():
        return str(uuid.uuid4())


class SecurityAlert(models.Model):

    class AlertType(models.TextChoices):
        NEW_LOGIN = "NEW_LOGIN", "New Login"
        FAILED_LOGIN = "FAILED_LOGIN", "Failed Login"
        ACCESS_REQUEST = "ACCESS_REQUEST", "Access Request"
        ACCESS_GRANTED = "ACCESS_GRANTED", "Access Granted"
        ACCESS_REVOKED = "ACCESS_REVOKED", "Access Revoked"
        EMERGENCY_ACCESS = "EMERGENCY_ACCESS", "Emergency Access"
        PASSWORD_CHANGED = "PASSWORD_CHANGED", "Password Changed"
        MFA_CHANGED = "MFA_CHANGED", "MFA Changed"
        SECURITY_EVENT = "SECURITY_EVENT", "Security Event"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="security_alerts",
    )

    alert_type = models.CharField(
        max_length=50,
        choices=AlertType.choices,
    )

    title = models.CharField(
        max_length=255,
    )

    message = models.TextField()

    severity = models.CharField(
        max_length=20,
        default="INFO",
    )

    is_read = models.BooleanField(
        default=False,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )


class MFASetting(models.Model):
    class Method(models.TextChoices):
        TOTP = "TOTP", "Authenticator App"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mfa_setting",
    )

    is_enabled = models.BooleanField(default=False)

    method = models.CharField(
        max_length=20,
        choices=Method.choices,
        default=Method.TOTP,
    )

    secret_key = models.CharField(
        max_length=64,
        blank=True,
        null=True,
    )

    enabled_at = models.DateTimeField(
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
        return f"MFA - {self.user.email}"


class EmergencyAccess(models.Model):

    class Scope(models.TextChoices):
        EMERGENCY_PROFILE = (
            "EMERGENCY_PROFILE",
            "Emergency Profile",
        )

        MEDICAL_RECORDS = (
            "MEDICAL_RECORDS",
            "Medical Records",
        )

        PRESCRIPTIONS = (
            "PRESCRIPTIONS",
            "Prescriptions",
        )

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        EXPIRED = "EXPIRED", "Expired"
        REVOKED = "REVOKED", "Revoked"

    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="emergency_access_requests",
    )

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="emergency_access_received",
    )

    reason = models.TextField()

    scope = models.CharField(
        max_length=40,
        choices=Scope.choices,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    requested_at = models.DateTimeField(
        auto_now_add=True,
    )

    expires_at = models.DateTimeField()

    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    last_accessed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    access_count = models.PositiveIntegerField(
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=[
                    "patient",
                    "status",
                ]
            ),
            models.Index(
                fields=[
                    "doctor",
                    "status",
                ]
            ),
            models.Index(
                fields=[
                    "expires_at",
                ]
            ),
        ]

    def __str__(self):
        return (
            f"Emergency Access #{self.id} - "
            f"{self.doctor.email} → {self.patient.email}"
        )

    def is_currently_active(self):
        from django.utils import timezone

        if self.status != self.Status.ACTIVE:
            return False

        if self.expires_at <= timezone.now():
            return False

        return True
