from rest_framework import serializers
from .models import PatientProfile


class PatientProfileSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = PatientProfile

        fields = [
            "id",
            "email",
            "full_name",
            "date_of_birth",
            "gender",
            "phone",
            "blood_group",
            "address",
            "emergency_contact_name",
            "emergency_contact_phone",
            "profile_photo",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "email",
            "created_at",
            "updated_at",
        ]
