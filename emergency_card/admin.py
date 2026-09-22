from django.contrib import admin

from .models import EmergencyCard


@admin.register(EmergencyCard)
class EmergencyCardAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "patient",
        "is_active",
        "created_at",
        "updated_at",
    ]

    list_filter = [
        "is_active",
        "created_at",
    ]

    search_fields = [
        "patient__email",
        "patient__patient_profile__full_name",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]
