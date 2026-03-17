# Minimal URLs for WebSocket-only service on Fly.io
from django.urls import path
from django.http import JsonResponse
from django.conf import settings

def health_check(request):
    """Health check endpoint for Fly.io"""
    return JsonResponse({
        'status': 'healthy', 
        'service': 'websocket-only',
        'websocket_enabled': True,
        'redis_configured': bool(settings.REDIS_URL),
    })

def websocket_info(request):
    """WebSocket connection info"""
    return JsonResponse({
        'websocket_url': f"wss://{request.get_host()}/ws/chat/{{room_id}}/",
        'status': 'ready',
        'service': 'websocket-only',
        'cors_origins': settings.CORS_ALLOWED_ORIGINS,
    })

urlpatterns = [
    path('health/', health_check, name='health-check'),
    path('ws-info/', websocket_info, name='websocket-info'),
]