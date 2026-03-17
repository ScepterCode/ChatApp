from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoomViewSet, MembershipViewSet, MessageViewSet, DirectMessageViewSet,
    UserPresenceViewSet, TypingIndicatorViewSet
)
from .views_polling import PollingChatViewSet, poll_messages

router = DefaultRouter()
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'memberships', MembershipViewSet, basename='membership')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'direct-messages', DirectMessageViewSet, basename='direct-message')
router.register(r'presence', UserPresenceViewSet, basename='presence')
router.register(r'typing', TypingIndicatorViewSet, basename='typing')

# Polling-based chat (no WebSockets)
router.register(r'polling', PollingChatViewSet, basename='polling-chat')

urlpatterns = [
    path('', include(router.urls)),
    # Simple polling endpoint
    path('poll/', poll_messages, name='poll-messages'),
]
