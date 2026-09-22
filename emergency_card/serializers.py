from rest_framework import serializers

from .models import EmergencyCard
from .qr_utils import get_emergency_url


class EmergencyCardSerializer(serializers.ModelSerializer):
    patient_email = serializers.EmailField(
        source="patient.email",
        read_only=True,
    )

    patient_name = serializers.CharField(
        source="patient.patient_profile.full_name",
        read_only=True,
    )

    blood_group = serializers.CharField(
        source="patient.patient_profile.blood_group",
        read_only=True,
    )

    emergency_contact_name = serializers.CharField(
        source="patient.patient_profile.emergency_contact_name",
        read_only=True,
    )

    emergency_contact_phone = serializers.CharField(
        source="patient.patient_profile.emergency_contact_phone",
        read_only=True,
    )

    emergency_url = serializers.SerializerMethodField()

    def get_emergency_url(self, obj):
        return get_emergency_url(obj.emergency_token)

    class Meta:
        model = EmergencyCard

        fields = [
            "id",
            "patient_email",
            "patient_name",
            "blood_group",
            "emergency_contact_name",
            "emergency_contact_phone",
            "is_active",
            "allergies",
            "current_medications",
            "emergency_notes",
            "emergency_url",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "patient_email",
            "patient_name",
            "blood_group",
            "emergency_contact_name",
            "emergency_contact_phone",
            "emergency_url",
            "created_at",
            "updated_at",
        ]


class PublicEmergencyCardSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(
        source="patient.patient_profile.full_name",
        read_only=True,
    )

    blood_group = serializers.CharField(
        source="patient.patient_profile.blood_group",
        read_only=True,
    )

    emergency_contact_name = serializers.CharField(
        source="patient.patient_profile.emergency_contact_name",
        read_only=True,
    )

    emergency_contact_phone = serializers.CharField(
        source="patient.patient_profile.emergency_contact_phone",
        read_only=True,
    )

    class Meta:
        model = EmergencyCard

        fields = [
            "patient_name",
            "blood_group",
            "emergency_contact_name",
            "emergency_contact_phone",
            "allergies",
            "current_medications",
            "emergency_notes",
        ]

        read_only_fields = [
            "patient_name",
            "blood_group",
            "emergency_contact_name",
            "emergency_contact_phone",
            "allergies",
            "current_medications",
            "emergency_notes",
        ]
 