from django.contrib.auth import update_session_auth_hash
from django.db import transaction
from django.utils import timezone

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

import pyotp

from audit_logs.models import AuditLog
from consents.models import Consent
from notifications.models import Notification

from .models import (
    EmergencyAccess,
    MFASetting,
    SecurityAlert,
    SecuritySession,
)
from .serializers import (
    AuditActivitySerializer,
    ConsentSecuritySerializer,
    EmergencyAccessRequestSerializer,
    EmergencyAccessSerializer,
    MFADisableSerializer,
    MFASetupSerializer,
    MFASerializer,
    MFAVerifySerializer,
    PasswordChangeSerializer,
    SecurityAlertSerializer,
    SecuritySessionSerializer,
)

# ============================================================
# SECURITY SESSION LIST
# ============================================================


class SecuritySessionListView(generics.ListAPIView):
    serializer_class = SecuritySessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SecuritySession.objects.filter(user=self.request.user).order_by(
            "-last_activity"
        )


# ============================================================
# LOGOUT ALL SESSIONS
# ============================================================


class LogoutAllSessionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        now = timezone.now()

        sessions = SecuritySession.objects.filter(
            user=request.user,
            is_active=True,
        )

        sessions.update(
            is_active=False,
            logged_out_at=now,
        )

        AuditLog.objects.create(
            user=request.user,
            action="LOGOUT_ALL_SESSIONS",
            resource_type="SECURITY_SESSION",
            resource_id=str(request.user.id),
            ip_address=self._get_client_ip(request),
            metadata={"message": ("All active security sessions were logged out.")},
        )

        SecurityAlert.objects.create(
            user=request.user,
            alert_type=SecurityAlert.AlertType.SECURITY_EVENT,
            title="All sessions logged out",
            message=("All active sessions for your account were logged out."),
            severity="INFO",
            metadata={
                "action": "LOGOUT_ALL_SESSIONS",
            },
        )

        return Response(
            {"detail": ("All active sessions have been logged out.")},
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _get_client_ip(request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")


# ============================================================
# SECURITY ACTIVITY
# ============================================================


class SecurityActivityView(generics.ListAPIView):
    serializer_class = AuditActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AuditLog.objects.filter(user=self.request.user).order_by("-created_at")[
            :100
        ]


# ============================================================
# SECURITY ALERT LIST
# ============================================================


class SecurityAlertListView(generics.ListAPIView):
    serializer_class = SecurityAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SecurityAlert.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )


# ============================================================
# SECURITY ALERT READ
# ============================================================


class SecurityAlertReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        alert = SecurityAlert.objects.filter(
            id=pk,
            user=request.user,
        ).first()

        if not alert:
            return Response(
                {"detail": "Security alert not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        alert.is_read = True

        alert.save(update_fields=["is_read"])

        return Response(
            {"detail": "Security alert marked as read."},
            status=status.HTTP_200_OK,
        )


# ============================================================
# PASSWORD CHANGE
# ============================================================


class PasswordChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        user = request.user

        user.set_password(serializer.validated_data["new_password"])

        user.save(update_fields=["password"])

        update_session_auth_hash(
            request,
            user,
        )

        now = timezone.now()

        SecuritySession.objects.filter(
            user=user,
            is_active=True,
        ).update(
            is_active=False,
            logged_out_at=now,
        )

        AuditLog.objects.create(
            user=user,
            action="PASSWORD_CHANGED",
            resource_type="USER",
            resource_id=str(user.id),
            ip_address=self._get_client_ip(request),
            metadata={"message": "Account password was changed."},
        )

        SecurityAlert.objects.create(
            user=user,
            alert_type=SecurityAlert.AlertType.PASSWORD_CHANGED,
            title="Password changed",
            message=(
                "Your Arova account password was changed. "
                "For security, all active sessions have been logged out."
            ),
            severity="INFO",
            metadata={
                "action": "PASSWORD_CHANGED",
            },
        )

        return Response(
            {
                "detail": (
                    "Password changed successfully. "
                    "All active sessions have been logged out."
                )
            },
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _get_client_ip(request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")


# ============================================================
# MFA
# ============================================================


class MFAView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        mfa_setting, _ = MFASetting.objects.get_or_create(user=request.user)

        serializer = MFASerializer(mfa_setting)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = MFASetupSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        method = serializer.validated_data["method"]

        if method != "TOTP":
            return Response(
                {"detail": ("Only TOTP MFA is currently supported.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        mfa_setting, _ = MFASetting.objects.get_or_create(user=request.user)

        if mfa_setting.is_enabled:
            return Response(
                {"detail": "MFA is already enabled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not mfa_setting.secret_key:
            mfa_setting.secret_key = pyotp.random_base32()
            mfa_setting.method = MFASetting.Method.TOTP

            mfa_setting.save(
                update_fields=[
                    "secret_key",
                    "method",
                    "updated_at",
                ]
            )

        totp = pyotp.TOTP(mfa_setting.secret_key)

        provisioning_uri = totp.provisioning_uri(
            name=request.user.email,
            issuer_name="Arova",
        )

        return Response(
            {
                "detail": (
                    "MFA setup initialized. "
                    "Use the provisioning URI with your "
                    "authenticator application."
                ),
                "method": mfa_setting.method,
                "provisioning_uri": provisioning_uri,
                "secret_key": mfa_setting.secret_key,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# MFA VERIFY / ENABLE
# ============================================================


class MFAVerifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MFAVerifySerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        otp = serializer.validated_data["otp"]

        mfa_setting = MFASetting.objects.filter(user=request.user).first()

        if not mfa_setting or not mfa_setting.secret_key:
            return Response(
                {"detail": ("MFA setup has not been initialized.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if mfa_setting.is_enabled:
            return Response(
                {"detail": "MFA is already enabled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        totp = pyotp.TOTP(mfa_setting.secret_key)

        if not totp.verify(
            otp,
            valid_window=1,
        ):
            return Response(
                {"detail": "Invalid MFA code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()

        mfa_setting.is_enabled = True
        mfa_setting.enabled_at = now

        mfa_setting.save(
            update_fields=[
                "is_enabled",
                "enabled_at",
                "updated_at",
            ]
        )

        AuditLog.objects.create(
            user=request.user,
            action="MFA_ENABLED",
            resource_type="MFA_SETTING",
            resource_id=str(mfa_setting.id),
            ip_address=self._get_client_ip(request),
            metadata={
                "method": mfa_setting.method,
            },
        )

        SecurityAlert.objects.create(
            user=request.user,
            alert_type=SecurityAlert.AlertType.MFA_CHANGED,
            title="MFA enabled",
            message=(
                "Multi-factor authentication has been enabled "
                "for your Arova account."
            ),
            severity="INFO",
            metadata={
                "action": "MFA_ENABLED",
                "method": mfa_setting.method,
            },
        )

        return Response(
            {"detail": "MFA enabled successfully."},
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _get_client_ip(request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")


# ============================================================
# MFA DISABLE
# ============================================================


class MFADisableView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MFADisableSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        otp = serializer.validated_data["otp"]

        mfa_setting = MFASetting.objects.filter(user=request.user).first()

        if not mfa_setting or not mfa_setting.is_enabled:
            return Response(
                {"detail": "MFA is not enabled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not mfa_setting.secret_key:
            return Response(
                {"detail": "MFA configuration is invalid."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        totp = pyotp.TOTP(mfa_setting.secret_key)

        if not totp.verify(
            otp,
            valid_window=1,
        ):
            return Response(
                {"detail": "Invalid MFA code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        mfa_setting.is_enabled = False
        mfa_setting.enabled_at = None

        mfa_setting.save(
            update_fields=[
                "is_enabled",
                "enabled_at",
                "updated_at",
            ]
        )

        AuditLog.objects.create(
            user=request.user,
            action="MFA_DISABLED",
            resource_type="MFA_SETTING",
            resource_id=str(mfa_setting.id),
            ip_address=self._get_client_ip(request),
            metadata={
                "method": mfa_setting.method,
            },
        )

        SecurityAlert.objects.create(
            user=request.user,
            alert_type=SecurityAlert.AlertType.MFA_CHANGED,
            title="MFA disabled",
            message=(
                "Multi-factor authentication has been disabled "
                "for your Arova account."
            ),
            severity="WARNING",
            metadata={
                "action": "MFA_DISABLED",
                "method": mfa_setting.method,
            },
        )

        return Response(
            {"detail": "MFA disabled successfully."},
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _get_client_ip(request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")


# ============================================================
# ACTIVE CONSENTS
# ============================================================


class ActiveConsentSecurityView(generics.ListAPIView):
    serializer_class = ConsentSecuritySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role != "PATIENT":
            return Consent.objects.none()

        now = timezone.now()

        return Consent.objects.filter(
            patient=user,
            status="ACTIVE",
        ).filter(expires_at__isnull=True) | Consent.objects.filter(
            patient=user,
            status="ACTIVE",
            expires_at__gt=now,
        )


# ============================================================
# PATIENT EMERGENCY ACCESS
# ============================================================


class EmergencyAccessSecurityView(generics.ListAPIView):
    serializer_class = EmergencyAccessSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role != "PATIENT":
            return EmergencyAccess.objects.none()

        return EmergencyAccess.objects.filter(patient=user).order_by("-created_at")


# ============================================================
# CREATE EMERGENCY ACCESS REQUEST
# ============================================================


class EmergencyAccessRequestCreateView(generics.CreateAPIView):
    serializer_class = EmergencyAccessRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if request.user.role != "DOCTOR":
            return Response(
                {"detail": ("Only doctors can request emergency access.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        emergency_access = serializer.save(
            doctor=request.user,
            status=EmergencyAccess.Status.ACTIVE,
        )

        patient = emergency_access.patient

        SecurityAlert.objects.create(
            user=patient,
            alert_type=SecurityAlert.AlertType.EMERGENCY_ACCESS,
            title="Emergency access requested",
            message=(
                f"Doctor {request.user.email} requested "
                "emergency access to your health information."
            ),
            severity="WARNING",
            metadata={
                "emergency_access_id": emergency_access.id,
                "doctor_id": request.user.id,
                "scope": emergency_access.scope,
                "reason": emergency_access.reason,
                "expires_at": (emergency_access.expires_at.isoformat()),
            },
        )

        Notification.objects.create(
            recipient=patient,
            notification_type="ACCESS_REQUEST",
            title="Emergency access requested",
            message=(
                f"Doctor {request.user.email} requested "
                "emergency access to your health information."
            ),
            reference_id=emergency_access.id,
        )

        AuditLog.objects.create(
            user=request.user,
            action="EMERGENCY_ACCESS_REQUESTED",
            resource_type="EMERGENCY_ACCESS",
            resource_id=str(emergency_access.id),
            ip_address=self._get_client_ip(request),
            metadata={
                "patient_id": patient.id,
                "scope": emergency_access.scope,
                "reason": emergency_access.reason,
                "expires_at": (emergency_access.expires_at.isoformat()),
            },
        )

        response_serializer = EmergencyAccessSerializer(
            emergency_access,
            context={"request": request},
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def _get_client_ip(request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")


# ============================================================
# EMERGENCY ACCESS LIST
# ============================================================


class EmergencyAccessListView(generics.ListAPIView):
    serializer_class = EmergencyAccessSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == "DOCTOR":
            return EmergencyAccess.objects.filter(doctor=user).order_by("-created_at")

        if user.role == "PATIENT":
            return EmergencyAccess.objects.filter(patient=user).order_by("-created_at")

        return EmergencyAccess.objects.none()


# ============================================================
# EMERGENCY ACCESS DETAIL
# ============================================================


class EmergencyAccessDetailView(generics.RetrieveAPIView):
    serializer_class = EmergencyAccessSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == "DOCTOR":
            return EmergencyAccess.objects.filter(doctor=user)

        if user.role == "PATIENT":
            return EmergencyAccess.objects.filter(patient=user)

        return EmergencyAccess.objects.none()


# ============================================================
# USE EMERGENCY ACCESS
# ============================================================


class EmergencyAccessUseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        if request.user.role != "DOCTOR":
            return Response(
                {"detail": ("Only doctors can use emergency access.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        emergency_access = (
            EmergencyAccess.objects.select_for_update()
            .filter(
                id=pk,
                doctor=request.user,
            )
            .select_related(
                "patient",
                "doctor",
            )
            .first()
        )

        if not emergency_access:
            return Response(
                {"detail": "Emergency access not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        now = timezone.now()

        if emergency_access.status != EmergencyAccess.Status.ACTIVE:
            return Response(
                {"detail": ("This emergency access is no longer active.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        if emergency_access.expires_at <= now:
            emergency_access.status = EmergencyAccess.Status.EXPIRED

            emergency_access.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            return Response(
                {"detail": ("This emergency access has expired.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        emergency_access.access_count += 1
        emergency_access.last_accessed_at = now

        emergency_access.save(
            update_fields=[
                "access_count",
                "last_accessed_at",
                "updated_at",
            ]
        )

        AuditLog.objects.create(
            user=request.user,
            action="EMERGENCY_ACCESS_USED",
            resource_type="EMERGENCY_ACCESS",
            resource_id=str(emergency_access.id),
            ip_address=self._get_client_ip(request),
            metadata={
                "patient_id": emergency_access.patient_id,
                "scope": emergency_access.scope,
                "reason": emergency_access.reason,
                "access_count": emergency_access.access_count,
            },
        )

        SecurityAlert.objects.create(
            user=emergency_access.patient,
            alert_type=SecurityAlert.AlertType.EMERGENCY_ACCESS,
            title="Emergency access used",
            message=(
                f"Doctor {request.user.email} used your "
                "emergency access authorization."
            ),
            severity="WARNING",
            metadata={
                "emergency_access_id": emergency_access.id,
                "doctor_id": request.user.id,
                "scope": emergency_access.scope,
                "access_count": emergency_access.access_count,
            },
        )

        response_data = {
            "detail": ("Emergency access used successfully."),
            "emergency_access_id": emergency_access.id,
            "scope": emergency_access.scope,
            "access_count": emergency_access.access_count,
            "last_accessed_at": (emergency_access.last_accessed_at),
        }

        if emergency_access.scope == EmergencyAccess.Scope.EMERGENCY_PROFILE:
            response_data["access"] = "Emergency profile access authorized."

        elif emergency_access.scope == EmergencyAccess.Scope.MEDICAL_RECORDS:
            response_data["access"] = "Medical record access authorized."

        elif emergency_access.scope == EmergencyAccess.Scope.PRESCRIPTIONS:
            response_data["access"] = "Prescription access authorized."

        return Response(
            response_data,
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _get_client_ip(request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")


# ============================================================
# REVOKE EMERGENCY ACCESS
# ============================================================


class EmergencyAccessRevokeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        if request.user.role != "PATIENT":
            return Response(
                {"detail": ("Only patients can revoke emergency access.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        emergency_access = (
            EmergencyAccess.objects.select_for_update()
            .filter(
                id=pk,
                patient=request.user,
            )
            .select_related("doctor")
            .first()
        )

        if not emergency_access:
            return Response(
                {"detail": "Emergency access not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if emergency_access.status != EmergencyAccess.Status.ACTIVE:
            return Response(
                {"detail": ("This emergency access is not active.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()

        emergency_access.status = EmergencyAccess.Status.REVOKED

        emergency_access.revoked_at = now

        emergency_access.save(
            update_fields=[
                "status",
                "revoked_at",
                "updated_at",
            ]
        )

        AuditLog.objects.create(
            user=request.user,
            action="EMERGENCY_ACCESS_REVOKED",
            resource_type="EMERGENCY_ACCESS",
            resource_id=str(emergency_access.id),
            ip_address=self._get_client_ip(request),
            metadata={
                "doctor_id": emergency_access.doctor_id,
                "scope": emergency_access.scope,
            },
        )

        SecurityAlert.objects.create(
            user=emergency_access.doctor,
            alert_type=SecurityAlert.AlertType.ACCESS_REVOKED,
            title="Emergency access revoked",
            message=(
                f"Emergency access granted by "
                f"{request.user.email} has been revoked."
            ),
            severity="WARNING",
            metadata={
                "emergency_access_id": emergency_access.id,
                "patient_id": request.user.id,
                "scope": emergency_access.scope,
            },
        )

        return Response(
            {"detail": ("Emergency access has been revoked.")},
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _get_client_ip(request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")
