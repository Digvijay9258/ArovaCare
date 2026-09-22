from django.utils import timezone

from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from audit_logs.models import AuditLog
from audit_logs.services import create_audit_log

from security.models import SecurityAlert, SecuritySession

from .models import User
from .serializers import (
    ArovaTokenObtainPairSerializer,
    ArovaTokenRefreshSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .throttles import LoginRateThrottle


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class LoginView(TokenObtainPairView):
    """
    JWT login endpoint with:

    - SecuritySession creation
    - session_id inside JWT
    - MFA verification when enabled
    - failed-login security alerts
    - login rate limiting
    - successful-login audit logging
    - new-login security alert
    """

    serializer_class = ArovaTokenObtainPairSerializer

    throttle_classes = [
        LoginRateThrottle,
    ]

    def post(self, request, *args, **kwargs):

        response = super().post(
            request,
            *args,
            **kwargs,
        )

        if response.status_code == 200:

            email = request.data.get("email")

            user = User.objects.filter(
                email=email,
            ).first()

            if user:

                session_id = response.data.get("session_id")

                create_audit_log(
                    user=user,
                    action=AuditLog.Action.LOGIN,
                    resource_type="Authentication",
                    resource_id=user.id,
                    request=request,
                    metadata={
                        "login_method": "JWT",
                        "authentication_status": "SUCCESS",
                        "session_id": session_id,
                    },
                )

                SecurityAlert.objects.create(
                    user=user,
                    alert_type=(SecurityAlert.AlertType.NEW_LOGIN),
                    title="New login detected",
                    message=("A new login to your Arova account " "was detected."),
                    severity="INFO",
                    metadata={
                        "session_id": session_id,
                        "ip_address": request.META.get("REMOTE_ADDR"),
                    },
                )

        return response


class RefreshTokenView(TokenRefreshView):
    """
    Secure JWT refresh endpoint.

    Refresh is allowed only when:

    - the user still exists
    - the user account is active
    - refresh token contains session_id
    - SecuritySession exists
    - SecuritySession is active
    """

    serializer_class = ArovaTokenRefreshSerializer


class LogoutView(APIView):
    """
    Logout current JWT session.

    The refresh token is blacklisted and the corresponding
    Arova SecuritySession is marked inactive.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):

        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"detail": ("Refresh token is required.")},
                status=400,
            )

        try:

            token = RefreshToken(refresh_token)

            session_id = token.get("session_id")

            token.blacklist()

            if session_id:

                SecuritySession.objects.filter(
                    user=request.user,
                    session_token_id=session_id,
                    is_active=True,
                ).update(
                    is_active=False,
                    logged_out_at=timezone.now(),
                )

            create_audit_log(
                user=request.user,
                action=AuditLog.Action.LOGOUT,
                resource_type="Authentication",
                resource_id=request.user.id,
                request=request,
                metadata={
                    "logout_method": "JWT",
                    "session_id": session_id,
                },
            )

            return Response(
                {"detail": ("Successfully logged out.")},
                status=200,
            )

        except Exception:

            return Response(
                {"detail": ("Invalid or already " "blacklisted refresh token.")},
                status=400,
            )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        serializer = UserSerializer(request.user)

        return Response(serializer.data)
