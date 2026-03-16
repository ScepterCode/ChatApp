"""
Custom exception classes for the chat application.
"""
from rest_framework.exceptions import APIException
from rest_framework import status


class ChatException(APIException):
    """Base exception for chat application."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'An error occurred.'
    default_code = 'error'


class RoomNotFound(ChatException):
    """Raised when a room is not found."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Room not found.'
    default_code = 'room_not_found'


class UserNotMember(ChatException):
    """Raised when user is not a member of the room."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You are not a member of this room.'
    default_code = 'not_member'


class UnauthorizedAction(ChatException):
    """Raised when user is not authorized to perform action."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You are not authorized to perform this action.'
    default_code = 'unauthorized'


class InvalidMessage(ChatException):
    """Raised when message is invalid."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid message.'
    default_code = 'invalid_message'


class UserNotFound(ChatException):
    """Raised when user is not found."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'User not found.'
    default_code = 'user_not_found'


class InvalidToken(ChatException):
    """Raised when token is invalid."""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Invalid or expired token.'
    default_code = 'invalid_token'
