from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.permissions import IsPatient, IsDoctor
from notifications.services import create_appointment_notification

from .models import Appointment
from .serializers import AppointmentSerializer


class PatientAppointmentListCreateView(generics.ListCreateAPIView):

    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, IsPatient]

    def get_queryset(self):
        return (
            Appointment.objects.filter(patient=self.request.user)
            .select_related(
                "patient",
                "doctor",
            )
            .order_by(
                "-appointment_date",
                "-appointment_time",
            )
        )

    def perform_create(self, serializer):

        appointment = serializer.save(patient=self.request.user)

        create_appointment_notification(
            recipient=appointment.doctor,
            title="New Appointment Request",
            message=(
                f"You have received a new appointment request "
                f"from {appointment.patient.email} for "
                f"{appointment.appointment_date} at "
                f"{appointment.appointment_time}."
            ),
            appointment=appointment,
        )


class DoctorAppointmentListView(generics.ListAPIView):

    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, IsDoctor]

    def get_queryset(self):
        return (
            Appointment.objects.filter(doctor=self.request.user)
            .select_related(
                "patient",
                "doctor",
            )
            .order_by(
                "-appointment_date",
                "-appointment_time",
            )
        )


class DoctorAppointmentStatusView(generics.UpdateAPIView):

    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, IsDoctor]
    http_method_names = ["patch"]

    def get_queryset(self):
        return Appointment.objects.filter(doctor=self.request.user)

    def partial_update(self, request, *args, **kwargs):

        appointment = self.get_object()

        old_status = appointment.status
        new_status = request.data.get("status")

        if new_status == "ACCEPTED":

            if appointment.status != "PENDING":
                return Response(
                    {"error": ("Only PENDING appointments " "can be accepted.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        elif new_status == "REJECTED":

            if appointment.status != "PENDING":
                return Response(
                    {"error": ("Only PENDING appointments " "can be rejected.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        elif new_status == "COMPLETED":

            if appointment.status != "ACCEPTED":
                return Response(
                    {"error": ("Only ACCEPTED appointments " "can be completed.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        elif new_status == "CANCELLED":

            if appointment.status not in [
                "PENDING",
                "ACCEPTED",
            ]:
                return Response(
                    {"error": ("This appointment cannot " "be cancelled.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        else:

            return Response(
                {
                    "error": (
                        "Invalid status. Use one of: "
                        "ACCEPTED, REJECTED, "
                        "COMPLETED, CANCELLED."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = new_status

        appointment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # -----------------------------------------------
        # AUTOMATIC APPOINTMENT NOTIFICATIONS
        # -----------------------------------------------

        if old_status != new_status:

            if new_status == "ACCEPTED":

                create_appointment_notification(
                    recipient=appointment.patient,
                    title="Appointment Accepted",
                    message=(
                        f"Your appointment with "
                        f"Dr. {appointment.doctor.email} "
                        f"on {appointment.appointment_date} at "
                        f"{appointment.appointment_time} "
                        f"has been accepted."
                    ),
                    appointment=appointment,
                )

            elif new_status == "REJECTED":

                create_appointment_notification(
                    recipient=appointment.patient,
                    title="Appointment Rejected",
                    message=(
                        f"Your appointment with "
                        f"Dr. {appointment.doctor.email} "
                        f"on {appointment.appointment_date} at "
                        f"{appointment.appointment_time} "
                        f"has been rejected."
                    ),
                    appointment=appointment,
                )

            elif new_status == "COMPLETED":

                create_appointment_notification(
                    recipient=appointment.patient,
                    title="Appointment Completed",
                    message=(
                        f"Your appointment with "
                        f"Dr. {appointment.doctor.email} "
                        f"on {appointment.appointment_date} at "
                        f"{appointment.appointment_time} "
                        f"has been marked as completed."
                    ),
                    appointment=appointment,
                )

            elif new_status == "CANCELLED":

                create_appointment_notification(
                    recipient=appointment.patient,
                    title="Appointment Cancelled",
                    message=(
                        f"Your appointment with "
                        f"Dr. {appointment.doctor.email} "
                        f"on {appointment.appointment_date} at "
                        f"{appointment.appointment_time} "
                        f"has been cancelled."
                    ),
                    appointment=appointment,
                )

        serializer = self.get_serializer(appointment)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class PatientCancelAppointmentView(generics.UpdateAPIView):

    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, IsPatient]
    http_method_names = ["patch"]

    def get_queryset(self):
        return Appointment.objects.filter(patient=self.request.user)

    def partial_update(self, request, *args, **kwargs):

        appointment = self.get_object()

        if appointment.status not in [
            "PENDING",
            "ACCEPTED",
        ]:
            return Response(
                {
                    "error": (
                        "Only PENDING or ACCEPTED " "appointments can be cancelled."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = "CANCELLED"

        appointment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # Notify doctor that patient cancelled
        create_appointment_notification(
            recipient=appointment.doctor,
            title="Appointment Cancelled",
            message=(
                f"The appointment with "
                f"{appointment.patient.email} on "
                f"{appointment.appointment_date} at "
                f"{appointment.appointment_time} "
                f"has been cancelled by the patient."
            ),
            appointment=appointment,
        )

        serializer = self.get_serializer(appointment)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
