import json
from decimal import Decimal

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import (
    IsAdminUserRole,
    IsDoctor,
    IsPatient,
)

from .gateways import RazorpayGateway
from .models import (
    DoctorEarning,
    Payment,
    Settlement,
)
from .serializers import (
    DoctorEarningSerializer,
    PaymentCreateSerializer,
    PaymentSerializer,
    RazorpayOrderCreateSerializer,
    RazorpayPaymentVerifySerializer,
    SettlementCreateSerializer,
    SettlementSerializer,
)
from .services import (
    create_payment,
    create_razorpay_order,
    mark_payment_failed,
    verify_razorpay_payment,
    verify_razorpay_webhook_payment,
)

# ============================================================
# PATIENT PAYMENT
# ============================================================


class PatientPaymentListCreateView(generics.ListCreateAPIView):
    permission_classes = [
        IsAuthenticated,
        IsPatient,
    ]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PaymentCreateSerializer

        return PaymentSerializer

    def get_queryset(self):
        return (
            Payment.objects.filter(patient=self.request.user)
            .select_related(
                "patient",
                "doctor",
                "appointment",
            )
            .order_by("-created_at")
        )

    def create(
        self,
        request,
        *args,
        **kwargs,
    ):
        serializer = self.get_serializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(raise_exception=True)

        try:
            payment = create_payment(
                patient=request.user,
                appointment=(serializer.validated_data["appointment"]),
                amount=(serializer.validated_data["amount"]),
                gateway=(
                    serializer.validated_data.get(
                        "gateway",
                        Payment.Gateway.MANUAL,
                    )
                ),
                currency=(
                    serializer.validated_data.get(
                        "currency",
                        "INR",
                    )
                ),
                actor=request.user,
            )

        except ValueError as exc:
            return Response(
                {
                    "error": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = PaymentSerializer(
            payment,
            context={
                "request": request,
            },
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class PatientPaymentDetailView(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer

    permission_classes = [
        IsAuthenticated,
        IsPatient,
    ]

    def get_queryset(self):
        return Payment.objects.filter(patient=self.request.user).select_related(
            "patient",
            "doctor",
            "appointment",
        )


# ============================================================
# RAZORPAY ORDER CREATION
# ============================================================


class RazorpayOrderCreateView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsPatient,
    ]

    @transaction.atomic
    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        serializer = RazorpayOrderCreateSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(raise_exception=True)

        appointment = serializer.validated_data["appointment"]

        amount = serializer.validated_data["amount"]

        currency = serializer.validated_data.get(
            "currency",
            "INR",
        )

        try:
            payment = create_payment(
                patient=request.user,
                appointment=appointment,
                amount=amount,
                gateway=Payment.Gateway.RAZORPAY,
                currency=currency,
                actor=request.user,
            )

            payment = create_razorpay_order(
                payment=payment,
                actor=request.user,
            )

        except ValueError as exc:
            return Response(
                {
                    "error": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": ("Razorpay order created successfully."),
                "payment": PaymentSerializer(
                    payment,
                    context={
                        "request": request,
                    },
                ).data,
                "razorpay": {
                    "key_id": (settings.RAZORPAY_KEY_ID),
                    "order_id": (payment.gateway_order_id),
                    "amount": int(payment.amount * 100),
                    "currency": payment.currency,
                },
            },
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# RAZORPAY PAYMENT VERIFICATION
# ============================================================


class RazorpayPaymentVerifyView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsPatient,
    ]

    @transaction.atomic
    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        serializer = RazorpayPaymentVerifySerializer(
            data=request.data,
        )

        serializer.is_valid(raise_exception=True)

        payment_id = serializer.validated_data["payment_id"]

        try:
            payment = (
                Payment.objects.select_for_update()
                .select_related(
                    "patient",
                    "doctor",
                    "appointment",
                )
                .get(
                    id=payment_id,
                    patient=request.user,
                )
            )

        except Payment.DoesNotExist:
            return Response(
                {
                    "error": "Payment not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            payment, earning = verify_razorpay_payment(
                payment=payment,
                razorpay_order_id=(serializer.validated_data["razorpay_order_id"]),
                razorpay_payment_id=(serializer.validated_data["razorpay_payment_id"]),
                razorpay_signature=(serializer.validated_data["razorpay_signature"]),
                actor=request.user,
            )

        except ValueError as exc:
            return Response(
                {
                    "error": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            return Response(
                {
                    "error": ("Razorpay payment verification failed."),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": ("Payment verified successfully."),
                "payment": PaymentSerializer(
                    payment,
                    context={
                        "request": request,
                    },
                ).data,
                "earning": DoctorEarningSerializer(
                    earning,
                    context={
                        "request": request,
                    },
                ).data,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# RAZORPAY WEBHOOK
# ============================================================


class RazorpayWebhookView(APIView):
    """
    Razorpay server-to-server webhook.

    This endpoint does not use JWT authentication.

    Security is provided by Razorpay webhook signature
    verification.

    IMPORTANT:

    Razorpay webhook signatures are different from
    Razorpay Checkout payment signatures.

    The webhook signature is verified against the raw
    request body using RAZORPAY_WEBHOOK_SECRET.

    After that verification succeeds, the webhook-specific
    payment service processes the payment.

    We must NOT call verify_razorpay_payment() here because
    that method is specifically for Razorpay Checkout
    payment signatures.
    """

    permission_classes = [
        AllowAny,
    ]

    authentication_classes = []

    @transaction.atomic
    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        # ----------------------------------------------------
        # 1. Get webhook signature
        # ----------------------------------------------------

        signature = request.headers.get("X-Razorpay-Signature")

        if not signature:
            return Response(
                {"error": ("Missing Razorpay webhook signature.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # 2. Verify webhook signature
        # ----------------------------------------------------

        try:
            gateway = RazorpayGateway()

            gateway.verify_webhook_signature(
                payload=request.body,
                signature=signature,
            )

        except Exception:
            return Response(
                {"error": ("Invalid webhook signature.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # 3. Parse JSON payload
        # ----------------------------------------------------

        try:
            payload = json.loads(request.body.decode("utf-8"))

        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
        ):
            return Response(
                {"error": ("Invalid webhook payload.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # 4. Extract event
        # ----------------------------------------------------

        event = payload.get("event")

        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})

        razorpay_payment_id = payment_entity.get("id")

        razorpay_order_id = payment_entity.get("order_id")

        # ----------------------------------------------------
        # 5. Validate event
        # ----------------------------------------------------

        supported_events = [
            "payment.captured",
            "order.paid",
            "payment.failed",
        ]

        if event not in supported_events:
            return Response(
                {
                    "message": (
                        "Webhook received. " "Event does not require processing."
                    ),
                    "event": event,
                },
                status=status.HTTP_200_OK,
            )

        # ----------------------------------------------------
        # 6. Order ID is required for payment matching
        # ----------------------------------------------------

        if not razorpay_order_id:
            return Response(
                {"message": ("Webhook received without " "Razorpay order ID.")},
                status=status.HTTP_200_OK,
            )

        # ----------------------------------------------------
        # 7. Find local payment
        # ----------------------------------------------------

        try:
            payment = (
                Payment.objects.select_for_update()
                .select_related(
                    "patient",
                    "doctor",
                    "appointment",
                )
                .get(
                    gateway=Payment.Gateway.RAZORPAY,
                    gateway_order_id=(razorpay_order_id),
                )
            )

        except Payment.DoesNotExist:
            # Return 200 so Razorpay does not repeatedly
            # retry an unknown order.

            return Response(
                {"message": ("Payment not found. " "Webhook ignored.")},
                status=status.HTTP_200_OK,
            )

        # ----------------------------------------------------
        # 8. Successful payment
        # ----------------------------------------------------

        if event in [
            "payment.captured",
            "order.paid",
        ]:
            # A successful payment is idempotent.
            # Duplicate Razorpay webhooks will not create
            # another DoctorEarning.

            if payment.status == Payment.Status.SUCCESS:
                return Response(
                    {"message": ("Payment already processed.")},
                    status=status.HTTP_200_OK,
                )

            if not razorpay_payment_id:
                return Response(
                    {"error": ("Razorpay payment ID is missing.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                # IMPORTANT:
                #
                # The webhook signature has already been
                # verified above using the raw request body.
                #
                # Therefore we use the dedicated webhook
                # payment service here.
                #
                # We DO NOT call verify_razorpay_payment()
                # because that method expects the Checkout
                # payment signature.

                payment, earning = verify_razorpay_webhook_payment(
                    payment=payment,
                    razorpay_order_id=(razorpay_order_id),
                    razorpay_payment_id=(razorpay_payment_id),
                    actor=None,
                )

            except ValueError as exc:
                return Response(
                    {
                        "error": str(exc),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            except Exception:
                return Response(
                    {"error": ("Payment processing failed.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # ----------------------------------------------------
        # 9. Failed payment
        # ----------------------------------------------------

        elif event == "payment.failed":
            # Never change an already successful payment
            # back to FAILED.

            if payment.status == Payment.Status.SUCCESS:
                return Response(
                    {"message": ("Payment already successful.")},
                    status=status.HTTP_200_OK,
                )

            failure_reason = (
                payment_entity.get("error_description")
                or payment_entity.get("error_reason")
                or "Razorpay payment failed."
            )

            try:
                mark_payment_failed(
                    payment=payment,
                    failure_reason=failure_reason,
                    actor=None,
                )

            except ValueError as exc:
                return Response(
                    {
                        "error": str(exc),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            except Exception:
                return Response(
                    {"error": ("Failed to update payment status.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            {
                "message": ("Webhook processed successfully."),
                "event": event,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# DOCTOR PAYMENTS
# ============================================================


class DoctorPaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer

    permission_classes = [
        IsAuthenticated,
        IsDoctor,
    ]

    def get_queryset(self):
        return (
            Payment.objects.filter(doctor=self.request.user)
            .select_related(
                "patient",
                "doctor",
                "appointment",
            )
            .order_by("-created_at")
        )


# ============================================================
# DOCTOR EARNINGS
# ============================================================


class DoctorEarningListView(generics.ListAPIView):
    serializer_class = DoctorEarningSerializer

    permission_classes = [
        IsAuthenticated,
        IsDoctor,
    ]

    def get_queryset(self):
        return (
            DoctorEarning.objects.filter(doctor=self.request.user)
            .select_related(
                "doctor",
                "payment",
                "payment__appointment",
            )
            .order_by("-created_at")
        )


class DoctorEarningDetailView(generics.RetrieveAPIView):
    serializer_class = DoctorEarningSerializer

    permission_classes = [
        IsAuthenticated,
        IsDoctor,
    ]

    def get_queryset(self):
        return DoctorEarning.objects.filter(doctor=self.request.user).select_related(
            "doctor",
            "payment",
            "payment__appointment",
        )


# ============================================================
# DOCTOR SETTLEMENTS
# ============================================================


class DoctorSettlementListCreateView(generics.ListCreateAPIView):
    permission_classes = [
        IsAuthenticated,
        IsDoctor,
    ]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SettlementCreateSerializer

        return SettlementSerializer

    def get_queryset(self):
        return (
            Settlement.objects.filter(doctor=self.request.user)
            .select_related(
                "doctor",
                "earning",
                "earning__payment",
            )
            .order_by("-created_at")
        )

    @transaction.atomic
    def create(
        self,
        request,
        *args,
        **kwargs,
    ):
        serializer = self.get_serializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(raise_exception=True)

        # ----------------------------------------------------
        # Get earning ID from validated data
        # ----------------------------------------------------

        earning_id = serializer.validated_data["earning"].id

        amount = serializer.validated_data["amount"]

        # ----------------------------------------------------
        # Lock earning row
        #
        # This protects against two simultaneous settlement
        # requests trying to use the same earning.
        # ----------------------------------------------------

        try:
            earning = DoctorEarning.objects.select_for_update().get(
                id=earning_id,
                doctor=request.user,
            )

        except DoctorEarning.DoesNotExist:
            return Response(
                {"error": ("Earning not found.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ----------------------------------------------------
        # Verify earning status again after locking
        # ----------------------------------------------------

        if earning.status != (DoctorEarning.Status.AVAILABLE):
            return Response(
                {"error": ("Only available earnings can " "be settled.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Calculate already allocated amount
        #
        # PENDING + PROCESSING + COMPLETED settlements
        # are considered allocated.
        # ----------------------------------------------------

        allocated_amount = Settlement.objects.filter(
            earning=earning,
            status__in=[
                Settlement.Status.PENDING,
                Settlement.Status.PROCESSING,
                Settlement.Status.COMPLETED,
            ],
        ).aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")

        remaining_amount = earning.net_amount - allocated_amount

        # ----------------------------------------------------
        # Prevent settlement when nothing remains
        # ----------------------------------------------------

        if remaining_amount <= Decimal("0.00"):
            return Response(
                {
                    "error": (
                        "No settlement amount remains " "available for this earning."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Prevent over-settlement
        # ----------------------------------------------------

        if amount > remaining_amount:
            return Response(
                {
                    "error": (
                        "Settlement amount cannot exceed "
                        "the remaining available earning "
                        f"of {remaining_amount}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Prevent duplicate active settlement
        # ----------------------------------------------------

        existing_settlement = Settlement.objects.filter(
            earning=earning,
            status__in=[
                Settlement.Status.PENDING,
                Settlement.Status.PROCESSING,
            ],
        ).first()

        if existing_settlement:
            return Response(
                {
                    "error": (
                        "A settlement is already pending "
                        "or being processed for this earning."
                    ),
                    "settlement_id": (existing_settlement.id),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Create settlement
        # ----------------------------------------------------

        settlement = Settlement.objects.create(
            doctor=request.user,
            earning=earning,
            amount=amount,
            status=Settlement.Status.PENDING,
        )

        # Earning stays AVAILABLE until admin
        # actually completes settlement.

        earning.status = DoctorEarning.Status.AVAILABLE

        earning.settled_at = None

        earning.save(
            update_fields=[
                "status",
                "settled_at",
                "updated_at",
            ]
        )

        response_serializer = SettlementSerializer(
            settlement,
            context={
                "request": request,
            },
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class DoctorSettlementDetailView(generics.RetrieveAPIView):
    serializer_class = SettlementSerializer

    permission_classes = [
        IsAuthenticated,
        IsDoctor,
    ]

    def get_queryset(self):
        return Settlement.objects.filter(doctor=self.request.user).select_related(
            "doctor",
            "earning",
            "earning__payment",
        )


# ============================================================
# ADMIN SETTLEMENTS
# ============================================================


class AdminSettlementListView(generics.ListAPIView):
    serializer_class = SettlementSerializer

    permission_classes = [
        IsAuthenticated,
        IsAdminUserRole,
    ]

    def get_queryset(self):
        queryset = Settlement.objects.select_related(
            "doctor",
            "earning",
            "earning__payment",
        ).order_by("-created_at")

        settlement_status = self.request.query_params.get("status")

        if settlement_status:
            queryset = queryset.filter(status=settlement_status)

        return queryset


class AdminSettlementStatusView(generics.UpdateAPIView):
    serializer_class = SettlementSerializer

    permission_classes = [
        IsAuthenticated,
        IsAdminUserRole,
    ]

    http_method_names = [
        "patch",
    ]

    def get_queryset(self):
        return Settlement.objects.select_related(
            "doctor",
            "earning",
            "earning__payment",
        )

    @transaction.atomic
    def partial_update(
        self,
        request,
        *args,
        **kwargs,
    ):
        settlement = self.get_object()

        new_status = request.data.get("status")

        allowed_statuses = [
            Settlement.Status.PROCESSING,
            Settlement.Status.COMPLETED,
            Settlement.Status.FAILED,
            Settlement.Status.CANCELLED,
        ]

        if new_status not in allowed_statuses:
            return Response(
                {
                    "error": (
                        "Invalid settlement status. "
                        "Use one of: "
                        "PROCESSING, COMPLETED, "
                        "FAILED, CANCELLED."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Final states cannot be modified
        # ----------------------------------------------------

        if settlement.status in [
            Settlement.Status.COMPLETED,
            Settlement.Status.CANCELLED,
        ]:
            return Response(
                {"error": ("This settlement can no longer " "be modified.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # PROCESSING
        # ----------------------------------------------------

        if new_status == (Settlement.Status.PROCESSING):
            if settlement.status != (Settlement.Status.PENDING):
                return Response(
                    {
                        "error": (
                            "Only PENDING settlements " "can be moved to PROCESSING."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            settlement.status = Settlement.Status.PROCESSING

        # ----------------------------------------------------
        # COMPLETED
        # ----------------------------------------------------

        elif new_status == (Settlement.Status.COMPLETED):
            if settlement.status not in [
                Settlement.Status.PENDING,
                Settlement.Status.PROCESSING,
            ]:
                return Response(
                    {
                        "error": (
                            "Only PENDING or PROCESSING "
                            "settlements can be completed."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            now = timezone.now()

            settlement.status = Settlement.Status.COMPLETED

            settlement.processed_at = now

            earning = settlement.earning

            earning.status = DoctorEarning.Status.SETTLED

            earning.settled_at = now

            earning.save(
                update_fields=[
                    "status",
                    "settled_at",
                    "updated_at",
                ]
            )

        # ----------------------------------------------------
        # FAILED
        # ----------------------------------------------------

        elif new_status == (Settlement.Status.FAILED):
            if settlement.status not in [
                Settlement.Status.PENDING,
                Settlement.Status.PROCESSING,
            ]:
                return Response(
                    {
                        "error": (
                            "Only PENDING or PROCESSING " "settlements can be failed."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            settlement.status = Settlement.Status.FAILED

            earning = settlement.earning

            earning.status = DoctorEarning.Status.AVAILABLE

            earning.settled_at = None

            earning.save(
                update_fields=[
                    "status",
                    "settled_at",
                    "updated_at",
                ]
            )

        # ----------------------------------------------------
        # CANCELLED
        # ----------------------------------------------------

        elif new_status == (Settlement.Status.CANCELLED):
            if settlement.status not in [
                Settlement.Status.PENDING,
                Settlement.Status.PROCESSING,
            ]:
                return Response(
                    {
                        "error": (
                            "Only PENDING or PROCESSING "
                            "settlements can be cancelled."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            settlement.status = Settlement.Status.CANCELLED

            earning = settlement.earning

            earning.status = DoctorEarning.Status.AVAILABLE

            earning.settled_at = None

            earning.save(
                update_fields=[
                    "status",
                    "settled_at",
                    "updated_at",
                ]
            )

        # ----------------------------------------------------
        # Save settlement
        # ----------------------------------------------------

        settlement.save(
            update_fields=[
                "status",
                "processed_at",
                "updated_at",
            ]
        )

        serializer = self.get_serializer(settlement)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
