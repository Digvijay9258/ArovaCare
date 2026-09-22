from rest_framework import serializers

from .models import IntegrityProof


class IntegrityProofSerializer(serializers.ModelSerializer):
    medical_record_id = serializers.IntegerField(
        source="medical_record.id",
        read_only=True,
    )

    created_by_email = serializers.EmailField(
        source="created_by.email",
        read_only=True,
    )

    class Meta:
        model = IntegrityProof
        fields = [
            "id",
            "medical_record_id",
            "record_hash",
            "hash_algorithm",
            "created_by_email",
            "proof_type",
            "block_reference",
            "previous_hash",
            "verification_count",
            "last_verified_at",
            "is_valid",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields
