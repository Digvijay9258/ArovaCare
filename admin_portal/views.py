from django.db.models import Count
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from audit_logs.models import AuditLog
from audit_logs.services import create_audit_log
from security.models import SecurityAlert, SecuritySession
from users.models import User

from .permissions import IsAdminUser
from .serializers import (
    AdminAuditLogSerializer,
    AdminSecurityAlertSerializer,
    AdminSecuritySessionSerializer,
    AdminUserSerializer,
)


class AdminSecurityOverviewView(generics.GenericAPIView):
    """
    Security overview for the Admin Portal.

    This endpoint exposes security monitoring information,
    not private medical-record contents.
    """

    permission_classes = [
        IsAuthenticated,
        IsAdminUser,
    ]

    def get(self, request):
        active_sessions = SecuritySession.objects.filter(
            is_active=True,
        ).count()

        total_sessions = SecuritySession.objects.count()

        unread_alerts = SecurityAlert.objects.filter(
            is_read=False,
        ).count()

        total_alerts = SecurityAlert.objects.count()

        total_audit_logs = AuditLog.objects.count()

        today = timezone.now().date()

        today_audit_logs = AuditLog.objects.filter(
            created_at__date=today,
        ).count()

        alert_breakdown = list(
            SecurityAlert.objects.values(
                "alert_type",
            )
            .annotate(
                count=Count("id"),
            )
            .order_by("-count")
        )

        return Response(
            {
                "sessions": {
                    "active": active_sessions,
                    "total": total_sessions,
                },
                "alerts": {
                    "unread": unread_alerts,
                    "total": total_alerts,
                    "breakdown": alert_breakdown,
                },
                "audit": {
                    "total": total_audit_logs,
                    "today": today_audit_logs,
                },
            }
        )


class AdminSecuritySessionListView(generics.ListAPIView):
    serializer_class = AdminSecuritySessionSerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminUser,
    ]

    def get_queryset(self):
        queryset = SecuritySession.objects.select_related("user").order_by(
            "-last_activity"
        )

        is_active = self.request.query_params.get("is_active")

        if is_active == "true":
            queryset = queryset.filter(is_active=True)

        elif is_active == "false":
            queryset = queryset.filter(is_active=False)

        return queryset


class AdminSecurityAlertListView(generics.ListAPIView):
    serializer_class = AdminSecurityAlertSerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminUser,
    ]

    def get_queryset(self):
        queryset = SecurityAlert.objects.select_related("user").order_by("-created_at")

        alert_type = self.request.query_params.get("alert_type")

        severity = self.request.query_params.get("severity")

        is_read = self.request.query_params.get("is_read")

        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)

        if severity:
            queryset = queryset.filter(severity=severity)

        if is_read == "true":
            queryset = queryset.filter(is_read=True)

        elif is_read == "false":
            queryset = queryset.filter(is_read=False)

        return queryset


class AdminAuditLogListView(generics.ListAPIView):
    serializer_class = AdminAuditLogSerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminUser,
    ]

    def get_queryset(self):
        queryset = AuditLog.objects.select_related("user").order_by("-created_at")

        action = self.request.query_params.get("action")

        resource_type = self.request.query_params.get("resource_type")

        user_id = self.request.query_params.get("user_id")

        if action:
            queryset = queryset.filter(action=action)

        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        return queryset


class AdminUserListView(generics.ListAPIView):
    """
    Admin-only user management list.

    Supports:
    - email search
    - role filtering
    - active/inactive filtering
    """

    serializer_class = AdminUserSerializer

    permission_classes = [
        IsAuthenticated,
        IsAdminUser,
    ]

    def get_queryset(self):
        queryset = User.objects.all().order_by("-created_at")

        search = self.request.query_params.get("search")

        role = self.request.query_params.get("role")

        is_active = self.request.query_params.get("is_active")

        if search:
            queryset = queryset.filter(email__icontains=search)

        if role:
            queryset = queryset.filter(role=role)

        if is_active == "true":
            queryset = queryset.filter(is_active=True)

        elif is_active == "false":
            queryset = queryset.filter(is_active=False)

        return queryset


