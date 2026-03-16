import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from chat.consumers_minimal import MinimalChatConsumer

# Minimal WebSocket routing without authentication middleware
minimal_websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_id>\w+)/$', MinimalChatConsumer.as_asgi()),
]

# Minimal ASGI application without JWT middleware
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(minimal_websocket_urlpatterns),
})