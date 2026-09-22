from django.urls import path

from .views import (
    AdminSettlementListView,
    AdminSettlementStatusView,
    DoctorEarningDetailView,
    DoctorEarningListView,
    DoctorPaymentListView,
    DoctorSettlementDetailView,
    DoctorSettlementListCreateView,
    PatientPaymentDetailView,
    PatientPaymentListCreateView,
    RazorpayOrderCreateView,
    RazorpayPaymentVerifyView,
    RazorpayWebhookView,
)

urlpatterns = [
    # ========================================================
    # PATIENT PAYMENTS
    # ========================================================
    path(
        "",
        PatientPaymentListCreateView.as_view(),
        name="patient-payment-list-create",
    ),
    path(
        "<int:pk>/",
        PatientPaymentDetailView.as_view(),
        name="patient-payment-detail",
    ),
    # ========================================================
    # RAZORPAY
    # ========================================================
    path(
        "razorpay/order/",
        RazorpayOrderCreateView.as_view(),
        name="razorpay-order-create",
    ),
    path(
        "razorpay/verify/",
        RazorpayPaymentVerifyView.as_view(),
        name="razorpay-payment-verify",
    ),
    path(
        "razorpay/webhook/",
        RazorpayWebhookView.as_view(),
        name="razorpay-webhook",
    ),
    # ========================================================
    # DOCTOR PAYMENTS
    # ========================================================
    path(
        "doctor/",
        DoctorPaymentListView.as_view(),
        name="doctor-payment-list",
    ),
    # ========================================================
    # DOCTOR EARNINGS
    # ========================================================
    path(
        "earnings/",
        DoctorEarningListView.as_view(),
        name="doctor-earning-list",
    ),
    path(
        "earnings/<int:pk>/",
        DoctorEarningDetailView.as_view(),
        name="doctor-earning-detail",
    ),
    # ========================================================
    # DOCTOR SETTLEMENTS
    # ========================================================
    path(
        "settlements/",
        DoctorSettlementListCreateView.as_view(),
        name="doctor-settlement-list-create",
    ),
    path(
        "settlements/<int:pk>/",
        DoctorSettlementDetailView.as_view(),
        name="doctor-settlement-detail",
    ),
    # ========================================================
    # ADMIN SETTLEMENTS
    # ========================================================
    path(
        "admin/settlements/",
        AdminSettlementListView.as_view(),
        name="admin-settlement-list",
    ),
    path(
        "admin/settlements/<int:pk>/status/",
        AdminSettlementStatusView.as_view(),
        name="admin-settlement-status",
    ),
]
