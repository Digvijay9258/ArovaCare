from django.urls import path

from .views import (
    NotificationListView,
    NotificationDetailView,
    UnreadNotificationCountView,
    MarkNotificationReadView,
    MarkAllNotificationsReadView,
    NotificationDeleteView,
)

urlpatterns = [
    path(
        "",
        NotificationListView.as_view(),
        name="notification-list",
    ),
    path(
        "unread-count/",
        UnreadNotificationCountView.as_view(),
        name="notification-unread-count",
    ),
    path(
        "mark-all-read/",
        MarkAllNotificationsReadView.as_view(),
        name="notification-mark-all-read",
    ),
    path(
        "<int:pk>/",
        NotificationDetailView.as_view(),
        name="notification-detail",
    ),
    path(
        "<int:pk>/read/",
        MarkNotificationReadView.as_view(),
        name="notification-read",
    ),
    path(
        "<int:pk>/delete/",
        NotificationDeleteView.as_view(),
        name="notification-delete",
    ),
]
