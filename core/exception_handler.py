"""
Custom exception handler for DRF.
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that logs exceptions and formats responses.
    
    Args:
        exc: Exception instance
        context: Context dict with request, view, etc.
        
    Returns:
        Response: Formatted error response
    """
    # Get the standard exception response
    response = exception_handler(exc, context)
    
    # Log the exception
    request = context.get('request')
    view = context.get('view')
    
    logger.error(
        f"Exception in {view.__class__.__name__}.{context.get('view').action if hasattr(context.get('view'), 'action') else 'unknown'} | "
        f"User: {request.user.username if request.user.is_authenticated else 'Anonymous'} | "
        f"Method: {request.method} | Path: {request.path} | "
        f"Error: {str(exc)}",
        exc_info=True
    )
    
    # Customize the response format
    if response is not None:
        custom_response_data = {
            'error': {
                'status_code': response.status_code,
                'message': response.data.get('detail', 'An error occurred'),
            }
        }
        
        # Add field errors if present
        if isinstance(response.data, dict):
            errors = {k: v for k, v in response.data.items() if k != 'detail'}
            if errors:
                custom_response_data['error']['fields'] = errors
        
        response.data = custom_response_data
    else:
        # Handle exceptions that don't have a response
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        response = Response(
            {
                'error': {
                    'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                    'message': 'An unexpected error occurred'
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return response
