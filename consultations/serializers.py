from rest_framework import serializers

from .models import Consultation


class ConsultationSerializer(serializers.ModelSerializer):
    doctor_email = serializers.EmailField(source="doctor.email", read_only=True)

    patient_email = serializers.EmailField(source="patient.email", read_only=True)

    appointment_id = serializers.IntegerField(source="appointment.id", read_only=True)

    class Meta:
        model = Consultation
        fields = [
            "id",
            "appointment",
            "appointment_id",
            "doctor",
            "doctor_email",
            "patient",
            "patient_email",
            "status",
            "symptoms",
            "clinical_notes",
            "diagnosis",
            "treatment_plan",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "doctor",
            "doctor_email",
            "patient",
            "patient_email",
            "appointment_id",
            "created_at",
            "updated_at",
        ]
