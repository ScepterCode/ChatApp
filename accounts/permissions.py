from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.owner == request.user

class IsRoomAdmin(BasePermission):
    """
    Permission to check if user is room admin.
    """
    def has_object_permission(self, request, view, obj):
        return obj.admin == request.user

class IsRoomMember(BasePermission):
    """
    Permission to check if user is a member of the room.
    """
    def has_object_permission(self, request, view, obj):
        from chat.models import Membership
        return Membership.objects.filter(user=request.user, room=obj).exists()
