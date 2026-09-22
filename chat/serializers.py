from rest_framework import serializers

from .models import Conversation, Message


class ConversationSerializer(serializers.ModelSerializer):
    doctor_email = serializers.EmailField(
        source="doctor.email",
        read_only=True,
    )

    patient_email = serializers.EmailField(
        source="patient.email",
        read_only=True,
    )

    last_message = serializers.SerializerMethodField()

    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "doctor",
            "doctor_email",
            "patient",
            "patient_email",
            "appointment",
            "created_at",
            "updated_at",
            "last_message",
            "unread_count",
        ]

        read_only_fields = [
            "id",
            "doctor",
            "doctor_email",
            "patient",
            "patient_email",
            "created_at",
            "updated_at",
            "last_message",
            "unread_count",
        ]

    def get_last_message(self, obj):
        message = obj.messages.order_by("-created_at").first()

        if not message:
            return None

        return {
            "id": message.id,
            "sender": message.sender_id,
            "sender_email": message.sender.email,
            "content": message.content,
            "is_read": message.is_read,
            "created_at": message.created_at,
        }

    def get_unread_count(self, obj):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return 0

        return obj.messages.filter(is_read=False).exclude(sender=request.user).count()


class MessageSerializer(serializers.ModelSerializer):
    sender_email = serializers.EmailField(
        source="sender.email",
        read_only=True,
    )

    conversation_id = serializers.IntegerField(
        source="conversation.id",
        read_only=True,
    )

    class Meta:
        model = Message

        fields = [
            "id",
            "conversation",
            "conversation_id",
            "sender",
            "sender_email",
            "content",
            "is_read",
            "attachment",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "sender",
            "sender_email",
            "conversation_id",
            "is_read",
            "created_at",
            "updated_at",
        ]

    def validate_content(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Message content cannot be empty.")

        return value
