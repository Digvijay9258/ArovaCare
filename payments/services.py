from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from audit_logs.models import AuditLog
from audit_logs.services import create_audit_log

from .gateways import RazorpayGateway
from .models import DoctorEarning, Payment

DEFAULT_PLATFORM_FEE_PERCENT = Decimal("10.00")


def calculate_platform_fee(
    amount,
    fee_percent=DEFAULT_PLATFORM_FEE_PERCENT,
):
    amount = Decimal(str(amount))
    fee_percent = Decimal(str(fee_percent))

    fee = (amount * fee_percent / Decimal("100")).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    return fee


def calculate_doctor_amount(
    amount,
    platform_fee,
):
    amount = Decimal(str(amount))
    platform_fee = Decimal(str(platform_fee))

    doctor_amount = (amount - platform_fee).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    return doctor_amount


@transaction.atomic
def create_payment(
    *,
    patient,
    appointment,
    amount,
    gateway=Payment.Gateway.MANUAL,
    currency="INR",
    fee_percent=DEFAULT_PLATFORM_FEE_PERCENT,
    actor=None,
):
    amount = Decimal(str(amount))

    if amount <= Decimal("0.00"):
        raise ValueError("Payment amount must be greater than zero.")

    if appointment.patient_id != patient.id:
        raise ValueError("The appointment does not belong to this patient.")

    existing_payment = Payment.objects.filter(appointment=appointment).first()

    if existing_payment:
        raise ValueError("A payment already exists for this appointment.")

    platform_fee = calculate_platform_fee(
        amount=amount,
        fee_percent=fee_percent,
    )

    doctor_amount = calculate_doctor_amount(
        amount=amount,
        platform_fee=platform_fee,
    )

    payment = Payment.objects.create(
        patient=appointment.patient,
        doctor=appointment.doctor,
        appointment=appointment,
        amount=amount,
        currency=currency,
        platform_fee=platform_fee,
        doctor_amount=doctor_amount,
        gateway=gateway,
        status=Payment.Status.PENDING,
    )

    if actor:
        create_audit_log(
            user=actor,
            action=AuditLog.Action.CREATE,
            resource_type="Payment",
            resource_id=payment.id,
            metadata={
                "appointment_id": appointment.id,
                "amount": str(amount),
                "currency": currency,
                "platform_fee": str(platform_fee),
                "doctor_amount": str(doctor_amount),
                "gateway": gateway,
                "status": Payment.Status.PENDING,
            },
        )

    return payment


@transaction.atomic
def create_razorpay_order(
    *,
    payment,
    actor=None,
):
    if payment.gateway != Payment.Gateway.RAZORPAY:
        raise ValueError("This payment is not configured for Razorpay.")

    if payment.status != Payment.Status.PENDING:
        raise ValueError("Only pending payments can create a Razorpay order.")

    # Idempotency:
    # If an order already exists, return the existing payment.
    if payment.gateway_order_id:
        return payment

    gateway = RazorpayGateway()

    order = gateway.create_order(
        amount=payment.amount,
        currency=payment.currency,
        receipt=f"arova_payment_{payment.id}",
        notes={
            "payment_id": str(payment.id),
            "appointment_id": str(payment.appointment_id),
            "patient_id": str(payment.patient_id),
            "doctor_id": str(payment.doctor_id),
        },
    )

    gateway_order_id = order.get("id")

    if not gateway_order_id:
        raise ValueError("Razorpay did not return an order ID.")

    payment.gateway_order_id = gateway_order_id

    payment.save(
        update_fields=[
            "gateway_order_id",
            "updated_at",
        ]
    )

    if actor:
        create_audit_log(
            user=actor,
            action=AuditLog.Action.UPDATE,
            resource_type="Payment",
            resource_id=payment.id,
            metadata={
                "event": "RAZORPAY_ORDER_CREATED",
                "gateway_order_id": gateway_order_id,
                "amount": str(payment.amount),
                "currency": payment.currency,
            },
        )

    return payment


