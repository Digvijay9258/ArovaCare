from django.contrib import admin

from .models import Consultation


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "appointment",
        "doctor",
        "patient",
        "status",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "doctor__email",
        "patient__email",
        "doctor__username",
        "patient__username",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)
