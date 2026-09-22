import hashlib
import json

from django.db import transaction
from django.utils import timezone

from audit_logs.services import create_audit_log

from .models import IntegrityProof


def build_canonical_record_data(record):
    """
    Build a deterministic representation of a medical record.

    We intentionally exclude:
    - uploaded file contents
    - URLs
    - updated_at
    - uploaded_at

    The integrity hash represents the important medical-record metadata,
    not the physical file bytes.
    """

    return {
        "id": record.id,
        "patient_id": record.patient_id,
        "title": record.title,
        "record_type": record.record_type,
        "description": record.description or "",
        "record_date": (record.record_date.isoformat() if record.record_date else None),
    }


def generate_record_hash(record):
    """
    Generate a deterministic SHA-256 hash for a medical record.
    """

    canonical_data = build_canonical_record_data(record)

    canonical_json = json.dumps(
        canonical_data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


@transaction.atomic
def create_integrity_proof(record, actor=None):
    """
    Create a new integrity proof for a medical record.

    The previous proof hash is linked through previous_hash,
    creating a tamper-evident chain.
    """

    record_hash = generate_record_hash(record)

    previous_proof = (
        IntegrityProof.objects.filter(medical_record=record)
        .order_by("-created_at", "-id")
        .first()
    )

    previous_hash = previous_proof.record_hash if previous_proof else None

    proof = IntegrityProof.objects.create(
        medical_record=record,
        record_hash=record_hash,
        hash_algorithm="SHA-256",
        created_by=actor,
        proof_type="MEDICAL_RECORD",
        previous_hash=previous_hash,
        is_valid=True,
    )

    if actor:
        create_audit_log(
            user=actor,
            action="CREATE",
            resource_type="IntegrityProof",
            resource_id=str(proof.id),
            metadata={
                "medical_record_id": record.id,
                "hash_algorithm": "SHA-256",
            },
        )

    return proof


@transaction.atomic
def verify_record_integrity(record, actor=None):
    """
    Verify the current medical record against its latest integrity proof.
    """

    latest_proof = (
        IntegrityProof.objects.filter(medical_record=record)
        .order_by("-created_at", "-id")
        .first()
    )

    if not latest_proof:
        return {
            "verified": False,
            "status": "NO_PROOF",
            "message": "No integrity proof exists for this medical record.",
            "medical_record_id": record.id,
        }

    current_hash = generate_record_hash(record)

    is_valid = current_hash == latest_proof.record_hash

    latest_proof.verification_count += 1
    latest_proof.last_verified_at = timezone.now()
    latest_proof.is_valid = is_valid
    latest_proof.save(
        update_fields=[
            "verification_count",
            "last_verified_at",
            "is_valid",
            "updated_at",
        ]
    )

    if actor:
        create_audit_log(
            user=actor,
            action="READ",
            resource_type="IntegrityProof",
            resource_id=str(latest_proof.id),
            metadata={
                "medical_record_id": record.id,
                "verified": is_valid,
                "verification_result": ("VALID" if is_valid else "TAMPERED"),
            },
        )

    return {
        "verified": is_valid,
        "status": "VALID" if is_valid else "TAMPERED",
        "message": (
            "Medical record integrity verified successfully."
            if is_valid
            else "Medical record integrity verification failed."
        ),
        "medical_record_id": record.id,
        "proof_id": latest_proof.id,
        "stored_hash": latest_proof.record_hash,
        "current_hash": current_hash,
        "hash_algorithm": latest_proof.hash_algorithm,
        "verified_at": latest_proof.last_verified_at,
    }
