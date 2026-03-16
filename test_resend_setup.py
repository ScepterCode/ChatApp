#!/usr/bin/env python
"""
Test script to verify Resend setup and configuration.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
from decouple import config

def check_resend_config():
    """Check if Resend is properly configured."""
    print("🔍 Checking Resend Configuration...")
    print("="*50)
    
    # Check if Resend API key is set
    resend_key = config('RESEND_API_KEY', default=None)
    if resend_key and resend_key != 'your-resend-api-key-here':
        print(f"✅ RESEND_API_KEY: Configured (starts with: {resend_key[:8]}...)")
        api_key_valid = True
    else:
        print("❌ RESEND_API_KEY: Not configured or using placeholder")
        api_key_valid = False
    
    # Check default from email
    from_email = config('DEFAULT_FROM_EMAIL', default=None)
    if from_email and from_email != 'onboarding@resend.dev':
        print(f"✅ DEFAULT_FROM_EMAIL: {from_email}")
        from_email_valid = True
    else:
        print("⚠️  DEFAULT_FROM_EMAIL: Using default (onboarding@resend.dev)")
        from_email_valid = True  # Default is actually valid
    
    # Check email backend
    print(f"📧 EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    
    if 'ResendEmailBackend' in settings.EMAIL_BACKEND:
        print("✅ Using Resend email backend")
        backend_valid = True
    else:
        print("ℹ️  Using console/SMTP email backend")
        backend_valid = False
    
    print("="*50)
    
    if api_key_valid and backend_valid:
        print("🎉 Resend is properly configured!")
        return True
    elif not api_key_valid:
        print("⚠️  To use Resend, update your .env file:")
        print("   RESEND_API_KEY=re_your_actual_api_key")
        print("   DEFAULT_FROM_EMAIL=your-domain@resend.dev")
        return False
    else:
        print("ℹ️  Resend configuration incomplete")
        return False

def test_resend_import():
    """Test if resend package is properly installed."""
    print("\n🔍 Testing Resend Package...")
    print("="*50)
    
    try:
        import resend
        print("✅ Resend package imported successfully")
        print(f"📦 Resend version: {resend.__version__ if hasattr(resend, '__version__') else 'Unknown'}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import resend: {e}")
        print("💡 Install with: pip install resend")
        return False

def show_setup_instructions():
    """Show setup instructions for Resend."""
    print("\n📋 Resend Setup Instructions:")
    print("="*50)
    print("1. Sign up at https://resend.com")
    print("2. Get your API key from the dashboard")
    print("3. Add a verified domain (or use onboarding@resend.dev for testing)")
    print("4. Update your .env file:")
    print("   RESEND_API_KEY=re_your_actual_api_key")
    print("   DEFAULT_FROM_EMAIL=your-domain@resend.dev")
    print("5. Restart your Django server")
    print("\n🧪 Test with:")
    print("   python test_email.py")
    print("   POST /api/auth/password-reset/ with a real email")

def main():
    """Run Resend configuration check."""
    print("🚀 Resend Configuration Checker")
    print("="*50)
    
    # Test package import
    package_ok = test_resend_import()
    
    # Check configuration
    config_ok = check_resend_config()
    
    if not package_ok or not config_ok:
        show_setup_instructions()
    
    print("\n" + "="*50)
    if package_ok and config_ok:
        print("🎉 Ready to send emails with Resend!")
    else:
        print("⚠️  Setup incomplete - see instructions above")

if __name__ == '__main__':
    main()