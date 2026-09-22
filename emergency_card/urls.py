from django.urls import path

from .views import (
    EmergencyCardView,
    PublicEmergencyCardView,
    EmergencyCardQRView,
)

urlpatterns = [
    path("", EmergencyCardView.as_view(), name="emergency-card"),
    path("qr/", EmergencyCardQRView.as_view(), name="emergency-card-qr"),
    path(
        "<str:token>/",
        PublicEmergencyCardView.as_view(),
        name="public-emergency-card",
    ),
]
