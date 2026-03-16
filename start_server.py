#!/usr/bin/env python
"""
Start the Django server with ASGI support for WebSockets
"""
import os
import sys
import django
import subprocess
import time

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

def check_requirements():
    """Check if all required services are available"""
    print("🔍 Checking requirements...")
    
    # Check if Redis is running (for Celery)
    try:
        import redis
        r = redis.Redis(host='127.0.0.1', port=6379, db=0)
        r.ping()
        print("✅ Redis is running")
    except Exception as e:
        print(f"⚠️  Redis not available: {e}")
        print("   Celery tasks won't work, but WebSockets will still function")
    
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
    """Run the ASGI server with Daphne"""
    print("🚀 Starting Django ASGI server with WebSocket support...")
    print("📡 Server will be available at: http://localhost:8000")
    print("🔌 WebSocket endpoint: ws://localhost:8000/ws/chat/<room_id>/")
    print("\n💡 To test WebSocket connection, run: python test_websocket_simple.py")
    print("🛑 Press Ctrl+C to stop the server\n")
    
    try:
        from daphne.cli import CommandLineInterface
        args = ['-b', '0.0.0.0', '-p', '8000', 'core.asgi:application']
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