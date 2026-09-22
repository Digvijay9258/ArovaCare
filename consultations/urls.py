from django.urls import path

from .views import (
    DoctorConsultationListCreateView,
    DoctorConsultationDetailView,
    PatientConsultationListView,
    PatientConsultationDetailView,
)

urlpatterns = [
    path(
        "doctor/",
        DoctorConsultationListCreateView.as_view(),
        name="doctor-consultations",
    ),
    path(
        "doctor/<int:pk>/",
        DoctorConsultationDetailView.as_view(),
        name="doctor-consultation-detail",
    ),
    path(
        "patient/",
        PatientConsultationListView.as_view(),
        name="patient-consultations",
    ),
    path(
        "patient/<int:pk>/",
        PatientConsultationDetailView.as_view(),
        name="patient-consultation-detail",
    ),
]
