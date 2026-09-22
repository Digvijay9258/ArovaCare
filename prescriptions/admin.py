from django.contrib import admin

from .models import Prescription


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "patient",
        "doctor",
        "appointment",
        "diagnosis",
        "follow_up_date",
        "created_at",
    ]

    list_filter = [
        "follow_up_date",
        "created_at",
    ]

    search_fields = [
        "patient__email",
        "doctor__email",
        "diagnosis",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]
