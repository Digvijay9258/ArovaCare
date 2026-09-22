from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated

from access_control.models import MedicalRecordAccess

from .models import Document
from .serializers import DocumentSerializer


class DocumentListCreateView(generics.ListCreateAPIView):

    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    def get_queryset(self):
        user = self.request.user

        return (
            Document.objects.filter(patient=user)
            .select_related("patient")
            .order_by("-uploaded_at")
        )

    def perform_create(self, serializer):

        user = self.request.user

        if getattr(user, "role", None) != "PATIENT":
            raise PermissionDenied("Only patients can upload documents.")

        serializer.save(patient=user)


class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    def get_object(self):

        document = get_object_or_404(
            Document.objects.select_related("patient"),
            pk=self.kwargs["pk"],
        )

        user = self.request.user

        # --------------------------------------------------
        # PATIENT
        # --------------------------------------------------

        if document.patient == user:

            self.is_doctor_access = False

            return document

        # --------------------------------------------------
        # DOCTOR ACCESS
        # --------------------------------------------------

        has_access = (
            MedicalRecordAccess.objects.filter(
                record__patient=document.patient,
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
                "You do not have permission to access this document."
            )

        self.is_doctor_access = True

        return document

    def update(self, request, *args, **kwargs):

        self.get_object()

        if getattr(self, "is_doctor_access", False):

            raise PermissionDenied("Doctors have read-only access to documents.")

        return super().update(
            request,
            *args,
            **kwargs,
        )

    def destroy(self, request, *args, **kwargs):

        self.get_object()

        if getattr(self, "is_doctor_access", False):

            raise PermissionDenied("Doctors cannot delete documents.")

        return super().destroy(
            request,
            *args,
            **kwargs,
        )
