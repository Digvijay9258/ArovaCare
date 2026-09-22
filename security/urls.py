from django.urls import path

from .views import (
    ActiveConsentSecurityView,
    EmergencyAccessDetailView,
    EmergencyAccessListView,
    EmergencyAccessRequestCreateView,
    EmergencyAccessRevokeView,
    EmergencyAccessUseView,
    LogoutAllSessionsView,
    MFAView,
    MFADisableView,
    MFAVerifyView,
    PasswordChangeView,
    SecurityActivityView,
    SecurityAlertListView,
    SecurityAlertReadView,
    SecuritySessionListView,
)

urlpatterns = [
    # Security Sessions
    path(
        "sessions/",
        SecuritySessionListView.as_view(),
        name="security-sessions",
    ),
    path(
        "sessions/logout-all/",
        LogoutAllSessionsView.as_view(),
        name="logout-all-sessions",
    ),
    # Security Activity & Alerts
    path(
        "activity/",
        SecurityActivityView.as_view(),
        name="security-activity",
    ),
    path(
        "alerts/",
        SecurityAlertListView.as_view(),
        name="security-alerts",
    ),
    path(
        "alerts/<int:pk>/read/",
        SecurityAlertReadView.as_view(),
        name="security-alert-read",
    ),
    # Password
    path(
        "password/change/",
        PasswordChangeView.as_view(),
        name="password-change",
    ),
    # MFA
    path(
        "mfa/",
        MFAView.as_view(),
        name="mfa",
    ),
    path(
        "mfa/verify/",
        MFAVerifyView.as_view(),
        name="mfa-verify",
    ),
    path(
        "mfa/disable/",
        MFADisableView.as_view(),
        name="mfa-disable",
    ),
    # Consent Security
    path(
        "consents/",
        ActiveConsentSecurityView.as_view(),
        name="active-consents",
    ),
    # Emergency Access
    path(
        "emergency-access/",
        EmergencyAccessListView.as_view(),
        name="emergency-access-list",
    ),
    path(
        "emergency-access/request/",
        EmergencyAccessRequestCreateView.as_view(),
        name="emergency-access-request",
    ),
    path(
        "emergency-access/<int:pk>/",
        EmergencyAccessDetailView.as_view(),
        name="emergency-access-detail",
    ),
    path(
        "emergency-access/<int:pk>/use/",
        EmergencyAccessUseView.as_view(),
        name="emergency-access-use",
    ),
    path(
        "emergency-access/<int:pk>/revoke/",
        EmergencyAccessRevokeView.as_view(),
        name="emergency-access-revoke",
    ),
]
