from django.conf import settings
from django.db import models


class Document(models.Model):

    class DocumentType(models.TextChoices):
        MEDICAL_REPORT = "MEDICAL_REPORT", "Medical Report"
        LAB_REPORT = "LAB_REPORT", "Lab Report"
        BLOOD_REPORT = "BLOOD_REPORT", "Blood Report"
        XRAY = "XRAY", "X-Ray"
        MRI = "MRI", "MRI"
        CT_SCAN = "CT_SCAN", "CT Scan"
        PRESCRIPTION = "PRESCRIPTION", "Prescription"
        DISCHARGE_SUMMARY = "DISCHARGE_SUMMARY", "Discharge Summary"
        INSURANCE = "INSURANCE", "Insurance"
        ID_DOCUMENT = "ID_DOCUMENT", "ID Document"
        OTHER = "OTHER", "Other"

    class Visibility(models.TextChoices):
        PRIVATE = "PRIVATE", "Private"
        SHARED = "SHARED", "Shared"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
    )

    title = models.CharField(
        max_length=255,
    )

    document_type = models.CharField(
        max_length=50,
        choices=DocumentType.choices,
        default=DocumentType.OTHER,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    file = models.FileField(
        upload_to="documents/%Y/%m/",
    )

    document_date = models.DateField(
        null=True,
        blank=True,
    )

    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(
                fields=["patient", "-uploaded_at"],
                name="document_patient_date_idx",
            ),
            models.Index(
                fields=["patient", "document_type"],
                name="document_patient_type_idx",
            ),
            models.Index(
                fields=["visibility"],
                name="document_visibility_idx",
            ),
        ]

    def __str__(self):
        return f"{self.patient.email} - {self.title}"
