from django.conf import settings
from django.db import models


class AuditLog(models.Model):

    class Action(models.TextChoices):
        CREATE = "CREATE", "Create"
        READ = "READ", "Read"
        UPDATE = "UPDATE", "Update"
        DELETE = "DELETE", "Delete"
        GRANT_ACCESS = "GRANT_ACCESS", "Grant Access"
        REVOKE_ACCESS = "REVOKE_ACCESS", "Revoke Access"
        GRANT_CONSENT = "GRANT_CONSENT", "Grant Consent"
        REVOKE_CONSENT = "REVOKE_CONSENT", "Revoke Consent"
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    action = models.CharField(
        max_length=30,
        choices=Action.choices,
    )

    resource_type = models.CharField(
        max_length=100,
    )

    resource_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["action", "-created_at"]),
        ]

    def __str__(self):
        username = self.user.email if self.user else "System"

        return (
            f"{username} - "
            f"{self.action} - "
            f"{self.resource_type} "
            f"#{self.resource_id or '-'}"
        )
