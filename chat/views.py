from django.db.models import Q

from rest_framework import generics
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer

from rest_framework.response import Response


class ConversationListCreateView(generics.ListCreateAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        return Conversation.objects.filter(
            Q(doctor=user) | Q(patient=user)
        ).select_related(
            "doctor",
            "patient",
            "appointment",
        )

    def create(self, request, *args, **kwargs):
        user = request.user

        if getattr(user, "role", None) not in ["DOCTOR", "PATIENT"]:
            raise PermissionDenied(
                "Only doctors and patients can create conversations."
            )

        doctor_id = request.data.get("doctor")
        patient_id = request.data.get("patient")

        if not doctor_id and not patient_id:
            raise ValidationError("Please provide the doctor ID or patient ID.")

        if getattr(user, "role", None) == "PATIENT":
            if not doctor_id:
                raise ValidationError({"doctor": "Doctor ID is required."})

            patient_id = user.id

        elif getattr(user, "role", None) == "DOCTOR":
            if not patient_id:
                raise ValidationError({"patient": "Patient ID is required."})

            doctor_id = user.id

        try:
            from django.contrib.auth import get_user_model

            User = get_user_model()

            doctor = User.objects.get(
                id=doctor_id,
                role="DOCTOR",
            )

            patient = User.objects.get(
                id=patient_id,
                role="PATIENT",
            )

        except User.DoesNotExist:
            raise ValidationError("Invalid doctor or patient ID.")

        if doctor == patient:
            raise ValidationError("Doctor and patient cannot be the same user.")

        existing = Conversation.objects.filter(
            doctor=doctor,
            patient=patient,
        ).first()

        if existing:
            serializer = self.get_serializer(existing)

            return Response(
                serializer.data,
                status=200,
            )

        appointment_id = request.data.get("appointment")

        conversation_data = {
            "doctor": doctor,
            "patient": patient,
        }

        if appointment_id:
            from appointments.models import Appointment

            try:
                appointment = Appointment.objects.get(
                    id=appointment_id,
                    doctor=doctor,
                    patient=patient,
                )

                conversation_data["appointment"] = appointment

            except Appointment.DoesNotExist:
                raise ValidationError(
                    {
                        "appointment": (
                            "Appointment does not exist or does not "
                            "belong to this doctor and patient."
                        )
                    }
                )

        conversation = Conversation.objects.create(**conversation_data)

        serializer = self.get_serializer(conversation)

        return Response(
            serializer.data,
            status=201,
        )


class ConversationDetailView(generics.RetrieveAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        return Conversation.objects.filter(
            Q(doctor=user) | Q(patient=user)
        ).select_related(
            "doctor",
            "patient",
            "appointment",
        )


class ConversationMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_conversation(self):
        user = self.request.user

        try:
            return Conversation.objects.get(
                Q(id=self.kwargs["conversation_id"])
                & (Q(doctor=user) | Q(patient=user))
            )

        except Conversation.DoesNotExist:
            raise NotFound("Conversation not found or you do not have access to it.")

    def get_queryset(self):
        conversation = self.get_conversation()

        return Message.objects.filter(conversation=conversation).select_related(
            "sender",
            "conversation",
        )

    def perform_create(self, serializer):
        conversation = self.get_conversation()

        serializer.save(
            conversation=conversation,
            sender=self.request.user,
        )


class MessageDetailView(generics.RetrieveAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        return Message.objects.filter(
            Q(conversation__doctor=user) | Q(conversation__patient=user)
        ).select_related(
            "sender",
            "conversation",
        )


class MarkMessageReadView(generics.UpdateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = ["patch"]

    def get_queryset(self):
        user = self.request.user

        return Message.objects.filter(
            Q(conversation__doctor=user) | Q(conversation__patient=user)
        ).select_related(
            "sender",
            "conversation",
        )

    def perform_update(self, serializer):
        message = self.get_object()

        if message.sender == self.request.user:
            raise ValidationError("You cannot mark your own message as read.")

        serializer.save(is_read=True)
