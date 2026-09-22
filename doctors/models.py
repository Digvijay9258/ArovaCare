from django.conf import settings
from django.db import models


class DoctorProfile(models.Model):

    VERIFICATION_STATUS = [
        ("PENDING", "Pending"),
        ("VERIFIED", "Verified"),
        ("REJECTED", "Rejected"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_profile"
    )

    full_name = models.CharField(
        max_length=150
    )

    specialization = models.CharField(
        max_length=150
    )

    medical_registration_number = models.CharField(
        max_length=100,
        unique=True
    )

    qualification = models.CharField(
        max_length=200,
        blank=True
    )

    experience_years = models.PositiveIntegerField(
        default=0
    )

    hospital_or_clinic = models.CharField(
        max_length=200,
        blank=True
    )

    consultation_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    bio = models.TextField(
        blank=True
    )

    profile_photo = models.ImageField(
        upload_to="doctors/profile/",
        null=True,
        blank=True
    )

    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS,
        default="PENDING"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Dr. {self.full_name}"
    