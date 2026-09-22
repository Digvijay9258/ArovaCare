from django.contrib import admin
from .models import MedicalRecord


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "patient",
        "record_type",
        "record_date",
        "uploaded_at",
    )

    search_fields = (
        "title",
        "patient__email",
    )

    list_filter = (
        "record_type",
        "uploaded_at",
    )
