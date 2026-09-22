from django.urls import path

from .views import (
    MedicalRecordIntegrityVerifyView,
    MedicalRecordIntegrityHistoryView,
)

urlpatterns = [
    path(
        "records/<int:record_id>/verify/",
        MedicalRecordIntegrityVerifyView.as_view(),
        name="medical-record-integrity-verify",
    ),
    path(
        "records/<int:record_id>/history/",
        MedicalRecordIntegrityHistoryView.as_view(),
        name="medical-record-integrity-history",
    ),
]
