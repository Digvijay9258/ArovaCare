from django.utils import timezone

from rest_framework import serializers

from .models import Consent


class ConsentSerializer(serializers.ModelSerializer):

    patient_email = serializers.EmailField(
        source="patient.email",
        read_only=True,
    )

    doctor_email = serializers.EmailField(
        source="doctor.email",
        read_only=True,
    )

    record_title = serializers.CharField(
        source="record.title",
        read_only=True,
    )

    class Meta:
        model = Consent

        fields = [
            "id",
            "patient",
            "patient_email",
            "doctor",
            "doctor_email",
            "record",
            "record_title",
            "consent_type",
            "purpose",
            "status",
            "granted_at",
            "expires_at",
            "revoked_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "patient",
            "patient_email",
            "doctor_email",
            "record_title",
            "status",
            "granted_at",
            "revoked_at",
            "created_at",
            "updated_at",
        ]

    def validate_doctor(self, doctor):
        if doctor.role != "DOCTOR":
            raise serializers.ValidationError("Selected user is not a doctor.")

        return doctor

    def validate_record(self, record):
        request = self.context.get("request")

        if request and record.patient != request.user:
            raise serializers.ValidationError(
                "You can only give consent for your own medical records."
            )

        return record

    def validate(self, attrs):
        request = self.context.get("request")

        doctor = attrs.get("doctor")
        record = attrs.get("record")
        consent_type = attrs.get("consent_type")
        expires_at = attrs.get("expires_at")

        # ---------------------------------------------------------
        # EXPIRY VALIDATION
        # ---------------------------------------------------------
        if expires_at and expires_at <= timezone.now():
            raise serializers.ValidationError(
                {"expires_at": "Expiry time must be in the future."}
            )

        # ---------------------------------------------------------
        # RECORD REQUIRED FOR MEDICAL_RECORD CONSENT
        # ---------------------------------------------------------
        if consent_type == Consent.ConsentType.MEDICAL_RECORD and not record:
            raise serializers.ValidationError(
                {"record": "A medical record is required for this consent type."}
            )

        # ---------------------------------------------------------
        # DUPLICATE ACTIVE CONSENT CHECK
        # ---------------------------------------------------------
        if request and doctor:
            existing_consents = Consent.objects.filter(
                patient=request.user,
                doctor=doctor,
                status=Consent.Status.ACTIVE,
            )

            if record:
                existing_consents = existing_consents.filter(record=record)

            if existing_consents.exists():
                raise serializers.ValidationError(
                    "An active consent already exists for this doctor and record."
                )

        return attrs
