from django.contrib import admin
from .models import PatientProfile


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):

    list_display = (
        "full_name",
        "user",
        "gender",
        "blood_group",
        "phone",
        "created_at",
    )

    search_fields = (
        "full_name",
        "user__email",
        "phone",
    )
