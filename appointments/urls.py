from django.urls import path

from .views import (
    PatientAppointmentListCreateView,
    DoctorAppointmentListView,
    DoctorAppointmentStatusView,
    PatientCancelAppointmentView,
)

urlpatterns = [
    path(
        "",
        PatientAppointmentListCreateView.as_view(),
        name="patient-appointments",
    ),
    path(
        "doctor/",
        DoctorAppointmentListView.as_view(),
        name="doctor-appointments",
    ),
    path(
        "doctor/<int:pk>/status/",
        DoctorAppointmentStatusView.as_view(),
        name="doctor-appointment-status",
    ),
    path(
        "<int:pk>/cancel/",
        PatientCancelAppointmentView.as_view(),
        name="patient-cancel-appointment",
    ),
]
