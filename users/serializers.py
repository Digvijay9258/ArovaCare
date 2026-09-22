from django.conf import settings
from django.utils import timezone

from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.exceptions import (
    AuthenticationFailed,
    InvalidToken,
)

import pyotp

from audit_logs.models import AuditLog
from audit_logs.services import create_audit_log

from security.models import (
    MFASetting,
    SecurityAlert,
    SecuritySession,
)

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "role",
        ]

    def validate_role(self, value):
        if value == "ADMIN":
            raise serializers.ValidationError(
                "Admin accounts cannot be created through public registration."
            )

        if value not in [
            "PATIENT",
            "DOCTOR",
        ]:
            raise serializers.ValidationError("Invalid registration role.")

        return value

    def create(self, validated_data):
        password = validated_data.pop("password")

        return User.objects.create_user(
            password=password,
            **validated_data,
        )


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "role",
            "is_verified",
            "is_active",
            "created_at",
        ]


class ArovaTokenObtainPairSerializer(TokenObtainPairSerializer):
    otp = serializers.CharField(
        required=False,
        write_only=True,
        allow_blank=True,
    )

    @classmethod
    def get_token(cls, user):
        return super().get_token(user)

    def _get_request_details(self):
        request = self.context.get("request")

        ip_address = None
        user_agent = ""

        if request:
            forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

            if forwarded_for:
                ip_address = forwarded_for.split(",")[0].strip()
            else:
                ip_address = request.META.get("REMOTE_ADDR")

            user_agent = request.META.get(
                "HTTP_USER_AGENT",
                "",
            )

        return ip_address, user_agent

    def _create_failed_login_alert(
        self,
        user=None,
        reason="Invalid authentication attempt.",
    ):
        if not user:
            return

        request = self.context.get("request")

        ip_address, user_agent = self._get_request_details()

        metadata = {
            "login_method": "JWT",
            "reason": reason,
            "ip_address": ip_address,
            "user_agent": user_agent[:500],
        }

        SecurityAlert.objects.create(
            user=user,
            alert_type=(SecurityAlert.AlertType.FAILED_LOGIN),
            title="Failed login attempt",
            message=("A failed login attempt was detected " "for your Arova account."),
            severity="WARNING",
            metadata=metadata,
        )

        create_audit_log(
            user=user,
            action=AuditLog.Action.LOGIN,
            resource_type="Authentication",
            resource_id=user.id,
            request=request,
            metadata={
                "login_method": "JWT",
                "authentication_status": "FAILED",
                "reason": reason,
                "ip_address": ip_address,
            },
        )

    def validate(self, attrs):
        email = attrs.get("email")

        user_by_email = (
            User.objects.filter(email__iexact=email).first() if email else None
        )

        try:
            data = super().validate(attrs)

        except AuthenticationFailed:
            self._create_failed_login_alert(
                user=user_by_email,
                reason="Invalid email or password.",
            )
            raise

        user = self.user

        if not user.is_active:
            self._create_failed_login_alert(
                user=user,
                reason="Inactive user account.",
            )

            raise AuthenticationFailed("This user account has been deactivated.")

        mfa = MFASetting.objects.filter(user=user).first()

        if mfa and mfa.is_enabled:
            otp = attrs.get("otp")

            if not otp:
                self._create_failed_login_alert(
                    user=user,
                    reason="MFA OTP was not provided.",
                )

                raise serializers.ValidationError(
                    {"otp": ("MFA is enabled for this " "account. OTP is required.")}
                )

            if not mfa.secret_key:
                self._create_failed_login_alert(
                    user=user,
                    reason="MFA secret is missing.",
                )

                raise serializers.ValidationError(
                    {
                        "otp": (
                            "MFA is enabled but no valid "
                            "authentication secret is configured."
                        )
                    }
                )

            totp = pyotp.TOTP(mfa.secret_key)

            if not totp.verify(
                otp,
                valid_window=1,
            ):
                self._create_failed_login_alert(
                    user=user,
                    reason="Invalid or expired MFA code.",
                )

                raise serializers.ValidationError(
                    {"otp": ("Invalid or expired MFA code.")}
                )

        request = self.context.get("request")

        ip_address, user_agent = self._get_request_details()

        device_name = user_agent[:255] if user_agent else "Unknown Device"

        session_id = SecuritySession.generate_session_id()

        SecuritySession.objects.create(
            user=user,
            session_token_id=session_id,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
        )

        refresh = self.get_token(user)

        refresh["session_id"] = session_id

        access = refresh.access_token

        data["refresh"] = str(refresh)
        data["access"] = str(access)
        data["session_id"] = session_id

        return data


class ArovaTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Secure refresh-token handling.

    A refresh request is accepted only when:

    - user exists
    - user is active
    - refresh token contains session_id
    - SecuritySession exists
    - SecuritySession is active
    - session has not exceeded the inactivity timeout
    """

    def validate(self, attrs):
        data = super().validate(attrs)

        refresh = self.token_class(attrs["refresh"])

        user_id = refresh.get("user_id")

        if not user_id:
            raise InvalidToken("User information is missing from refresh token.")

        user = User.objects.filter(id=user_id).first()

        if not user:
            raise InvalidToken("User account not found.")

        if not user.is_active:
            raise InvalidToken("This user account has been deactivated.")

        session_id = refresh.get("session_id")

        if not session_id:
            raise InvalidToken("Security session information is missing.")

        security_session = SecuritySession.objects.filter(
            user=user,
            session_token_id=session_id,
        ).first()

        if not security_session:
            raise InvalidToken("Security session not found.")

        if not security_session.is_active:
            raise InvalidToken("This security session has been logged out.")

        # -------------------------------------------------
        # Inactivity timeout
        # -------------------------------------------------

        timeout_seconds = getattr(
            settings,
            "SECURITY_SESSION_TIMEOUT_SECONDS",
            1800,
        )

        now = timezone.now()

        last_activity = security_session.last_activity

        if last_activity:
            inactive_seconds = (now - last_activity).total_seconds()

            if inactive_seconds > timeout_seconds:
                security_session.is_active = False
                security_session.logged_out_at = now

                security_session.save(
                    update_fields=[
                        "is_active",
                        "logged_out_at",
                    ]
                )

                raise InvalidToken(
                    "This security session has expired " "due to inactivity."
                )

        # -------------------------------------------------
        # Refresh session activity
        # -------------------------------------------------

        security_session.last_activity = now

        security_session.save(
            update_fields=[
                "last_activity",
            ]
        )

        # -------------------------------------------------
        # Add session_id to newly generated access token
        # -------------------------------------------------

        access_token = data.get("access")

        if access_token:
            from rest_framework_simplejwt.tokens import (
                AccessToken,
            )

            access = AccessToken(access_token)

            access["session_id"] = session_id

            data["access"] = str(access)

        data["session_id"] = session_id

        return data