@transaction.atomic
def mark_payment_success(
    *,
    payment,
    gateway_payment_id,
    gateway_order_id=None,
    actor=None,
):
    """
    Mark a payment as successful after the gateway
    has already been trusted/verified.

    IMPORTANT:
    This function does not verify Razorpay signatures.

    Signature verification must happen before calling
    this function.

    Checkout flow:
        verify_razorpay_payment()

    Webhook flow:
        verify_razorpay_webhook_payment()
    """

    # --------------------------------------------------------
    # Idempotency
    # --------------------------------------------------------

    if payment.status == Payment.Status.SUCCESS:

        earning = DoctorEarning.objects.filter(payment=payment).first()

        return payment, earning

    # --------------------------------------------------------
    # Invalid state protection
    # --------------------------------------------------------

    if payment.status in [
        Payment.Status.REFUNDED,
        Payment.Status.CANCELLED,
    ]:
        raise ValueError("This payment cannot be marked as successful.")

    # --------------------------------------------------------
    # Gateway order verification
    # --------------------------------------------------------

    if (
        payment.gateway_order_id
        and gateway_order_id
        and payment.gateway_order_id != gateway_order_id
    ):
        raise ValueError("Gateway order ID does not match this payment.")

    if not gateway_payment_id:
        raise ValueError("Gateway payment ID is required.")

    # --------------------------------------------------------
    # Update payment
    # --------------------------------------------------------

    payment.gateway_payment_id = gateway_payment_id

    if gateway_order_id:
        payment.gateway_order_id = gateway_order_id

    payment.status = Payment.Status.SUCCESS
    payment.paid_at = timezone.now()

    payment.save(
        update_fields=[
            "gateway_payment_id",
            "gateway_order_id",
            "status",
            "paid_at",
            "updated_at",
        ]
    )

    # --------------------------------------------------------
    # Create doctor earning
    # --------------------------------------------------------

    earning, created = DoctorEarning.objects.get_or_create(
        payment=payment,
        defaults={
            "doctor": payment.doctor,
            "gross_amount": payment.amount,
            "platform_fee": payment.platform_fee,
            "net_amount": payment.doctor_amount,
            "status": (DoctorEarning.Status.AVAILABLE),
            "available_at": timezone.now(),
        },
    )

    # --------------------------------------------------------
    # Keep earning consistent
    # --------------------------------------------------------

    if not created:

        earning.doctor = payment.doctor
        earning.gross_amount = payment.amount
        earning.platform_fee = payment.platform_fee
        earning.net_amount = payment.doctor_amount

        if earning.status == DoctorEarning.Status.PENDING:
            earning.status = DoctorEarning.Status.AVAILABLE

        if earning.available_at is None:
            earning.available_at = timezone.now()

        earning.save(
            update_fields=[
                "doctor",
                "gross_amount",
                "platform_fee",
                "net_amount",
                "status",
                "available_at",
                "updated_at",
            ]
        )

    # --------------------------------------------------------
    # Audit
    # --------------------------------------------------------

    if actor:
        create_audit_log(
            user=actor,
            action=AuditLog.Action.UPDATE,
            resource_type="Payment",
            resource_id=payment.id,
            metadata={
                "event": "PAYMENT_SUCCESS",
                "gateway": payment.gateway,
                "gateway_order_id": (payment.gateway_order_id),
                "gateway_payment_id": (payment.gateway_payment_id),
                "amount": str(payment.amount),
                "currency": payment.currency,
                "doctor_earning_id": earning.id,
                "earning_created": created,
            },
        )

    return payment, earning


