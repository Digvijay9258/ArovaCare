from django.contrib.auth import password_validation
from django.utils import timezone

from rest_framework import serializers

from audit_logs.models import AuditLog
from consents.models import Consent

from .models import (
    EmergencyAccess,
    SecurityAlert,
    SecuritySession,
    MFASetting,
)

# ============================================================
# SECURITY SESSION SERIALIZER
# ============================================================


class SecuritySessionSerializer(serializers.ModelSerializer):
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = SecuritySession

        fields = [
            "id",
            "device_name",
            "ip_address",
            "user_agent",
            "is_active",
            "is_current",
            "last_activity",
            "created_at",
            "logged_out_at",
        ]

        read_only_fields = fields

    def get_is_current(self, obj):
        request = self.context.get("request")

        if not request:
            return False

        current_session_id = request.headers.get("X-Session-ID")

        return bool(current_session_id and current_session_id == obj.session_token_id)


# ============================================================
# SECURITY ALERT SERIALIZER
# ============================================================


class SecurityAlertSerializer(serializers.ModelSerializer):

    class Meta:
        model = SecurityAlert

        fields = [
            "id",
            "alert_type",
            "title",
            "message",
            "severity",
            "is_read",
            "metadata",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "alert_type",
            "title",
            "message",
            "severity",
            "metadata",
            "created_at",
        ]


# ============================================================
# MFA SERIALIZER
# ============================================================


class MFASerializer(serializers.ModelSerializer):

    class Meta:
        model = MFASetting

        fields = [
            "id",
            "is_enabled",
            "method",
            "enabled_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "is_enabled",
            "method",
            "enabled_at",
            "updated_at",
        ]


# ============================================================
# MFA SETUP SERIALIZER
# ============================================================


class MFASetupSerializer(serializers.Serializer):
    method = serializers.ChoiceField(
        choices=[
            ("TOTP", "Authenticator App"),
        ],
        default="TOTP",
    )


# ============================================================
# MFA VERIFY SERIALIZER
# ============================================================


class MFAVerifySerializer(serializers.Serializer):
    otp = serializers.CharField(
        min_length=6,
        max_length=6,
        write_only=True,
    )

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")

        return value


# ============================================================
# MFA DISABLE SERIALIZER
# ============================================================


class MFADisableSerializer(serializers.Serializer):
    otp = serializers.CharField(
        min_length=6,
        max_length=6,
        write_only=True,
    )

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")

        return value


# ============================================================
# PASSWORD CHANGE SERIALIZER
# ============================================================


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True,
        required=True,
    )

    new_password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
    )

    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
    )

    def validate_old_password(self, value):
        user = self.context["request"].user

        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")

        return value

    def validate(self, attrs):
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        if new_password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": ("New passwords do not match.")}
            )

        user = self.context["request"].user

        password_validation.validate_password(
            new_password,
            user,
        )

        return attrs


# ============================================================
# CONSENT SECURITY SERIALIZER
# ============================================================


class ConsentSecuritySerializer(serializers.ModelSerializer):
    doctor_email = serializers.EmailField(
        source="doctor.email",
        read_only=True,
    )

    record_title = serializers.CharField(
        source="record.title",
        read_only=True,
    )

    class Meta:
        model = Consent

        fields = [
            "id",
            "doctor_email",
            "record_title",
            "consent_type",
            "purpose",
            "status",
            "granted_at",
            "expires_at",
            "revoked_at",
        ]

        read_only_fields = fields


# ============================================================
# AUDIT ACTIVITY SERIALIZER
# ============================================================


class AuditActivitySerializer(serializers.ModelSerializer):

    class Meta:
        model = AuditLog

        fields = [
            "id",
            "action",
            "resource_type",
            "resource_id",
            "ip_address",
            "metadata",
            "created_at",
        ]

        read_only_fields = fields


# ============================================================
# EMERGENCY ACCESS REQUEST SERIALIZER
# ============================================================


class EmergencyAccessRequestSerializer(serializers.ModelSerializer):
    patient_email = serializers.EmailField(
        source="patient.email",
        read_only=True,
    )

    doctor_email = serializers.EmailField(
        source="doctor.email",
        read_only=True,
    )

    class Meta:
        model = EmergencyAccess

        fields = [
            "id",
            "doctor",
            "doctor_email",
            "patient",
            "patient_email",
            "reason",
            "scope",
            "status",
            "requested_at",
            "expires_at",
            "revoked_at",
            "last_accessed_at",
            "access_count",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "doctor",
            "doctor_email",
            "patient_email",
            "status",
            "requested_at",
            "revoked_at",
            "last_accessed_at",
            "access_count",
            "created_at",
            "updated_at",
        ]

    def validate_patient(self, patient):
        if patient.role != "PATIENT":
            raise serializers.ValidationError(
                "Emergency access can only be requested for a patient."
            )

        if not patient.is_active:
            raise serializers.ValidationError(
                "The selected patient account is inactive."
            )

        return patient

    def validate_reason(self, value):
        value = value.strip()

        if len(value) < 10:
            raise serializers.ValidationError(
                "Emergency reason must contain at least 10 characters."
            )

        return value

    def validate_expires_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError(
                "Emergency access expiry must be in the future."
            )

        return value

    def validate(self, attrs):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")

        doctor = request.user

        if doctor.role != "DOCTOR":
            raise serializers.ValidationError(
                "Only doctors can request emergency access."
            )

        patient = attrs.get("patient")

        if patient and patient == doctor:
            raise serializers.ValidationError(
                "Doctor cannot request emergency access for their own account."
            )

        return attrs


# ============================================================
# EMERGENCY ACCESS SERIALIZER
# ============================================================


class EmergencyAccessSerializer(EmergencyAccessRequestSerializer):
    pass
