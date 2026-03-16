from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/chat/', include('chat.urls')),
    
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
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT or os.path.join(settings.BASE_DIR, 'static'))
