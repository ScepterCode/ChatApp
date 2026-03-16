#!/usr/bin/env python
"""
Test script for email functionality.
Tests both console and Resend email backends.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from accounts.models import CustomUser
import requests

def test_basic_email():
    """Test basic email sending."""
    print("🧪 Testing basic email functionality...")
    
    try:
        send_mail(
            subject='Test Email from ChatApp',
            message='This is a test email to verify email configuration.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['test@example.com'],
            fail_silently=False,
        )
        print("✅ Basic email test successful!")
        return True
    except Exception as e:
        print(f"❌ Basic email test failed: {e}")
        return False

def test_html_email():
    """Test HTML email sending."""
    print("🧪 Testing HTML email functionality...")
    
    try:
        text_content = "This is a test HTML email from ChatApp."
        html_content = """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #4F46E5;">Test HTML Email</h2>
            <p>This is a <strong>test HTML email</strong> from ChatApp.</p>
            <div style="background-color: #f0f0f0; padding: 20px; border-radius: 5px;">
                <p>HTML formatting is working correctly!</p>
            </div>
        </div>
        """
        
        msg = EmailMultiAlternatives(
            subject='Test HTML Email from ChatApp',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=['test@example.com'],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        print("✅ HTML email test successful!")
        return True
    except Exception as e:
        print(f"❌ HTML email test failed: {e}")
        return False

def test_password_reset_email():
    """Test password reset email functionality."""
    print("🧪 Testing password reset email...")
    
    try:
        # Create a test user if it doesn't exist
        user, created = CustomUser.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"✅ Created test user: {user.username}")
        else:
            print(f"✅ Using existing test user: {user.username}")
        
        # Test the password reset endpoint
        from django.test import Client
        client = Client()
        
        response = client.post('/api/auth/password-reset/', {
            'email': user.email
        }, content_type='application/json')
        
        if response.status_code == 200:
            print("✅ Password reset email test successful!")
            print(f"📧 Response: {response.json()}")
            return True
        else:
            print(f"❌ Password reset failed with status {response.status_code}")
            print(f"📧 Response: {response.json()}")
            return False
            
    except Exception as e:
        print(f"❌ Password reset email test failed: {e}")
        return False

def main():
    """Run all email tests."""
    print("="*60)
    print("🚀 ChatApp Email Testing Suite")
    print("="*60)
    
    print(f"📧 Email Backend: {settings.EMAIL_BACKEND}")
    print(f"📧 Default From Email: {settings.DEFAULT_FROM_EMAIL}")
    
    if hasattr(settings, 'RESEND_API_KEY'):
        print(f"📧 Resend API Key: {'✅ Configured' if settings.RESEND_API_KEY != 'your-resend-api-key-here' else '❌ Not configured'}")
    
    print("\n" + "="*60)
    
    # Run tests
    tests = [
        test_basic_email,
        test_html_email,
        test_password_reset_email,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("="*60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All email tests passed!")
    else:
        print("⚠️  Some email tests failed. Check configuration.")
    
    print("="*60)

if __name__ == '__main__':
    main()