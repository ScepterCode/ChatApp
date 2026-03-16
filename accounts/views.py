"""
Authentication views for user registration, login, and password management.
"""
import logging
from typing import Optional
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    RegisterSerializer, LoginSerializer, ProfileSerializer,
    ChangePasswordSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer
)
from .models import CustomUser
from core.utils import log_action, handle_exceptions, sanitize_input

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """
    User registration endpoint.
    
    POST /api/auth/register/
    - username: str (required)
    - email: str (required)
    - password: str (required)
    
    Returns:
    - access: JWT access token
    - refresh: JWT refresh token
    - user: User profile data
    """
    permission_classes = [AllowAny]

    @log_action('user_registration')
    @handle_exceptions
    def post(self, request: Request) -> Response:
        """Register a new user."""
        # Sanitize input data
        data = request.data.copy()
        if 'username' in data:
            data['username'] = sanitize_input(data['username'], max_length=150)
        if 'email' in data:
            data['email'] = sanitize_input(data['email'], max_length=254)
        
        serializer = RegisterSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            logger.info(f"User registered: {user.username}")
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': ProfileSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        logger.warning(f"Registration failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    User login endpoint.
    
    POST /api/auth/login/
    - username: str (required)
    - password: str (required)
    
    Returns:
    - access: JWT access token
    - refresh: JWT refresh token
    - user: User profile data
    - user_id: User ID
    - username: Username
    """
    permission_classes = [AllowAny]

    @log_action('user_login')
    @handle_exceptions
    def post(self, request: Request) -> Response:
        """Authenticate user and return tokens."""
        # Sanitize input data
        data = request.data.copy()
        if 'username' in data:
            data['username'] = sanitize_input(data['username'], max_length=150)
        
        serializer = LoginSerializer(data=data)
        if serializer.is_valid():
            user = authenticate(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password']
            )
            if user:
                refresh = RefreshToken.for_user(user)
                user_data = ProfileSerializer(user).data
                logger.info(f"User logged in: {user.username}")
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': user_data,
                    'user_id': user.id,
                    'username': user.username
                })
            logger.warning(f"Login failed: Invalid credentials for {serializer.validated_data['username']}")
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    """
    Get current user profile.
    
    GET /api/auth/profile/
    
    Returns:
    - User profile data
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request: Request) -> Response:
        """Retrieve current user profile."""
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)


