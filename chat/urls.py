from django.urls import path

from .views import (
    ConversationListCreateView,
    ConversationDetailView,
    ConversationMessageListCreateView,
    MessageDetailView,
    MarkMessageReadView,
)

urlpatterns = [
    path(
        "conversations/",
        ConversationListCreateView.as_view(),
        name="conversation-list",
    ),
    path(
        "conversations/<int:pk>/",
        ConversationDetailView.as_view(),
        name="conversation-detail",
    ),
    path(
        "conversations/<int:conversation_id>/messages/",
        ConversationMessageListCreateView.as_view(),
        name="conversation-messages",
    ),
    path(
        "messages/<int:pk>/",
        MessageDetailView.as_view(),
        name="message-detail",
    ),
    path(
        "messages/<int:pk>/read/",
        MarkMessageReadView.as_view(),
        name="message-read",
    ),
]
