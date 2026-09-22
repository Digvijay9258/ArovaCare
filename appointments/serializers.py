from datetime import datetime

from django.utils import timezone
from rest_framework import serializers

from .models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):

    patient_email = serializers.EmailField(
        source="patient.email",
        read_only=True,
    )

    doctor_email = serializers.EmailField(
        source="doctor.email",
        read_only=True,
    )

    class Meta:
        model = Appointment

        fields = [
            "id",
            "patient",
            "patient_email",
            "doctor",
            "doctor_email",
            "appointment_date",
            "appointment_time",
            "reason",
            "notes",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "patient",
            "patient_email",
            "doctor_email",
            "status",
            "created_at",
            "updated_at",
        ]

    def validate_doctor(self, doctor):
        # Make sure selected user has Doctor role
        if doctor.role != "DOCTOR":
            raise serializers.ValidationError("Selected user is not a doctor.")

        # Make sure doctor profile exists
        if not hasattr(doctor, "doctor_profile"):
            raise serializers.ValidationError("Doctor profile does not exist.")

        # Only verified doctors can receive appointments
        if doctor.doctor_profile.verification_status != "VERIFIED":
            raise serializers.ValidationError("Doctor is not verified yet.")

        return doctor

    def validate(self, attrs):
        appointment_date = attrs.get("appointment_date")
        appointment_time = attrs.get("appointment_time")

        if appointment_date and appointment_time:
            appointment_datetime = timezone.make_aware(
                datetime.combine(
                    appointment_date,
                    appointment_time,
                )
            )

            if appointment_datetime <= timezone.now():
                raise serializers.ValidationError(
                    "Appointment must be scheduled for a future date and time."
                )

        return attrs
