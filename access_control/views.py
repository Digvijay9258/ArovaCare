from django.db import models
from django.utils import timezone

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers

from .models import MedicalRecordAccess
from .serializers import MedicalRecordAccessSerializer
from .permissions import IsPatient

from audit_logs.models import AuditLog
from audit_logs.services import create_audit_log


class AccessGrantListCreateView(generics.ListCreateAPIView):
    serializer_class = MedicalRecordAccessSerializer
    permission_classes = [IsPatient]

    def get_queryset(self):
        return (
            MedicalRecordAccess.objects.filter(patient=self.request.user)
            .select_related(
                "patient",
                "doctor",
                "record",
            )
            .order_by("-granted_at")
        )

    def perform_create(self, serializer):
        access = serializer.save(patient=self.request.user)

        create_audit_log(
            user=self.request.user,
            action=AuditLog.Action.GRANT_ACCESS,
            resource_type="MedicalRecordAccess",
            resource_id=access.id,
            request=self.request,
            metadata={
                "doctor_id": access.doctor_id,
                "record_id": access.record_id,
                "record_title": (access.record.title if access.record else None),
            },
        )


class AccessRevokeView(generics.UpdateAPIView):
    serializer_class = MedicalRecordAccessSerializer
    permission_classes = [IsPatient]

    http_method_names = ["patch"]

    def get_queryset(self):
        return MedicalRecordAccess.objects.filter(patient=self.request.user)

    def perform_update(self, serializer):

        access = self.get_object()

        if access.status != "ACTIVE":
            raise serializers.ValidationError("Only active access can be revoked.")

        access = serializer.save(status="REVOKED")

        create_audit_log(
            user=self.request.user,
            action=AuditLog.Action.REVOKE_ACCESS,
            resource_type="MedicalRecordAccess",
            resource_id=access.id,
            request=self.request,
            metadata={
                "doctor_id": access.doctor_id,
                "record_id": access.record_id,
                "record_title": (access.record.title if access.record else None),
            },
        )


class DoctorAccessibleRecordsView(generics.ListAPIView):
    serializer_class = MedicalRecordAccessSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        return (
            MedicalRecordAccess.objects.filter(
                doctor=user,
                status="ACTIVE",
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


class GrantMedicalRecordAccessView(generics.CreateAPIView):
    serializer_class = MedicalRecordAccessSerializer
    permission_classes = [IsPatient]

    def perform_create(self, serializer):

        access = serializer.save(
            patient=self.request.user,
            status="ACTIVE",
        )

        create_audit_log(
            user=self.request.user,
            action=AuditLog.Action.GRANT_ACCESS,
            resource_type="MedicalRecordAccess",
            resource_id=access.id,
            request=self.request,
            metadata={
                "doctor_id": access.doctor_id,
                "record_id": access.record_id,
                "record_title": (access.record.title if access.record else None),
            },
        )
