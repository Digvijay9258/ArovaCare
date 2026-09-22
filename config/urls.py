"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin
    path(
        "admin/",
        admin.site.urls,
    ),
    # Authentication
    path(
        "api/auth/",
        include("users.urls"),
    ),
    # Patient
    path(
        "api/patients/",
        include("patients.urls"),
    ),
    # Doctor
    path(
        "api/doctors/",
        include("doctors.urls"),
    ),
    # Medical Records
    path(
        "api/medical-records/",
        include("medical_records.urls"),
    ),
    # Medical Record Access Control
    path(
        "api/access/",
        include("access_control.urls"),
    ),
    # Backward-compatible access-control prefix
    path(
        "api/access-control/",
        include("access_control.urls"),
    ),
    # Appointments
    path(
        "api/appointments/",
        include("appointments.urls"),
    ),
    # Prescriptions
    path(
        "api/prescriptions/",
        include("prescriptions.urls"),
    ),
    # Consultations
    path(
        "api/consultations/",
        include("consultations.urls"),
    ),
    # Secure Chat
    path(
        "api/chat/",
        include("chat.urls"),
    ),
    # Notifications
    path(
        "api/notifications/",
        include("notifications.urls"),
    ),
    # Documents
    path(
        "api/documents/",
        include("documents.urls"),
    ),
    # Consent Management
    path(
        "api/consents/",
        include("consents.urls"),
    ),
    # Emergency Medical Card
    path(
        "api/emergency-card/",
        include("emergency_card.urls"),
    ),
    # Security Center
    path(
        "api/security/",
        include("security.urls"),
    ),
    # Admin Portal APIs
    path(
        "api/admin/",
        include("admin_portal.urls"),
    ),
    # Blockchain / Medical Record Integrity
    path(
        "api/blockchain/",
        include("blockchain.urls"),
    ),
    # Payments / Revenue
    path(
        "api/payments/",
        include("payments.urls"),
    ),
]


urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT,
)
