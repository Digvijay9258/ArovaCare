from decimal import Decimal

from rest_framework import serializers

from appointments.models import Appointment

from .models import DoctorEarning, Payment, Settlement


class PaymentSerializer(serializers.ModelSerializer):
    patient_email = serializers.EmailField(
        source="patient.email",
        read_only=True,
    )

    doctor_email = serializers.EmailField(
        source="doctor.email",
        read_only=True,
    )

    appointment_date = serializers.DateField(
        source="appointment.appointment_date",
        read_only=True,
    )

    appointment_time = serializers.TimeField(
        source="appointment.appointment_time",
        read_only=True,
    )

    class Meta:
        model = Payment

        fields = [
            "id",
            "patient",
            "patient_email",
            "doctor",
            "doctor_email",
            "appointment",
            "appointment_date",
            "appointment_time",
            "amount",
            "currency",
            "platform_fee",
            "doctor_amount",
            "gateway",
            "gateway_order_id",
            "gateway_payment_id",
            "status",
            "failure_reason",
            "paid_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "patient",
            "patient_email",
            "doctor",
            "doctor_email",
            "appointment_date",
            "appointment_time",
            "platform_fee",
            "doctor_amount",
            "gateway_order_id",
            "gateway_payment_id",
            "status",
            "failure_reason",
            "paid_at",
            "created_at",
            "updated_at",
        ]


class PaymentCreateSerializer(serializers.Serializer):
    appointment = serializers.PrimaryKeyRelatedField(queryset=Appointment.objects.all())

    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )

    currency = serializers.CharField(
        max_length=10,
        default="INR",
    )

    gateway = serializers.ChoiceField(
        choices=[
            (
                Payment.Gateway.MANUAL,
                "Manual",
            ),
            (
                Payment.Gateway.RAZORPAY,
                "Razorpay",
            ),
        ],
        default=Payment.Gateway.MANUAL,
    )

    def validate_currency(self, value):
        value = value.upper()

        if value != "INR":
            raise serializers.ValidationError(
                "Only INR currency is currently supported."
            )

        return value

    def validate_gateway(self, value):
        if value not in [
            Payment.Gateway.MANUAL,
            Payment.Gateway.RAZORPAY,
        ]:
            raise serializers.ValidationError(
                "This payment gateway is not currently supported."
            )

        return value

    def validate_appointment(self, appointment):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")

        if appointment.patient_id != request.user.id:
            raise serializers.ValidationError(
                "You can only create payments for your own appointments."
            )

        if appointment.status not in [
            "ACCEPTED",
            "COMPLETED",
        ]:
            raise serializers.ValidationError(
                "Payment can only be created for an accepted or completed appointment."
            )

        if hasattr(appointment, "payment"):
            raise serializers.ValidationError(
                "A payment already exists for this appointment."
            )

        return appointment


class RazorpayOrderCreateSerializer(serializers.Serializer):
    appointment = serializers.PrimaryKeyRelatedField(queryset=Appointment.objects.all())

    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )

    currency = serializers.CharField(
        max_length=10,
        default="INR",
    )

    def validate_currency(self, value):
        value = value.upper()

        if value != "INR":
            raise serializers.ValidationError(
                "Razorpay payments currently support INR only."
            )

        return value

    def validate_appointment(self, appointment):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")

        if appointment.patient_id != request.user.id:
            raise serializers.ValidationError(
                "You can only pay for your own appointments."
            )

        if appointment.status not in [
            "ACCEPTED",
            "COMPLETED",
        ]:
            raise serializers.ValidationError(
                "Razorpay payment can only be created for an accepted or completed appointment."
            )

        if hasattr(appointment, "payment"):
            raise serializers.ValidationError(
                "A payment already exists for this appointment."
            )

        return appointment


class RazorpayPaymentVerifySerializer(serializers.Serializer):
    payment_id = serializers.IntegerField(min_value=1)

    razorpay_order_id = serializers.CharField(
        max_length=255,
        trim_whitespace=True,
    )

    razorpay_payment_id = serializers.CharField(
        max_length=255,
        trim_whitespace=True,
    )

    razorpay_signature = serializers.CharField(
        max_length=512,
        trim_whitespace=True,
    )


class DoctorEarningSerializer(serializers.ModelSerializer):
    doctor_email = serializers.EmailField(
        source="doctor.email",
        read_only=True,
    )

    payment_id = serializers.IntegerField(
        source="payment.id",
        read_only=True,
    )

    appointment_id = serializers.IntegerField(
        source="payment.appointment.id",
        read_only=True,
    )

    class Meta:
        model = DoctorEarning

        fields = [
            "id",
            "doctor",
            "doctor_email",
            "payment_id",
            "appointment_id",
            "gross_amount",
            "platform_fee",
            "net_amount",
            "status",
            "available_at",
            "settled_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields


class SettlementSerializer(serializers.ModelSerializer):
    doctor_email = serializers.EmailField(
        source="doctor.email",
        read_only=True,
    )

    earning_id = serializers.IntegerField(
        source="earning.id",
        read_only=True,
    )

    class Meta:
        model = Settlement

        fields = [
            "id",
            "doctor",
            "doctor_email",
            "earning",
            "earning_id",
            "amount",
            "payout_reference",
            "status",
            "failure_reason",
            "processed_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "doctor",
            "doctor_email",
            "earning_id",
            "status",
            "failure_reason",
            "processed_at",
            "created_at",
            "updated_at",
        ]


class SettlementCreateSerializer(serializers.Serializer):
    earning = serializers.PrimaryKeyRelatedField(queryset=DoctorEarning.objects.all())

    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )

    def validate_earning(self, earning):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")

        if earning.doctor_id != request.user.id:
            raise serializers.ValidationError(
                "You can only request settlement for your own earnings."
            )

        if earning.status != (DoctorEarning.Status.AVAILABLE):
            raise serializers.ValidationError("Only available earnings can be settled.")

        return earning

    def validate(self, attrs):
        earning = attrs["earning"]
        amount = attrs["amount"]

        # ----------------------------------------------------
        # Calculate already requested/settled amount
        # ----------------------------------------------------

        existing_amount = Settlement.objects.filter(
            earning=earning,
            status__in=[
                Settlement.Status.PENDING,
                Settlement.Status.PROCESSING,
                Settlement.Status.COMPLETED,
            ],
        ).values_list("amount", flat=True)

        already_allocated = sum(
            existing_amount,
            Decimal("0.00"),
        )

        remaining_amount = earning.net_amount - already_allocated

        if remaining_amount <= Decimal("0.00"):
            raise serializers.ValidationError(
                {
                    "earning": (
                        "No settlement amount remains " "available for this earning."
                    )
                }
            )

        if amount > remaining_amount:
            raise serializers.ValidationError(
                {
                    "amount": (
                        "Settlement amount cannot exceed "
                        "the remaining available earning "
                        f"of {remaining_amount}."
                    )
                }
            )

        return attrs
