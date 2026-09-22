from rest_framework import serializers

from .models import MedicalRecordAccess
from medical_records.models import MedicalRecord


class MedicalRecordAccessSerializer(serializers.ModelSerializer):

    patient_email = serializers.EmailField(
        source="patient.email",
        read_only=True
    )

    doctor_email = serializers.EmailField(
        source="doctor.email",
        read_only=True
    )

    record_title = serializers.CharField(
        source="record.title",
        read_only=True
    )

    class Meta:
        model = MedicalRecordAccess

        fields = [
            "id",
            "patient_email",
            "doctor_email",
            "record_title",
            "patient",
            "doctor",
            "record",
            "status",
            "granted_at",
            "expires_at",
        ]

        read_only_fields = [
            "id",
            "patient",
            "patient_email",
            "doctor_email",
            "record_title",
            "status",
            "granted_at",
        ]

    def validate_doctor(self, doctor):

        if doctor.role != "DOCTOR":
            raise serializers.ValidationError(
                "Selected user is not a doctor."
            )

        return doctor

    def validate_record(self, record):

        request = self.context.get("request")

        if request and record.patient != request.user:
            raise serializers.ValidationError(
                "You can only grant access to your own medical records."
            )

        return record

    def validate(self, attrs):

        doctor = attrs.get("doctor")
        record = attrs.get("record")

        if doctor and record:
            existing_access = MedicalRecordAccess.objects.filter(
                doctor=doctor,
                record=record,
                status="ACTIVE"
            ).exists()

            if existing_access:
                raise serializers.ValidationError(
                    "This doctor already has active access to this record."
                )

        return attrs