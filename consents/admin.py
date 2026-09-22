from django.contrib import admin
from .models import Consent


@admin.register(Consent)
class ConsentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "patient",
        "doctor",
        "consent_type",
        "status",
        "granted_at",
        "expires_at",
        "revoked_at",
    )

    list_filter = (
        "consent_type",
        "status",
        "granted_at",
    )

    search_fields = (
        "patient__email",
        "doctor__email",
        "purpose",
    )

    readonly_fields = (
        "granted_at",
        "revoked_at",
        "created_at",
        "updated_at",
    )

    ordering = ("-granted_at",)
