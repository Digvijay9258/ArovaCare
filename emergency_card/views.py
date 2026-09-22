from django.http import HttpResponse

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from audit_logs.models import AuditLog
from audit_logs.services import create_audit_log
from users.permissions import IsPatient

from .models import EmergencyCard
from .qr_utils import generate_emergency_qr
from .serializers import (
    EmergencyCardSerializer,
    PublicEmergencyCardSerializer,
)


class EmergencyCardView(generics.RetrieveUpdateAPIView):
    """
    Patient's private Emergency Card.

    Only the patient who owns the card can access or update it.
    """

    serializer_class = EmergencyCardSerializer
    permission_classes = [
        IsAuthenticated,
        IsPatient,
    ]

    def get_object(self):

        card, created = EmergencyCard.objects.get_or_create(patient=self.request.user)

        return card

    def retrieve(self, request, *args, **kwargs):

        card = self.get_object()

        create_audit_log(
            user=request.user,
            action=AuditLog.Action.READ,
            resource_type="EmergencyCard",
            resource_id=card.id,
            request=request,
            metadata={
                "access_type": "PATIENT_PRIVATE",
                "patient_id": request.user.id,
            },
        )

        serializer = self.get_serializer(card)

        return Response(serializer.data)

    def update(self, request, *args, **kwargs):

        card = self.get_object()

        response = super().update(
            request,
            *args,
            **kwargs,
        )

        create_audit_log(
            user=request.user,
            action=AuditLog.Action.UPDATE,
            resource_type="EmergencyCard",
            resource_id=card.id,
            request=request,
            metadata={
                "access_type": "PATIENT_PRIVATE",
                "patient_id": request.user.id,
            },
        )

        return response


class PublicEmergencyCardView(generics.RetrieveAPIView):
    """
    Public Emergency Card endpoint.

    This endpoint is intentionally unauthenticated because
    emergency responders may scan the QR code without having
    an Arova account.

    Only limited emergency information is exposed by the
    PublicEmergencyCardSerializer.

    Raw medical records are never exposed here.
    """

    serializer_class = PublicEmergencyCardSerializer
    permission_classes = []

    lookup_field = "emergency_token"
    lookup_url_kwarg = "token"

    def get_queryset(self):

        return EmergencyCard.objects.filter(is_active=True).select_related(
            "patient",
            "patient__patient_profile",
        )

    def retrieve(self, request, *args, **kwargs):

        card = self.get_object()

        create_audit_log(
            user=None,
            action=AuditLog.Action.READ,
            resource_type="EmergencyCard",
            resource_id=card.id,
            request=request,
            metadata={
                "access_type": "EMERGENCY_QR",
                "public_access": True,
                "card_active": card.is_active,
                "patient_id": card.patient_id,
            },
        )

        serializer = self.get_serializer(card)

        return Response(serializer.data)


class EmergencyCardQRView(generics.GenericAPIView):
    """
    Generates the patient's Emergency Card QR code.

    The QR contains only the secure emergency endpoint URL.
    Private medical information is not embedded directly
    inside the QR code.
    """

    permission_classes = [
        IsAuthenticated,
        IsPatient,
    ]

    def get(self, request):

        card, created = EmergencyCard.objects.get_or_create(patient=request.user)

        qr_image = generate_emergency_qr(card.emergency_token)

        response = HttpResponse(content_type="image/png")

        qr_image.save(
            response,
            format="PNG",
        )

        create_audit_log(
            user=request.user,
            action=AuditLog.Action.READ,
            resource_type="EmergencyCard",
            resource_id=card.id,
            request=request,
            metadata={
                "access_type": "QR_GENERATION",
                "patient_id": request.user.id,
            },
        )

        return response
