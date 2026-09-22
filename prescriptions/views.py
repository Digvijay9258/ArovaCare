from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsDoctor, IsPatient

from .models import Prescription
from .serializers import PrescriptionSerializer


class DoctorPrescriptionListCreateView(generics.ListCreateAPIView):

    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated, IsDoctor]

    def get_queryset(self):
        return (
            Prescription.objects.filter(doctor=self.request.user)
            .select_related(
                "patient",
                "doctor",
                "appointment",
            )
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user)


class PatientPrescriptionListView(generics.ListAPIView):

    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self):
        return (
            Prescription.objects.filter(patient=self.request.user)
            .select_related(
                "patient",
                "doctor",
                "appointment",
            )
            .order_by("-created_at")
        )


class PatientPrescriptionDetailView(generics.RetrieveAPIView):

    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self):
        return Prescription.objects.filter(patient=self.request.user).select_related(
            "patient",
            "doctor",
            "appointment",
        )
