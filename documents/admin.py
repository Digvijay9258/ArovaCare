from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "title",
        "patient",
        "document_type",
        "visibility",
        "document_date",
        "uploaded_at",
    )

    search_fields = (
        "title",
        "patient__email",
        "description",
    )

    list_filter = (
        "document_type",
        "visibility",
        "uploaded_at",
    )

    readonly_fields = (
        "uploaded_at",
        "updated_at",
    )

    ordering = ("-uploaded_at",)

    list_per_page = 50
