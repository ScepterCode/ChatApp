from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
import os

def health_check(request):
    """Health check endpoint for Render deployment"""
    return JsonResponse({'status': 'healthy', 'service': 'chatapp'})

def websocket_test(request):
    """WebSocket connection test endpoint"""
    return JsonResponse({
        'websocket_url': f"wss://{request.get_host()}/ws/chat/test/",
        'status': 'ready',
        'redis_configured': bool(settings.REDIS_URL),
        'channels_configured': 'channels_redis' in str(settings.CHANNEL_LAYERS),
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/chat/', include('chat.urls')),
    path('health/', health_check, name='health-check'),
    path('ws-test/', websocket_test, name='websocket-test'),
    
    # Frontend pages
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('signup/', TemplateView.as_view(template_name='signup.html'), name='signup'),
    path('forgot-password/', TemplateView.as_view(template_name='forgot-password.html'), name='forgot-password'),
    path('reset-password/', TemplateView.as_view(template_name='reset-password.html'), name='reset-password'),
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    path('chat/', TemplateView.as_view(template_name='chat.html'), name='chat'),
    path('groups/', TemplateView.as_view(template_name='groups.html'), name='groups'),
    path('group-chat/', TemplateView.as_view(template_name='group-chat.html'), name='group-chat'),
    path('group-chat-polling/', TemplateView.as_view(template_name='group-chat-polling.html'), name='group-chat-polling'),
    path('websocket-test/', TemplateView.as_view(template_name='websocket-test.html'), name='websocket-test'),
    path('websocket-debug/', TemplateView.as_view(template_name='websocket-debug.html'), name='websocket-debug'),
]

# Serve static files in development
if settings.DEBUG:
    from django.contrib.staticfiles.views import serve
    from django.urls import re_path
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve),
    ]