class AdminUserDetailView(generics.RetrieveAPIView):
    serializer_class = AdminUserSerializer

    permission_classes = [
        IsAuthenticated,
        IsAdminUser,
    ]

    queryset = User.objects.all()


class AdminUserStatusView(generics.GenericAPIView):
    """
    Activate or deactivate a user account.

    Admin cannot deactivate itself.

    When a user is deactivated:
    - The account becomes inactive.
    - All active security sessions are terminated.
    - A security alert is generated.
    - An audit log is created.
    """

    permission_classes = [
        IsAuthenticated,
        IsAdminUser,
    ]

    queryset = User.objects.all()

    def post(self, request, pk):

        user = self.get_object()

        # ---------------------------------------------------------
        # PREVENT ADMIN SELF-DEACTIVATION
        # ---------------------------------------------------------
        if user == request.user:

            return Response(
                {"detail": ("You cannot deactivate " "your own admin account.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------------------
        # ACTIVATE / DEACTIVATE
        # ---------------------------------------------------------
        user.is_active = not user.is_active

        user.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        # ---------------------------------------------------------
        # DEACTIVATION SECURITY HARDENING
        # ---------------------------------------------------------
        terminated_sessions = 0

        if not user.is_active:

            now = timezone.now()

            terminated_sessions = SecuritySession.objects.filter(
                user=user,
                is_active=True,
            ).update(
                is_active=False,
                logged_out_at=now,
            )

            # -----------------------------------------------------
            # SECURITY ALERT
            # -----------------------------------------------------
            SecurityAlert.objects.create(
                user=user,
                alert_type=SecurityAlert.AlertType.SECURITY_EVENT,
                title="Account deactivated",
                message=(
                    "Your Arova account has been "
                    "deactivated by an administrator. "
                    "All active security sessions "
                    "have been terminated."
                ),
                severity="WARNING",
                metadata={
                    "action": "ACCOUNT_DEACTIVATED",
                    "admin_user_id": request.user.id,
                    "admin_user_email": request.user.email,
                    "terminated_sessions": terminated_sessions,
                },
            )

        else:

            # -----------------------------------------------------
            # SECURITY ALERT FOR REACTIVATION
            # -----------------------------------------------------
            SecurityAlert.objects.create(
                user=user,
                alert_type=SecurityAlert.AlertType.SECURITY_EVENT,
                title="Account reactivated",
                message=(
                    "Your Arova account has been " "reactivated by an administrator."
                ),
                severity="INFO",
                metadata={
                    "action": "ACCOUNT_REACTIVATED",
                    "admin_user_id": request.user.id,
                    "admin_user_email": request.user.email,
                },
            )

        # ---------------------------------------------------------
        # ADMIN AUDIT LOG
        # ---------------------------------------------------------
        action = "activated" if user.is_active else "deactivated"

        create_admin_audit_log(
            request=request,
            admin_user=request.user,
            target_user=user,
            action=action,
            terminated_sessions=terminated_sessions,
        )

        return Response(
            {
                "detail": (f"User has been " f"{action} successfully."),
                "user_id": user.id,
                "email": user.email,
                "is_active": user.is_active,
                "terminated_sessions": terminated_sessions,
            },
            status=status.HTTP_200_OK,
        )


def create_admin_audit_log(
    *,
    request,
    admin_user,
    target_user,
    action,
    terminated_sessions=0,
):
    """
    Creates an audit entry whenever an Admin changes
    a user's account status.
    """

    create_audit_log(
        user=admin_user,
        action=AuditLog.Action.UPDATE,
        resource_type="User",
        resource_id=target_user.id,
        request=request,
        metadata={
            "admin_action": action,
            "target_user_id": target_user.id,
            "target_user_email": target_user.email,
            "target_user_role": target_user.role,
            "terminated_sessions": terminated_sessions,
        },
    )
