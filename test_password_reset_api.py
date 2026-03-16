#!/usr/bin/env python
"""
Test the password reset API endpoint.
"""
import requests
import json

def test_password_reset_api():
    """Test the password reset API endpoint."""
    print("🧪 Testing Password Reset API")
    print("="*50)
    
    # API endpoint
    url = "http://localhost:8000/api/auth/password-reset/"
    
    # Test data
    test_email = "test@example.com"
    
    # Request payload
    payload = {
        "email": test_email
    }
    
    print(f"📧 Testing with email: {test_email}")
    print(f"🔗 Endpoint: {url}")
    
    try:
        # Make the request
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Password reset request successful!")
            print(f"📝 Response: {json.dumps(data, indent=2)}")
            
            # If in DEBUG mode, the response includes the reset URL
            if 'reset_url' in data:
                print(f"\n🔗 Reset URL: {data['reset_url']}")
                print("💡 In production, this would be sent via email only")
            
            return True
        else:
            print(f"❌ Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"📝 Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"📝 Response text: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure Django server is running")
        print("💡 Start server with: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def show_usage_instructions():
    """Show instructions for testing the API."""
    print("\n📋 How to Test Password Reset:")
    print("="*50)
    print("1. Start Django server:")
    print("   python manage.py runserver")
    print()
    print("2. Test with curl:")
    print('   curl -X POST http://localhost:8000/api/auth/password-reset/ \\')
    print('        -H "Content-Type: application/json" \\')
    print('        -d \'{"email": "test@example.com"}\'')
    print()
    print("3. Test with your frontend:")
    print("   POST /api/auth/password-reset/")
    print("   Body: {\"email\": \"user@example.com\"}")
    print()
    print("4. Check email output:")
    print("   - Console mode: Check terminal output")
    print("   - Resend mode: Check your email inbox")

if __name__ == '__main__':
    print("🚀 Password Reset API Tester")
    print("="*50)
    
    success = test_password_reset_api()
    
    if not success:
        show_usage_instructions()
    
    print("\n" + "="*50)
    if success:
        print("🎉 Password reset API is working!")
    else:
        print("⚠️  Check server status and try again")