from django.urls import path

from .views import (
    ConsentListCreateView,
    ConsentDetailView,
    ConsentRevokeView,
    DoctorConsentListView,
)

urlpatterns = [
    path(
        "",
        ConsentListCreateView.as_view(),
        name="consent-list-create",
    ),
    path(
        "<int:pk>/",
        ConsentDetailView.as_view(),
        name="consent-detail",
    ),
    path(
        "<int:pk>/revoke/",
        ConsentRevokeView.as_view(),
        name="consent-revoke",
    ),
    path(
        "doctor/",
        DoctorConsentListView.as_view(),
        name="doctor-consent-list",
    ),
]