class ChangePasswordView(APIView):
    """
    Change user password.
    
    POST /api/auth/change-password/
    - old_password: str (required)
    - new_password: str (required)
    
    Returns:
    - message: Success message
    """
    permission_classes = [IsAuthenticated]
    
    @log_action('password_change')
    @handle_exceptions
    def post(self, request: Request) -> Response:
        """Change user password."""
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                logger.warning(f"Password change failed for {user.username}: Invalid old password")
                return Response(
                    {'error': 'Old password is incorrect'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            logger.info(f"Password changed for user: {user.username}")
            return Response(
                {'message': 'Password changed successfully'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    """
    Request password reset token.
    
    POST /api/auth/password-reset/
    - email: str (required)
    
    Returns:
    - message: Success message
    """
    permission_classes = [AllowAny]
    
    @log_action('password_reset_request')
    @handle_exceptions
    def post(self, request: Request) -> Response:
        """Generate password reset token and send email."""
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            # Rate limiting: Allow only 3 reset requests per email per hour (disabled for testing)
            # cache_key = f"password_reset_{email}"
            # reset_count = cache.get(cache_key, 0)
            
            # if reset_count >= 3:
            #     logger.warning(f"Password reset rate limit exceeded for: {email}")
            #     return Response({
            #         'error': 'Too many password reset requests. Please try again later.'
            #     }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            try:
                user = CustomUser.objects.filter(email=email).first()
                if not user:
                    raise CustomUser.DoesNotExist()
                    
                token_generator = PasswordResetTokenGenerator()
                token = token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Create reset URL
                reset_url = f"http://localhost:8000/reset-password/?uid={uid}&token={token}"
                
                # Send email
                subject = 'Password Reset - ChatApp'
                message = f"""Hello {user.username},

You requested a password reset for your ChatApp account.

Click the link below to reset your password:
{reset_url}

If you didn't request this, please ignore this email.

Best regards,
ChatApp Team"""
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                
                # Increment rate limit counter (disabled for testing)
                # cache.set(cache_key, reset_count + 1, 3600)  # 1 hour timeout
                
                logger.info(f"Password reset email sent to: {user.email}")
                
                # In development mode, also return the reset URL
                response_data = {
                    'message': 'Password reset email sent. Check your email for instructions.'
                }
                
                if settings.DEBUG:
                    response_data['reset_url'] = reset_url
                    response_data['uid'] = uid
                    response_data['token'] = token
                    print(f"\n" + "="*60)
                    print(f"🔑 PASSWORD RESET EMAIL SENT!")
                    print(f"📧 To: {user.email}")
                    print(f"🔗 Reset Link: {reset_url}")
                    print(f"📝 Check the console output above for the full email content")
                    print(f"="*60 + "\n")
                
                return Response(response_data, status=status.HTTP_200_OK)
                
            except CustomUser.DoesNotExist:
                # Increment rate limit counter even for non-existent emails (disabled for testing)
                # cache.set(cache_key, reset_count + 1, 3600)
                
                logger.warning(f"Password reset requested for non-existent email: {email}")
                # Return success message for security (don't reveal if email exists)
                return Response({
                    'message': 'Password reset email sent. Check your email for instructions.'
                }, status=status.HTTP_200_OK)
            except Exception as e:
                # Handle any other unexpected errors (like MultipleObjectsReturned)
                logger.error(f"Unexpected error in password reset for {email}: {str(e)}")
                cache.set(cache_key, reset_count + 1, 3600)  # Still increment to prevent abuse
                return Response({
                    'message': 'Password reset email sent. Check your email for instructions.'
                }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with token.
    
    POST /api/auth/password-reset-confirm/
    - uid: str (required, base64 encoded user ID)
    - token: str (required)
    - new_password: str (required)
    
    Returns:
    - message: Success message
    """
    permission_classes = [AllowAny]
    
    @log_action('password_reset_confirm')
    @handle_exceptions
    def post(self, request: Request) -> Response:
        """Reset password with valid token."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            try:
                uid = request.data.get('uid')
                token = serializer.validated_data['token']
                user_id = force_str(urlsafe_base64_decode(uid))
                user = CustomUser.objects.get(pk=user_id)
                
                token_generator = PasswordResetTokenGenerator()
                if token_generator.check_token(user, token):
                    user.set_password(serializer.validated_data['new_password'])
                    user.save()
                    logger.info(f"Password reset completed for: {user.username}")
                    return Response(
                        {'message': 'Password reset successfully'},
                        status=status.HTTP_200_OK
                    )
                logger.warning(f"Password reset failed: Invalid or expired token for user {user_id}")
                return Response(
                    {'error': 'Invalid or expired token'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except (CustomUser.DoesNotExist, ValueError) as e:
                logger.error(f"Password reset error: {str(e)}")
                return Response(
                    {'error': 'Invalid reset link'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    User logout endpoint.
    
    POST /api/auth/logout/
    - refresh: str (required, refresh token)
    
    Returns:
    - message: Success message
    """
    permission_classes = [IsAuthenticated]
    
    @log_action('user_logout')
    @handle_exceptions
    def post(self, request: Request) -> Response:
        """Logout user by blacklisting refresh token."""
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info(f"User logged out: {request.user.username}")
            return Response(
                {'message': 'Logged out successfully'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )



class UsersListView(APIView):
    """
    List all users with search capability.
    
    GET /api/auth/users/?search=username
    
    Returns:
    - List of users
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request: Request) -> Response:
        """Get list of users with optional search."""
        search_query = request.query_params.get('search', '').strip()
        
        users = CustomUser.objects.all()
        
        if search_query:
            users = users.filter(username__icontains=search_query)
        
        # Exclude current user
        users = users.exclude(id=request.user.id)
        
        serializer = ProfileSerializer(users, many=True)
        return Response({
            'count': users.count(),
            'results': serializer.data
        })
