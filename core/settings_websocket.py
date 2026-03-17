# WebSocket-only settings for Fly.io deployment
# This inherits from main settings but removes unnecessary components

from .settings import *
import os

# Override for WebSocket-only mode
WEBSOCKET_ONLY = os.getenv('WEBSOCKET_ONLY', 'false').lower() == 'true'

if WEBSOCKET_ONLY:
    print("🔌 Running in WebSocket-only mode for Fly.io")
    
    # Remove unnecessary apps for WebSocket service
    INSTALLED_APPS = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'channels',
        'accounts',  # Keep for user model
        'chat',      # Keep for chat models
    ]
    
    # Minimal middleware for WebSocket service
    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'corsheaders.middleware.CorsMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
    ]
    
    # Remove admin and other HTTP-only URLs
    ROOT_URLCONF = 'core.urls_websocket'
    
    # WebSocket-specific CORS settings
    CORS_ALLOWED_ORIGINS = [
        "https://chatapp-1-kctm.onrender.com",  # Your main Render app
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    # Allow WebSocket connections from your main app
    ALLOWED_HOSTS = [
        'localhost',
        '127.0.0.1',
        'chatapp-websockets.fly.dev',  # Your Fly.io app name
        '.fly.dev',
    ]
    
    # Disable static files for WebSocket service
    STATIC_URL = None
    STATICFILES_DIRS = []
    
    print(f"🔌 WebSocket service configured for: {ALLOWED_HOSTS}")