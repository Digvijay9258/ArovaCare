from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Consultation
from .serializers import ConsultationSerializer
from .permissions import IsDoctor, IsPatient


class DoctorConsultationListCreateView(generics.ListCreateAPIView):
    serializer_class = ConsultationSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsDoctor()]

        return [IsAuthenticated(), IsDoctor()]

    def get_queryset(self):
        return Consultation.objects.filter(doctor=self.request.user).select_related(
            "doctor",
            "patient",
            "appointment",
        )

    def perform_create(self, serializer):
        appointment = serializer.validated_data["appointment"]

        if appointment.doctor != self.request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "You can only create consultations for your own appointments."
            )

        if appointment.status not in ["ACCEPTED", "COMPLETED"]:
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                {
                    "appointment": (
                        "Consultation can only be created for "
                        "an accepted or completed appointment."
                    )
                }
            )

        if hasattr(appointment, "consultation"):
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                {"appointment": ("A consultation already exists for this appointment.")}
            )

        serializer.save(
            doctor=appointment.doctor,
            patient=appointment.patient,
        )


class DoctorConsultationDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated, IsDoctor]

    def get_queryset(self):
        return Consultation.objects.filter(doctor=self.request.user).select_related(
            "doctor",
            "patient",
            "appointment",
        )


class PatientConsultationListView(generics.ListAPIView):
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self):
        return Consultation.objects.filter(patient=self.request.user).select_related(
            "doctor",
            "patient",
            "appointment",
        )


class PatientConsultationDetailView(generics.RetrieveAPIView):
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self):
        return Consultation.objects.filter(patient=self.request.user).select_related(
            "doctor",
            "patient",
            "appointment",
        )
