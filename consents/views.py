from django.db import models
from django.utils import timezone

from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsPatient

from audit_logs.models import AuditLog
from audit_logs.services import create_audit_log

from .models import Consent
from .serializers import ConsentSerializer


class ConsentListCreateView(generics.ListCreateAPIView):
    """
    Patient can view and create their own consents.
    """

    serializer_class = ConsentSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self):
        return (
            Consent.objects.filter(patient=self.request.user)
            .select_related(
                "patient",
                "doctor",
                "record",
            )
            .order_by("-granted_at")
        )

    def perform_create(self, serializer):
        consent = serializer.save(
            patient=self.request.user,
            status=Consent.Status.ACTIVE,
        )

        create_audit_log(
            user=self.request.user,
            action=AuditLog.Action.GRANT_CONSENT,
            resource_type="Consent",
            resource_id=consent.id,
            request=self.request,
            metadata={
                "doctor_id": consent.doctor_id,
                "record_id": consent.record_id,
                "consent_type": consent.consent_type,
                "purpose": consent.purpose,
            },
        )


class ConsentDetailView(generics.RetrieveAPIView):
    """
    Patient can view one of their own consents.
    """

    serializer_class = ConsentSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self):
        return Consent.objects.filter(patient=self.request.user).select_related(
            "patient",
            "doctor",
            "record",
        )


class ConsentRevokeView(generics.UpdateAPIView):
    """
    Patient can revoke their own active consent.
    """

    serializer_class = ConsentSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    http_method_names = ["patch"]

    def get_queryset(self):
        return Consent.objects.filter(
            patient=self.request.user,
        )

    def perform_update(self, serializer):
        consent = self.get_object()

        if consent.status != Consent.Status.ACTIVE:
            raise serializers.ValidationError("Only active consent can be revoked.")

        consent = serializer.save(
            status=Consent.Status.REVOKED,
            revoked_at=timezone.now(),
        )

        create_audit_log(
            user=self.request.user,
            action=AuditLog.Action.REVOKE_CONSENT,
            resource_type="Consent",
            resource_id=consent.id,
            request=self.request,
            metadata={
                "doctor_id": consent.doctor_id,
                "record_id": consent.record_id,
                "consent_type": consent.consent_type,
                "purpose": consent.purpose,
            },
        )


class DoctorConsentListView(generics.ListAPIView):
    """
    Doctor can see active consents granted to them.
    Expired consents are automatically excluded.
    """

    serializer_class = ConsentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        return (
            Consent.objects.filter(
                doctor=user,
                status=Consent.Status.ACTIVE,
            )
            .filter(
                models.Q(expires_at__isnull=True)
                | models.Q(expires_at__gt=timezone.now())
            )
            .select_related(
                "patient",
                "doctor",
                "record",
            )
            .order_by("-granted_at")
        )
