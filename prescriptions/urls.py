from django.urls import path

from .views import (
    DoctorPrescriptionListCreateView,
    PatientPrescriptionListView,
    PatientPrescriptionDetailView,
)

urlpatterns = [
    path(
        "doctor/",
        DoctorPrescriptionListCreateView.as_view(),
        name="doctor-prescription-list-create",
    ),
    path(
        "patient/",
        PatientPrescriptionListView.as_view(),
        name="patient-prescription-list",
    ),
    path(
        "patient/<int:pk>/",
        PatientPrescriptionDetailView.as_view(),
        name="patient-prescription-detail",
    ),
]
