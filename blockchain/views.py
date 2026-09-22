from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from access_control.models import MedicalRecordAccess
from audit_logs.models import AuditLog
from audit_logs.services import create_audit_log

from medical_records.models import MedicalRecord

from .models import IntegrityProof
from .serializers import IntegrityProofSerializer
from .services import verify_record_integrity


class MedicalRecordIntegrityVerifyView(generics.RetrieveAPIView):
    """
    Verify the integrity of a medical record.

    Access:
    - Patient who owns the record
    - Doctor with active access to the record
    """

    serializer_class = IntegrityProofSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        record = get_object_or_404(
            MedicalRecord,
            pk=self.kwargs["record_id"],
        )

        user = self.request.user

        # -------------------------------------------------
        # PATIENT OWN RECORD
        # -------------------------------------------------

        if record.patient == user:
            return record

        # -------------------------------------------------
        # DOCTOR ACCESS CHECK
        # -------------------------------------------------

        has_access = (
            MedicalRecordAccess.objects.filter(
                record=record,
                doctor=user,
                status="ACTIVE",
            )
            .filter(
                models.Q(expires_at__isnull=True)
                | models.Q(expires_at__gt=timezone.now())
            )
            .exists()
        )

        if not has_access:
            raise PermissionDenied(
                "You do not have permission to verify this medical record."
            )

        return record

    def retrieve(self, request, *args, **kwargs):
        record = self.get_object()

        # -------------------------------------------------
        # VERIFY RECORD
        # -------------------------------------------------

        verification_result = verify_record_integrity(
            record=record,
            actor=request.user,
        )

        # -------------------------------------------------
        # AUDIT LOG
        # -------------------------------------------------

        create_audit_log(
            user=request.user,
            action=AuditLog.Action.READ,
            resource_type="MedicalRecordIntegrity",
            resource_id=record.id,
            request=request,
            metadata={
                "medical_record_id": record.id,
                "verification_status": verification_result["status"],
                "verified": verification_result["verified"],
            },
        )

        return Response(
            verification_result,
            status=200,
        )


class MedicalRecordIntegrityHistoryView(generics.ListAPIView):
    """
    Return integrity proof history for a medical record.

    Only the patient or a doctor with active access can view
    the integrity history.
    """

    serializer_class = IntegrityProofSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        record = get_object_or_404(
            MedicalRecord,
            pk=self.kwargs["record_id"],
        )

        user = self.request.user

        # -------------------------------------------------
        # PATIENT
        # -------------------------------------------------

        if record.patient == user:
            return IntegrityProof.objects.filter(medical_record=record).select_related(
                "created_by",
                "medical_record",
            )

        # -------------------------------------------------
        # DOCTOR
        # -------------------------------------------------

        has_access = (
            MedicalRecordAccess.objects.filter(
                record=record,
                doctor=user,
                status="ACTIVE",
            )
            .filter(
                models.Q(expires_at__isnull=True)
                | models.Q(expires_at__gt=timezone.now())
            )
            .exists()
        )

        if not has_access:
            raise PermissionDenied(
                "You do not have permission to view integrity history."
            )

        return (
            IntegrityProof.objects.filter(medical_record=record)
            .select_related(
                "created_by",
                "medical_record",
            )
            .order_by("-created_at")
        )
