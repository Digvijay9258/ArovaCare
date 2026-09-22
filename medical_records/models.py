from django.conf import settings
from django.db import models



class MedicalRecord(models.Model):

    RECORD_TYPES = [
        ("PRESCRIPTION", "Prescription"),
        ("LAB_REPORT", "Lab Report"),
        ("BLOOD_REPORT", "Blood Report"),
        ("XRAY", "X-Ray"),
        ("MRI", "MRI"),
        ("CT_SCAN", "CT Scan"),
        ("DISCHARGE_SUMMARY", "Discharge Summary"),
        ("MEDICAL_HISTORY", "Medical History"),
        ("OTHER", "Other"),
    ]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="medical_records",
    )

    title = models.CharField(max_length=255)

    record_type = models.CharField(max_length=50, choices=RECORD_TYPES)

    description = models.TextField(
        blank=True,
        null=True,
    )

    file = models.FileField(
        upload_to="medical_records/%Y/%m/",
        blank=True,
        null=True,
    )

    record_date = models.DateField(null=True, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.email} - {self.title}"
