from django.urls import path

from .views import (
    AccessGrantListCreateView,
    AccessRevokeView,
    DoctorAccessibleRecordsView,
    GrantMedicalRecordAccessView,
)

urlpatterns = [
    path(
        "",
        AccessGrantListCreateView.as_view(),
        name="access-list-create",
    ),
    path(
        "<int:pk>/revoke/",
        AccessRevokeView.as_view(),
        name="access-revoke",
    ),
    path(
        "doctor/records/",
        DoctorAccessibleRecordsView.as_view(),
        name="doctor-accessible-records",
    ),
    path(
        "grant/",
        GrantMedicalRecordAccessView.as_view(),
        name="grant-medical-record-access",
    ),
]
