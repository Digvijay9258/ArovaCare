from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from access_control.models import MedicalRecordAccess
from audit_logs.models import AuditLog
from audit_logs.services import create_audit_log
from users.permissions import IsPatient

from blockchain.services import create_integrity_proof

from .models import MedicalRecord
from .serializers import MedicalRecordSerializer


class MedicalRecordListCreateView(generics.ListCreateAPIView):

    serializer_class = MedicalRecordSerializer

    permission_classes = [IsAuthenticated, IsPatient]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    def get_queryset(self):
        return MedicalRecord.objects.filter(patient=self.request.user).order_by(
            "-uploaded_at"
        )

    def perform_create(self, serializer):

        # -------------------------------------------------
        # CREATE MEDICAL RECORD
        # -------------------------------------------------

        record = serializer.save(patient=self.request.user)

        # -------------------------------------------------
        # AUDIT LOG
        # -------------------------------------------------

        create_audit_log(
            user=self.request.user,
            action=AuditLog.Action.CREATE,
            resource_type="MedicalRecord",
            resource_id=record.id,
            request=self.request,
            metadata={
                "record_title": record.title,
                "record_type": record.record_type,
            },
        )

        # -------------------------------------------------
        # BLOCKCHAIN / INTEGRITY PROOF
        # -------------------------------------------------

        create_integrity_proof(
            record=record,
            actor=self.request.user,
        )


class MedicalRecordDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = MedicalRecordSerializer

    permission_classes = [IsAuthenticated]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    def get_object(self):

        record = get_object_or_404(
            MedicalRecord,
            pk=self.kwargs["pk"],
        )

        user = self.request.user

        # -------------------------------------------------
        # PATIENT OWN RECORD
        # -------------------------------------------------

        if record.patient == user:

            self.is_doctor_access = False

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
                "You do not have permission to access this medical record."
            )

        self.is_doctor_access = True

        # -------------------------------------------------
        # AUDIT LOG
        # -------------------------------------------------

        create_audit_log(
            user=user,
            action=AuditLog.Action.READ,
            resource_type="MedicalRecord",
            resource_id=record.id,
            request=self.request,
            metadata={
                "access_type": "DOCTOR_GRANTED_ACCESS",
                "patient_id": record.patient_id,
                "record_title": record.title,
            },
        )

        return record

    def update(self, request, *args, **kwargs):

        # -------------------------------------------------
        # GET OBJECT AND CHECK ACCESS
        # -------------------------------------------------

        record = self.get_object()

        if getattr(self, "is_doctor_access", False):

            raise PermissionDenied("Doctors have read-only access to medical records.")

        # -------------------------------------------------
        # UPDATE MEDICAL RECORD
        # -------------------------------------------------

        response = super().update(
            request,
            *args,
            **kwargs,
        )

        # -------------------------------------------------
        # AUDIT LOG
        # -------------------------------------------------

        create_audit_log(
            user=request.user,
            action=AuditLog.Action.UPDATE,
            resource_type="MedicalRecord",
            resource_id=record.id,
            request=request,
        )

        # -------------------------------------------------
        # CREATE NEW INTEGRITY PROOF
        # -------------------------------------------------

        updated_record = MedicalRecord.objects.get(pk=record.id)

        create_integrity_proof(
            record=updated_record,
            actor=request.user,
        )

        return response

    def destroy(self, request, *args, **kwargs):

        # -------------------------------------------------
        # GET OBJECT AND CHECK ACCESS
        # -------------------------------------------------

        record = self.get_object()

        if getattr(self, "is_doctor_access", False):

            raise PermissionDenied("Doctors cannot delete medical records.")

        record_id = record.id

        # -------------------------------------------------
        # DELETE MEDICAL RECORD
        # -------------------------------------------------

        response = super().destroy(
            request,
            *args,
            **kwargs,
        )

        # -------------------------------------------------
        # AUDIT LOG
        # -------------------------------------------------

        create_audit_log(
            user=request.user,
            action=AuditLog.Action.DELETE,
            resource_type="MedicalRecord",
            resource_id=record_id,
            request=request,
        )

        return response