@transaction.atomic
def verify_razorpay_payment(
    *,
    payment,
    razorpay_order_id,
    razorpay_payment_id,
    razorpay_signature,
    actor=None,
):
    """
    Verify a Razorpay Checkout payment.

    This function is ONLY for the client-side
    Razorpay Checkout response.

    It must NOT be used for webhook verification.
    """

    if payment.gateway != Payment.Gateway.RAZORPAY:
        raise ValueError("This payment is not configured for Razorpay.")

    if payment.status in [
        Payment.Status.REFUNDED,
        Payment.Status.CANCELLED,
    ]:
        raise ValueError("This payment cannot be verified.")

    if not payment.gateway_order_id or payment.gateway_order_id != razorpay_order_id:
        raise ValueError("Razorpay order ID does not match this payment.")

    if not razorpay_payment_id:
        raise ValueError("Razorpay payment ID is required.")

    if not razorpay_signature:
        raise ValueError("Razorpay payment signature is required.")

    gateway = RazorpayGateway()

    # --------------------------------------------------------
    # Checkout signature verification
    # --------------------------------------------------------

    gateway.verify_payment_signature(
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_signature=razorpay_signature,
    )

    return mark_payment_success(
        payment=payment,
        gateway_payment_id=razorpay_payment_id,
        gateway_order_id=razorpay_order_id,
        actor=actor,
    )


@transaction.atomic
def verify_razorpay_webhook_payment(
    *,
    payment,
    razorpay_order_id,
    razorpay_payment_id,
    actor=None,
):
    """
    Process a successful Razorpay webhook payment.

    IMPORTANT:

    The webhook signature MUST already have been verified
    using RazorpayGateway.verify_webhook_signature()
    before this function is called.

    This function deliberately does NOT call
    verify_payment_signature(), because a Razorpay webhook
    signature is different from a Checkout payment signature.
    """

    if payment.gateway != Payment.Gateway.RAZORPAY:
        raise ValueError("This payment is not configured for Razorpay.")

    if payment.status in [
        Payment.Status.REFUNDED,
        Payment.Status.CANCELLED,
    ]:
        raise ValueError("This payment cannot be marked as successful.")

    if not payment.gateway_order_id or payment.gateway_order_id != razorpay_order_id:
        raise ValueError("Razorpay order ID does not match this payment.")

    if not razorpay_payment_id:
        raise ValueError("Razorpay payment ID is required.")

    return mark_payment_success(
        payment=payment,
        gateway_payment_id=razorpay_payment_id,
        gateway_order_id=razorpay_order_id,
        actor=actor,
    )


@transaction.atomic
def mark_payment_failed(
    *,
    payment,
    failure_reason=None,
    actor=None,
):
    if payment.status in [
        Payment.Status.SUCCESS,
        Payment.Status.REFUNDED,
    ]:
        raise ValueError("A successful or refunded payment cannot be marked as failed.")

    payment.status = Payment.Status.FAILED

    payment.failure_reason = failure_reason or "Payment failed."

    payment.save(
        update_fields=[
            "status",
            "failure_reason",
            "updated_at",
        ]
    )

    if actor:
        create_audit_log(
            user=actor,
            action=AuditLog.Action.UPDATE,
            resource_type="Payment",
            resource_id=payment.id,
            metadata={
                "event": "PAYMENT_FAILED",
                "failure_reason": (payment.failure_reason),
            },
        )

    return payment


@transaction.atomic
def refund_payment(
    *,
    payment,
    actor=None,
):
    if payment.status != Payment.Status.SUCCESS:
        raise ValueError("Only successful payments can be refunded.")

    payment.status = Payment.Status.REFUNDED

    payment.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    earning = DoctorEarning.objects.filter(payment=payment).first()

    if earning:
        earning.status = DoctorEarning.Status.REVERSED

        earning.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

    if actor:
        create_audit_log(
            user=actor,
            action=AuditLog.Action.UPDATE,
            resource_type="Payment",
            resource_id=payment.id,
            metadata={
                "event": "PAYMENT_REFUNDED",
                "doctor_earning_id": (earning.id if earning else None),
            },
        )

    return payment
