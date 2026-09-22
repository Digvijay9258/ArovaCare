from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Payment(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"
        CANCELLED = "CANCELLED", "Cancelled"

    class Gateway(models.TextChoices):
        RAZORPAY = "RAZORPAY", "Razorpay"
        STRIPE = "STRIPE", "Stripe"
        MANUAL = "MANUAL", "Manual"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments_made",
    )

    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_payments",
    )

    appointment = models.OneToOneField(
        "appointments.Appointment",
        on_delete=models.PROTECT,
        related_name="payment",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    currency = models.CharField(
        max_length=10,
        default="INR",
    )

    platform_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    doctor_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    gateway = models.CharField(
        max_length=20,
        choices=Gateway.choices,
        default=Gateway.MANUAL,
    )

    gateway_order_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )

    gateway_payment_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    failure_reason = models.TextField(
        blank=True,
        null=True,
    )

    paid_at = models.DateTimeField(
        blank=True,
        null=True,
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
            models.Index(fields=["patient", "-created_at"]),
            models.Index(fields=["doctor", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self):
        return (
            f"Payment #{self.id} - "
            f"{self.patient.email} - "
            f"{self.amount} {self.currency}"
        )


class DoctorEarning(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        AVAILABLE = "AVAILABLE", "Available"
        SETTLED = "SETTLED", "Settled"
        REVERSED = "REVERSED", "Reversed"

    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="earnings",
    )

    payment = models.OneToOneField(
        Payment,
        on_delete=models.PROTECT,
        related_name="doctor_earning",
    )

    gross_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    platform_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    available_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    settled_at = models.DateTimeField(
        blank=True,
        null=True,
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
            models.Index(fields=["doctor", "status"]),
            models.Index(fields=["doctor", "-created_at"]),
        ]

    def __str__(self):
        return f"Earning #{self.id} - " f"{self.doctor.email} - " f"{self.net_amount}"


class Settlement(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="settlements",
    )

    earning = models.ForeignKey(
        DoctorEarning,
        on_delete=models.PROTECT,
        related_name="settlements",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    payout_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    failure_reason = models.TextField(
        blank=True,
        null=True,
    )

    processed_at = models.DateTimeField(
        blank=True,
        null=True,
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
            models.Index(fields=["doctor", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self):
        return f"Settlement #{self.id} - " f"{self.doctor.email} - " f"{self.amount}"
