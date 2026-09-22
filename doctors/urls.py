from django.urls import path

from .views import (
    DoctorProfileView,
    DoctorVerificationView,
    DoctorListView,
)

urlpatterns = [
    path(
        "",
        DoctorListView.as_view(),
        name="doctor-list",
    ),
    path(
        "profile/",
        DoctorProfileView.as_view(),
        name="doctor-profile",
    ),
    path(
        "<int:pk>/verify/",
        DoctorVerificationView.as_view(),
        name="doctor-verify",
    ),
]
