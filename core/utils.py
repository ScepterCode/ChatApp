"""
Utility functions for the chat application.
"""
import logging
from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

logger = logging.getLogger(__name__)


def log_action(action_type):
    """
    Decorator to log user actions.
    
    Args:
        action_type (str): Type of action being performed
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            user = request.user
            logger.info(
                f"Action: {action_type} | User: {user.username} | "
                f"Method: {request.method} | Path: {request.path}"
            )
            try:
                result = func(self, request, *args, **kwargs)
                logger.info(f"Action completed successfully: {action_type}")
                return result
            except Exception as e:
                logger.error(
                    f"Action failed: {action_type} | Error: {str(e)}",
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


def handle_exceptions(func):
    """
    Decorator to handle common exceptions in views.
    """
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        try:
            return func(self, request, *args, **kwargs)
        except ValueError as e:
            logger.warning(f"ValueError: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except PermissionError as e:
            logger.warning(f"PermissionError: {str(e)}")
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    return wrapper


def cache_result(timeout=300):
    """
    Decorator to cache view results.
    
    Args:
        timeout (int): Cache timeout in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            cache_key = f"{func.__name__}:{request.user.id}:{request.path}"
            result = cache.get(cache_key)
            
            if result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return result
            
            result = func(self, request, *args, **kwargs)
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cache set for {cache_key}")
            return result
        return wrapper
    return decorator


def validate_input(required_fields):
    """
    Decorator to validate required input fields.
    
    Args:
        required_fields (list): List of required field names
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            data = request.data if hasattr(request, 'data') else request.POST
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                logger.warning(f"Missing required fields: {missing_fields}")
                return Response(
                    {'error': f'Missing required fields: {", ".join(missing_fields)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator


def rate_limit(calls=100, period=3600):
    """
    Simple rate limiting decorator.
    
    Args:
        calls (int): Number of allowed calls
        period (int): Time period in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            user_id = request.user.id if request.user.is_authenticated else request.META.get('REMOTE_ADDR')
            cache_key = f"rate_limit:{func.__name__}:{user_id}"
            
            count = cache.get(cache_key, 0)
            if count >= calls:
                logger.warning(f"Rate limit exceeded for {user_id}")
                return Response(
                    {'error': 'Rate limit exceeded'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            cache.set(cache_key, count + 1, period)
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator


def sanitize_input(text, max_length=5000):
    """
    Sanitize user input.
    
    Args:
        text (str): Input text to sanitize
        max_length (int): Maximum allowed length
        
    Returns:
        str: Sanitized text
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    
    # Strip whitespace
    text = text.strip()
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    return text


def get_client_ip(request):
    """
    Get client IP address from request.
    
    Args:
        request: Django request object
        
    Returns:
        str: Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def format_error_response(error_code, message, details=None):
    """
    Format error response consistently.
    
    Args:
        error_code (str): Error code
        message (str): Error message
        details (dict): Additional error details
        
    Returns:
        dict: Formatted error response
    """
    response = {
        'error': {
            'code': error_code,
            'message': message,
        }
    }
    
    if details:
        response['error']['details'] = details
    
    return response


def format_success_response(data, message=None):
    """
    Format success response consistently.
    
    Args:
        data: Response data
        message (str): Optional success message
        
    Returns:
        dict: Formatted success response
    """
    response = {'data': data}
    
    if message:
        response['message'] = message
    
    return response


def validate_message_content(content):
    """
    Validate message content for safety and length.
    
    Args:
        content (str): Message content to validate
        
    Returns:
        bool: True if content is valid, False otherwise
    """
    if not content or not isinstance(content, str):
        return False
    
    content = content.strip()
    
    # Check if empty after stripping
    if not content:
        return False
    
    # Check length limits
    if len(content) > 5000:
        return False
    
    # Check for null bytes or other problematic characters
    if '\x00' in content:
        return False
    
    return True
