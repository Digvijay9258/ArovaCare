from django.contrib import admin

from .models import (
    DoctorEarning,
    Payment,
    Settlement,
)

# ============================================================
# PAYMENT ADMIN
# ============================================================


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient",
        "doctor",
        "appointment",
        "amount",
        "currency",
        "platform_fee",
        "doctor_amount",
        "gateway",
        "status",
        "paid_at",
        "created_at",
    )

    list_filter = (
        "status",
        "gateway",
        "currency",
        "created_at",
        "paid_at",
    )

    search_fields = (
        "patient__email",
        "doctor__email",
        "gateway_order_id",
        "gateway_payment_id",
        "failure_reason",
    )

    readonly_fields = (
        "id",
        "patient",
        "doctor",
        "appointment",
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
    )

    ordering = ("-created_at",)

    list_per_page = 25


# ============================================================
# DOCTOR EARNING ADMIN
# ============================================================


@admin.register(DoctorEarning)
class DoctorEarningAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "doctor",
        "payment",
        "gross_amount",
        "platform_fee",
        "net_amount",
        "status",
        "available_at",
        "settled_at",
        "created_at",
    )

    list_filter = (
        "status",
        "available_at",
        "settled_at",
        "created_at",
    )

    search_fields = (
        "doctor__email",
        "payment__gateway_order_id",
        "payment__gateway_payment_id",
    )

    readonly_fields = (
        "id",
        "doctor",
        "payment",
        "gross_amount",
        "platform_fee",
        "net_amount",
        "status",
        "available_at",
        "settled_at",
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)

    list_per_page = 25


# ============================================================
# SETTLEMENT ADMIN
# ============================================================


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "doctor",
        "earning",
        "amount",
        "status",
        "payout_reference",
        "processed_at",
        "created_at",
    )

    list_filter = (
        "status",
        "processed_at",
        "created_at",
    )

    search_fields = (
        "doctor__email",
        "payout_reference",
        "earning__payment__gateway_order_id",
        "earning__payment__gateway_payment_id",
    )

    readonly_fields = (
        "id",
        "doctor",
        "earning",
        "amount",
        "status",
        "payout_reference",
        "failure_reason",
        "processed_at",
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)

    list_per_page = 25
