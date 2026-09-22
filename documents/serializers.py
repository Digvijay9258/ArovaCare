from rest_framework import serializers

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):

    patient_email = serializers.EmailField(
        source="patient.email",
        read_only=True,
    )

    document_type_display = serializers.CharField(
        source="get_document_type_display",
        read_only=True,
    )

    visibility_display = serializers.CharField(
        source="get_visibility_display",
        read_only=True,
    )

    class Meta:
        model = Document

        fields = [
            "id",
            "patient_email",
            "title",
            "document_type",
            "document_type_display",
            "description",
            "file",
            "document_date",
            "visibility",
            "visibility_display",
            "uploaded_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "patient_email",
            "document_type_display",
            "visibility_display",
            "uploaded_at",
            "updated_at",
        ]

    def validate_title(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Document title cannot be empty.")

        return value
