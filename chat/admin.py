from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "doctor",
        "patient",
        "appointment",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "created_at",
        "updated_at",
    )

    search_fields = (
        "doctor__email",
        "doctor__username",
        "patient__email",
        "patient__username",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = ("-updated_at",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "conversation",
        "sender",
        "content_preview",
        "is_read",
        "created_at",
    )

    list_filter = (
        "is_read",
        "created_at",
    )

    search_fields = (
        "content",
        "sender__email",
        "sender__username",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)

    @admin.display(description="Message")
    def content_preview(self, obj):
        if len(obj.content) > 60:
            return obj.content[:60] + "..."
        return obj.content
