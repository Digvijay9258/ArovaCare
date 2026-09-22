from rest_framework import serializers

from appointments.models import Appointment
from .models import Prescription


class PrescriptionSerializer(serializers.ModelSerializer):

    patient_email = serializers.EmailField(
        source="patient.email",
        read_only=True,
    )

    doctor_email = serializers.EmailField(
        source="doctor.email",
        read_only=True,
    )

    class Meta:
        model = Prescription

        fields = [
            "id",
            "patient",
            "patient_email",
            "doctor",
            "doctor_email",
            "appointment",
            "diagnosis",
            "medicines",
            "instructions",
            "follow_up_date",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "patient",
            "patient_email",
            "doctor",
            "doctor_email",
            "created_at",
            "updated_at",
        ]

    def validate_appointment(self, appointment):

        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")

        doctor = request.user

        # Appointment must belong to the logged-in doctor
        if appointment.doctor != doctor:
            raise serializers.ValidationError(
                "You can only create prescriptions for your own appointments."
            )

        # Prescription should be created only after appointment is accepted
        if appointment.status not in ["ACCEPTED", "COMPLETED"]:
            raise serializers.ValidationError(
                "Prescription can only be created for an accepted or completed appointment."
            )

        # One prescription per appointment
        if hasattr(appointment, "prescription"):
            raise serializers.ValidationError(
                "A prescription already exists for this appointment."
            )

        return appointment

    def validate_medicines(self, medicines):

        if not isinstance(medicines, list):
            raise serializers.ValidationError("Medicines must be provided as a list.")

        if not medicines:
            raise serializers.ValidationError("At least one medicine is required.")

        for medicine in medicines:

            if not isinstance(medicine, dict):
                raise serializers.ValidationError("Each medicine must be an object.")

            required_fields = [
                "name",
                "dosage",
                "frequency",
                "duration",
            ]

            for field in required_fields:
                if not medicine.get(field):
                    raise serializers.ValidationError(
                        f"Medicine field '{field}' is required."
                    )

        return medicines

    def validate(self, attrs):

        appointment = attrs.get("appointment")

        if appointment:
            attrs["patient"] = appointment.patient

        return attrs
