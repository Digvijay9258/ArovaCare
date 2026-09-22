from django.contrib import admin

from .models import (
    EmergencyAccess,
    MFASetting,
    SecurityAlert,
    SecuritySession,
)


@admin.register(SecuritySession)
class SecuritySessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "device_name",
        "ip_address",
        "is_active",
        "last_activity",
        "created_at",
        "logged_out_at",
    )

    list_filter = (
        "is_active",
        "created_at",
        "logged_out_at",
    )

    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "device_name",
        "ip_address",
        "session_token_id",
    )

    readonly_fields = (
        "session_token_id",
        "created_at",
        "last_activity",
        "logged_out_at",
    )

    ordering = ("-created_at",)


@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "alert_type",
        "title",
        "severity",
        "is_read",
        "created_at",
    )

    list_filter = (
        "alert_type",
        "severity",
        "is_read",
        "created_at",
    )

    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "title",
        "message",
    )

    readonly_fields = ("created_at",)

    ordering = ("-created_at",)


@admin.register(MFASetting)
class MFASettingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "method",
        "is_enabled",
        "enabled_at",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "is_enabled",
        "method",
        "enabled_at",
    )

    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
    )

    readonly_fields = (
        "secret_key",
        "enabled_at",
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)


@admin.register(EmergencyAccess)
class EmergencyAccessAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "doctor",
        "patient",
        "scope",
        "status",
        "requested_at",
        "expires_at",
        "access_count",
        "last_accessed_at",
    )

    list_filter = (
        "scope",
        "status",
        "requested_at",
        "expires_at",
    )

    search_fields = (
        "doctor__email",
        "doctor__first_name",
        "doctor__last_name",
        "patient__email",
        "patient__first_name",
        "patient__last_name",
        "reason",
    )

    readonly_fields = (
        "requested_at",
        "revoked_at",
        "last_accessed_at",
        "access_count",
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)
