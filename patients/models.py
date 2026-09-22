from django.conf import settings
from django.db import models


class PatientProfile(models.Model):

    GENDER_CHOICES = [
        ("MALE", "Male"),
        ("FEMALE", "Female"),
        ("OTHER", "Other"),
    ]

    BLOOD_GROUP_CHOICES = [
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
        ("O+", "O+"),
        ("O-", "O-"),
        ("UNKNOWN", "Unknown"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_profile",
    )

    full_name = models.CharField(max_length=150)

    date_of_birth = models.DateField(null=True, blank=True)

    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)

    phone = models.CharField(max_length=20, blank=True)

    blood_group = models.CharField(
        max_length=10, choices=BLOOD_GROUP_CHOICES, default="UNKNOWN"
    )

    address = models.TextField(blank=True)

    emergency_contact_name = models.CharField(max_length=150, blank=True)

    emergency_contact_phone = models.CharField(max_length=20, blank=True)

    profile_photo = models.ImageField(
        upload_to="patients/profile/", blank=True, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name
