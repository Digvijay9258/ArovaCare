from rest_framework import serializers

from .models import MedicalRecord


class MedicalRecordSerializer(serializers.ModelSerializer):

    patient_email = serializers.EmailField(source="patient.email", read_only=True)

    class Meta:
        model = MedicalRecord

        fields = [
            "id",
            "patient_email",
            "title",
            "record_type",
            "description",
            "file",
            "record_date",
            "uploaded_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "patient_email",
            "uploaded_at",
            "updated_at",
        ]
