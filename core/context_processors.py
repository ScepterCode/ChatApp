# Context processors for templates
from django.conf import settings

def websocket_config(request):
    """Add WebSocket configuration to template context"""
    return {
        'WEBSOCKET_SERVICE_URL': getattr(settings, 'WEBSOCKET_SERVICE_URL', 'wss://chatapp-websockets.fly.dev'),
        'WEBSOCKET_ENABLED': getattr(settings, 'WEBSOCKET_ENABLED', True),
    }