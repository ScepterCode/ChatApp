#!/usr/bin/env python
"""
Start the Django server with minimal ASGI configuration (no auth middleware)
"""
import os
import sys
import django

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

def check_requirements():
    """Check if all required services are available"""
    print("🔍 Checking requirements...")
    
    # Check database connection
    try:
        django.setup()
        from django.db import connection
        connection.ensure_connection()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    return True

def run_server():
    """Run the ASGI server with minimal configuration"""
    print("🚀 Starting Django ASGI server with MINIMAL WebSocket support...")
    print("⚠️  WARNING: Authentication middleware disabled for testing")
    print("📡 Server will be available at: http://localhost:8000")
    print("🔌 WebSocket endpoint: ws://localhost:8000/ws/chat/<room_id>/")
    print("🛑 Press Ctrl+C to stop the server\n")
    
    try:
        from daphne.cli import CommandLineInterface
        args = ['-b', '0.0.0.0', '-p', '8000', 'core.asgi_minimal:application']
        CommandLineInterface().run(args)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")

if __name__ == '__main__':
    if check_requirements():
        run_server()
    else:
        print("❌ Requirements check failed. Please fix the issues above.")
        sys.exit(1)