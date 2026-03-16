from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoomViewSet, MembershipViewSet, MessageViewSet, DirectMessageViewSet,
    UserPresenceViewSet, TypingIndicatorViewSet
)

router = DefaultRouter()
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'memberships', MembershipViewSet, basename='membership')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'direct-messages', DirectMessageViewSet, basename='direct-message')
router.register(r'presence', UserPresenceViewSet, basename='presence')
router.register(r'typing', TypingIndicatorViewSet, basename='typing')

urlpatterns = [
    path('', include(router.urls)),
]
