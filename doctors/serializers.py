from rest_framework import serializers
from .models import DoctorProfile


class DoctorProfileSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = DoctorProfile

        fields = [
            "id",
            "email",
            "full_name",
            "specialization",
            "medical_registration_number",
            "qualification",
            "experience_years",
            "hospital_or_clinic",
            "consultation_fee",
            "bio",
            "profile_photo",
            "verification_status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "email",
            "verification_status",
            "created_at",
            "updated_at",
        ]


class DoctorVerificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = DoctorProfile

        fields = [
            "verification_status",
        ]

        extra_kwargs = {"verification_status": {"required": True}}

    def validate_verification_status(self, value):

        if value not in ["VERIFIED", "REJECTED"]:
            raise serializers.ValidationError("Status must be VERIFIED or REJECTED.")

        return value
