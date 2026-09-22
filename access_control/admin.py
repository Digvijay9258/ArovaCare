from django.contrib import admin
from .models import MedicalRecordAccess


@admin.register(MedicalRecordAccess)
class MedicalRecordAccessAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "patient",
        "doctor",
        "record",
        "status",
        "granted_at",
        "expires_at",
    )

    list_filter = (
        "status",
        "granted_at",
    )

    search_fields = (
        "patient__email",
        "doctor__email",
        "record__title",
    )

    readonly_fields = ("granted_at",)

    ordering = ("-granted_at",)
