from django.contrib import admin
from .models import DoctorProfile


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):

    list_display = (
        "full_name",
        "user",
        "specialization",
        "medical_registration_number",
        "verification_status",
        "created_at",
    )

    search_fields = (
        "full_name",
        "user__email",
        "specialization",
        "medical_registration_number",
    )

    list_filter = (
        "verification_status",
        "specialization",
    )
