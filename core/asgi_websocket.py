# WebSocket-only ASGI application for Fly.io
import os
import django
from django.core.asgi import get_asgi_application

# Use WebSocket-specific settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_websocket')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from core.websocket_auth import JWTAuthMiddlewareStack
from core.routing import websocket_urlpatterns

# WebSocket-focused application
application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # Minimal HTTP for health checks
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})

print("🔌 WebSocket-only ASGI application loaded for Fly.io")