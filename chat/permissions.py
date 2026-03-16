from rest_framework.permissions import BasePermission

class IsRoomMember(BasePermission):
    """Check if user is a member of the room."""
    def has_object_permission(self, request, view, obj):
        return obj.members.filter(user=request.user).exists()

class IsRoomAdmin(BasePermission):
    """Check if user is the admin of the room."""
    def has_object_permission(self, request, view, obj):
        return obj.admin == request.user

class IsRoomMemberOrAdmin(BasePermission):
    """Check if user is either a member or admin of the room."""
    def has_object_permission(self, request, view, obj):
        # Admin always has access
        if obj.admin == request.user:
            return True
        # Check membership
        return obj.memberships.filter(user=request.user).exists()

