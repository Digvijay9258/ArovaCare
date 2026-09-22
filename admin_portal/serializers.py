from rest_framework import serializers

from audit_logs.models import AuditLog
from security.models import SecurityAlert, SecuritySession
from users.models import User


class AdminSecuritySessionSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    user_role = serializers.CharField(
        source="user.role",
        read_only=True,
    )

    class Meta:
        model = SecuritySession
        fields = [
            "id",
            "user_email",
            "user_role",
            "device_name",
            "ip_address",
            "user_agent",
            "is_active",
            "last_activity",
            "created_at",
            "logged_out_at",
        ]
        read_only_fields = fields


class AdminSecurityAlertSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    user_role = serializers.CharField(
        source="user.role",
        read_only=True,
    )

    class Meta:
        model = SecurityAlert
        fields = [
            "id",
            "user_email",
            "user_role",
            "alert_type",
            "title",
            "message",
            "severity",
            "is_read",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields


class AdminAuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    user_role = serializers.CharField(
        source="user.role",
        read_only=True,
    )

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user_email",
            "user_role",
            "action",
            "resource_type",
            "resource_id",
            "ip_address",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields


class AdminUserSerializer(serializers.ModelSerializer):
    """
    Safe Admin representation of a user.

    Private medical-record data is intentionally not included.
    """

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "role",
            "is_verified",
            "is_active",
            "is_staff",
            "is_superuser",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "role",
            "is_verified",
            "is_staff",
            "is_superuser",
            "created_at",
            "updated_at",
        ]
