from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    """
    Return notifications belonging only to the authenticated user.
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).only(
            "id",
            "recipient",
            "notification_type",
            "title",
            "message",
            "is_read",
            "reference_id",
            "reference_type",
            "created_at",
            "read_at",
        )


class NotificationDetailView(generics.RetrieveAPIView):
    """
    Retrieve one notification belonging to the authenticated user.
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class UnreadNotificationCountView(generics.GenericAPIView):
    """
    Return the number of unread notifications for the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()

        return Response(
            {
                "unread_count": unread_count,
            },
            status=HTTP_200_OK,
        )


class MarkNotificationReadView(generics.UpdateAPIView):
    """
    Mark one notification as read.
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = ["patch"]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    def perform_update(self, serializer):
        serializer.save(
            is_read=True,
            read_at=timezone.now(),
        )


class MarkAllNotificationsReadView(generics.GenericAPIView):
    """
    Mark all notifications belonging to the authenticated user as read.
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        updated_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(
            is_read=True,
            read_at=timezone.now(),
        )

        return Response(
            {
                "message": "All notifications marked as read.",
                "updated_count": updated_count,
            },
            status=HTTP_200_OK,
        )


class NotificationDeleteView(generics.DestroyAPIView):
    """
    Delete a notification belonging to the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)
