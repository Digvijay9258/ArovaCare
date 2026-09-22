from django.conf import settings
from django.db import models


class IntegrityProof(models.Model):
    medical_record = models.ForeignKey(
        "medical_records.MedicalRecord",
        on_delete=models.CASCADE,
        related_name="integrity_proofs",
    )

    record_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text=("SHA-256 hash of the canonical medical record data."),
    )

    hash_algorithm = models.CharField(
        max_length=20,
        default="SHA-256",
    )

    proof_type = models.CharField(
        max_length=30,
        default="MEDICAL_RECORD",
    )

    block_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=("Optional future blockchain/ledger transaction reference."),
    )

    previous_hash = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text=("Hash of the previous integrity proof for this record."),
    )

    verification_count = models.PositiveIntegerField(
        default=0,
    )

    last_verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    is_valid = models.BooleanField(
        default=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_integrity_proofs",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=[
                    "medical_record",
                    "-created_at",
                ],
            ),
            models.Index(
                fields=["record_hash"],
            ),
            models.Index(
                fields=[
                    "is_valid",
                    "-created_at",
                ],
            ),
        ]

    def __str__(self):
        return (
            f"Integrity Proof #{self.id} - " f"Medical Record #{self.medical_record_id}"
        )
