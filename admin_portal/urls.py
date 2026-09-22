from django.urls import path

from .views import (
    AdminAuditLogListView,
    AdminSecurityAlertListView,
    AdminSecurityOverviewView,
    AdminSecuritySessionListView,
    AdminUserDetailView,
    AdminUserListView,
    AdminUserStatusView,
)

urlpatterns = [
    path(
        "security/overview/",
        AdminSecurityOverviewView.as_view(),
        name="admin-security-overview",
    ),
    path(
        "security/sessions/",
        AdminSecuritySessionListView.as_view(),
        name="admin-security-sessions",
    ),
    path(
        "security/alerts/",
        AdminSecurityAlertListView.as_view(),
        name="admin-security-alerts",
    ),
    path(
        "security/audit-logs/",
        AdminAuditLogListView.as_view(),
        name="admin-security-audit-logs",
    ),
    path(
        "users/",
        AdminUserListView.as_view(),
        name="admin-users",
    ),
    path(
        "users/<int:pk>/",
        AdminUserDetailView.as_view(),
        name="admin-user-detail",
    ),
    path(
        "users/<int:pk>/status/",
        AdminUserStatusView.as_view(),
        name="admin-user-status",
    ),
]
