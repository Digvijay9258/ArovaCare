from django.urls import path

from .views import PatientProfileView
from .timeline import PatientTimelineView

urlpatterns = [
    path(
        "profile/",
        PatientProfileView.as_view(),
        name="patient-profile",
    ),
    path(
        "timeline/",
        PatientTimelineView.as_view(),
        name="patient-timeline",
    ),
]
