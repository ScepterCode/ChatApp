#!/usr/bin/env python
"""
Test Resend with real email address.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from accounts.models import CustomUser

def test_with_real_email():
    """Test password reset with your real email."""
    print("🧪 Testing Resend with your real email address...")
    
    # Your actual email from Resend error message
    real_email = "onyewuchiscepter@gmail.com"
    
    # Create or get test user with your real email
    user, created = CustomUser.objects.get_or_create(
        email=real_email,
        defaults={
            'username': 'onyewuchi',
            'first_name': 'Onyewuchi',
            'last_name': 'Scepter'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Created test user with email: {real_email}")
    else:
        print(f"✅ Using existing user with email: {real_email}")
    
    # Test the password reset API
    client = Client()
    response = client.post('/api/auth/password-reset/', {
        'email': real_email
    }, content_type='application/json')
    
    print(f"📊 Status: {response.status_code}")
    print(f"📧 Response: {response.json()}")
    
    if response.status_code == 200:
        print("🎉 SUCCESS! Check your email inbox!")
        print(f"📬 Email sent to: {real_email}")
        return True
    else:
        print("❌ Failed to send email")
        return False

if __name__ == '__main__':
    test_with_real_email()