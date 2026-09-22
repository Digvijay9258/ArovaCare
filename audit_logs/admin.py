from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "action",
        "resource_type",
        "resource_id",
        "ip_address",
        "created_at",
    )

    list_filter = (
        "action",
        "resource_type",
        "created_at",
    )

    search_fields = (
        "user__email",
        "resource_type",
        "resource_id",
        "ip_address",
    )

    readonly_fields = (
        "user",
        "action",
        "resource_type",
        "resource_id",
        "ip_address",
        "metadata",
        "created_at",
    )

    ordering = ("-created_at",)
