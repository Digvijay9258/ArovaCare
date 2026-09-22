from datetime import datetime

from django.utils import timezone

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.permissions import IsPatient

from appointments.models import Appointment
from consultations.models import Consultation
from prescriptions.models import Prescription
from medical_records.models import MedicalRecord


class PatientTimelineView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsPatient]

    def get(self, request, *args, **kwargs):
        patient = request.user
        events = []

        # ---------------------------------------------------------
        # APPOINTMENTS
        # ---------------------------------------------------------
        appointments = Appointment.objects.filter(patient=patient).select_related(
            "doctor"
        )

        for appointment in appointments:
            event_datetime = datetime.combine(
                appointment.appointment_date,
                appointment.appointment_time,
            )

            event_datetime = timezone.make_aware(
                event_datetime,
                timezone.get_current_timezone(),
            )

            events.append(
                {
                    "type": "APPOINTMENT",
                    "id": appointment.id,
                    "date": appointment.appointment_date,
                    "time": appointment.appointment_time,
                    "datetime": event_datetime,
                    "title": "Doctor Appointment",
                    "description": appointment.reason,
                    "status": appointment.status,
                    "doctor": appointment.doctor.email,
                    "notes": appointment.notes,
                }
            )

        # ---------------------------------------------------------
        # CONSULTATIONS
        # ---------------------------------------------------------
        consultations = Consultation.objects.filter(patient=patient).select_related(
            "doctor", "appointment"
        )

        for consultation in consultations:
            appointment = consultation.appointment

            event_datetime = datetime.combine(
                appointment.appointment_date,
                appointment.appointment_time,
            )

            event_datetime = timezone.make_aware(
                event_datetime,
                timezone.get_current_timezone(),
            )

            events.append(
                {
                    "type": "CONSULTATION",
                    "id": consultation.id,
                    "date": appointment.appointment_date,
                    "time": appointment.appointment_time,
                    "datetime": event_datetime,
                    "title": "Medical Consultation",
                    "description": consultation.diagnosis,
                    "status": consultation.status,
                    "doctor": consultation.doctor.email,
                    "symptoms": consultation.symptoms,
                    "clinical_notes": consultation.clinical_notes,
                    "diagnosis": consultation.diagnosis,
                    "treatment_plan": consultation.treatment_plan,
                }
            )

        # ---------------------------------------------------------
        # PRESCRIPTIONS
        # ---------------------------------------------------------
        prescriptions = Prescription.objects.filter(patient=patient).select_related(
            "doctor", "appointment"
        )

        for prescription in prescriptions:
            appointment = prescription.appointment

            event_datetime = datetime.combine(
                appointment.appointment_date,
                appointment.appointment_time,
            )

            event_datetime = timezone.make_aware(
                event_datetime,
                timezone.get_current_timezone(),
            )

            events.append(
                {
                    "type": "PRESCRIPTION",
                    "id": prescription.id,
                    "date": appointment.appointment_date,
                    "time": appointment.appointment_time,
                    "datetime": event_datetime,
                    "title": "Prescription",
                    "description": prescription.diagnosis,
                    "doctor": prescription.doctor.email,
                    "diagnosis": prescription.diagnosis,
                    "medicines": prescription.medicines,
                    "instructions": prescription.instructions,
                    "follow_up_date": prescription.follow_up_date,
                }
            )

        # ---------------------------------------------------------
        # MEDICAL RECORDS
        # ---------------------------------------------------------
        medical_records = MedicalRecord.objects.filter(patient=patient)

        for record in medical_records:
            if record.record_date:
                record_datetime = timezone.make_aware(
                    datetime.combine(
                        record.record_date,
                        datetime.min.time(),
                    ),
                    timezone.get_current_timezone(),
                )
            else:
                record_datetime = record.uploaded_at

            file_url = None

            if record.file:
                try:
                    file_url = request.build_absolute_uri(record.file.url)
                except ValueError:
                    file_url = None

            events.append(
                {
                    "type": "MEDICAL_RECORD",
                    "id": record.id,
                    "date": record.record_date,
                    "time": None,
                    "datetime": record_datetime,
                    "title": record.title,
                    "description": record.description,
                    "record_type": record.record_type,
                    "file": file_url,
                    "uploaded_at": record.uploaded_at,
                }
            )

        # ---------------------------------------------------------
        # SORT TIMELINE
        # ---------------------------------------------------------
        events.sort(
            key=lambda event: event["datetime"],
            reverse=True,
        )

        return Response(
            {
                "count": len(events),
                "timeline": events,
            }
        )
