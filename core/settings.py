# settings.py
# Django settings for chat project.

import os
from decouple import config
import dj_database_url

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1', 
    'testserver',
    'chatapp-1-kctm.onrender.com',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'channels',
    'corsheaders',
    'accounts',
    'chat',
    # AI app completely removed to avoid memory issues on Render
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.websocket_config',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://neondb_owner:npg_fTlgY7SIAhM5@ep-blue-leaf-ady4zdl9-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require',
        conn_max_age=600,
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # For production collectstatic
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # Development static files
]

# Channels
ASGI_APPLICATION = 'core.asgi.application'

# WebSocket Configuration for Render
WEBSOCKET_ENABLED = config('WEBSOCKET_ENABLED', default=True, cast=bool)
ALLOWED_WEBSOCKET_ORIGINS = config('ALLOWED_WEBSOCKET_ORIGINS', default='').split(',')

# WebSocket service URL (separate Fly.io service)
WEBSOCKET_SERVICE_URL = config('WEBSOCKET_SERVICE_URL', default='wss://chatapp-websockets.fly.dev')

# Add WebSocket origins to ALLOWED_HOSTS if specified
if ALLOWED_WEBSOCKET_ORIGINS and ALLOWED_WEBSOCKET_ORIGINS[0]:
    for origin in ALLOWED_WEBSOCKET_ORIGINS:
        host = origin.replace('https://', '').replace('http://', '')
        if host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host)

# Redis Configuration (Upstash with connection pooling)
REDIS_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/0')

# Parse Redis URL for manual configuration
from urllib.parse import urlparse
_redis_url = urlparse(REDIS_URL)

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
            'capacity': 1500,  # Maximum messages to store
            'expiry': 60,      # Message expiry in seconds
            'group_expiry': 86400,  # Group expiry in seconds (24 hours)
            'symmetric_encryption_keys': [SECRET_KEY],
        },
    },
}

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'EXCEPTION_HANDLER': 'core.exception_handler.custom_exception_handler',
}

# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# Custom user model
AUTH_USER_MODEL = 'accounts.CustomUser'

# CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://chatapp-1-kctm.onrender.com",
]

# Allow all origins temporarily for debugging
CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True

# Email Configuration (Console backend for development)
# Logging
from core.logging_config import LOGGING

# Email Configuration
if config('RESEND_API_KEY', default=None):
    # Resend email backend
    EMAIL_BACKEND = 'core.email_backend.ResendEmailBackend'
    RESEND_API_KEY = config('RESEND_API_KEY')
    DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='ChatApp <noreply@chatapp.com>')
    print(f"📧 Email configured for: Resend API ({DEFAULT_FROM_EMAIL})")
elif os.getenv('EMAIL_HOST'):
    # Production/Real SMTP email settings
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = f'ChatApp <{EMAIL_HOST_USER}>'
    print(f"📧 Email configured for: {EMAIL_HOST_USER}")
else:
    # Development mode - print emails to console only
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'ChatApp <noreply@chatapp.com>'
    print("📧 Email configured for: Console output only")

# Celery Configuration (Upstash Redis)
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
