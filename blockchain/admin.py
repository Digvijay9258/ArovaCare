from django.contrib import admin

from .models import IntegrityProof


@admin.register(IntegrityProof)
class IntegrityProofAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "medical_record",
        "hash_algorithm",
        "proof_type",
        "is_valid",
        "verification_count",
        "created_by",
        "last_verified_at",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "is_valid",
        "hash_algorithm",
        "proof_type",
        "created_at",
    )

    search_fields = (
        "medical_record__title",
        "medical_record__patient__email",
        "record_hash",
        "block_reference",
        "created_by__email",
    )

    readonly_fields = (
        "id",
        "medical_record",
        "record_hash",
        "hash_algorithm",
        "proof_type",
        "block_reference",
        "previous_hash",
        "verification_count",
        "last_verified_at",
        "is_valid",
        "created_by",
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)
