from .models import Notification


def create_appointment_notification(
    recipient,
    title,
    message,
    appointment,
):
    """
    Create an appointment-related notification.

    recipient:
        User who should receive the notification.

    title:
        Notification title.

    message:
        Notification message.

    appointment:
        Appointment instance related to the notification.
    """

    return Notification.objects.create(
        recipient=recipient,
        notification_type=Notification.NotificationType.APPOINTMENT,
        title=title,
        message=message,
        reference_id=appointment.id,
        reference_type="appointment",
    )


def create_appointment_notification(
    recipient,
    title,
    message,
    appointment,
):
    """
    Create an appointment-related notification.

    recipient:
        User who should receive the notification.

    title:
        Notification title.

    message:
        Notification message.

    appointment:
        Appointment instance related to the notification.
    """

    return Notification.objects.create(
        recipient=recipient,
        notification_type=Notification.NotificationType.APPOINTMENT,
        title=title,
        message=message,
        reference_id=appointment.id,
        reference_type="appointment",
    )
