#!/usr/bin/env python
"""
Test Upstash Redis connection and functionality.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
import redis
from urllib.parse import urlparse

def test_redis_connection():
    """Test basic Redis connection to Upstash."""
    print("🧪 Testing Upstash Redis Connection...")
    print("="*50)
    
    redis_url = settings.REDIS_URL
    print(f"📡 Redis URL: {redis_url[:50]}...")
    
    try:
        # Parse the Redis URL
        parsed = urlparse(redis_url)
        print(f"🌐 Host: {parsed.hostname}")
        print(f"🔌 Port: {parsed.port}")
        print(f"🔑 Auth: {'✅ Yes' if parsed.password else '❌ No'}")
        
        # Create Redis client
        r = redis.from_url(redis_url)
        
        # Test basic operations
        print("\n🔍 Testing Redis operations...")
        
        # Test SET/GET
        test_key = "chatapp:test"
        test_value = "Hello Upstash!"
        
        r.set(test_key, test_value, ex=60)  # Expire in 60 seconds
        retrieved = r.get(test_key)
        
        if retrieved and retrieved.decode() == test_value:
            print("✅ SET/GET operations working")
        else:
            print("❌ SET/GET operations failed")
            return False
        
        # Test PING
        pong = r.ping()
        if pong:
            print("✅ PING successful")
        else:
            print("❌ PING failed")
            return False
        
        # Test Redis info
        info = r.info()
        print(f"✅ Redis version: {info.get('redis_version', 'Unknown')}")
        print(f"✅ Connected clients: {info.get('connected_clients', 'Unknown')}")
        
        # Clean up
        r.delete(test_key)
        print("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def test_channels_redis():
    """Test Channels Redis layer."""
    print("\n🧪 Testing Channels Redis Layer...")
    print("="*50)
    
    try:
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        print(f"📡 Channel layer: {type(channel_layer).__name__}")
        
        if 'RedisChannelLayer' in str(type(channel_layer)):
            print("✅ Using Redis channel layer")
            return True
        else:
            print("❌ Not using Redis channel layer")
            return False
            
    except Exception as e:
        print(f"❌ Channels test failed: {e}")
        return False

def test_celery_config():
    """Test Celery configuration."""
    print("\n🧪 Testing Celery Configuration...")
    print("="*50)
    
    try:
        print(f"📡 Broker URL: {settings.CELERY_BROKER_URL[:50]}...")
        print(f"📡 Result Backend: {settings.CELERY_RESULT_BACKEND[:50]}...")
        
        if 'upstash.io' in settings.CELERY_BROKER_URL:
            print("✅ Celery configured for Upstash")
            return True
        else:
            print("❌ Celery not configured for Upstash")
            return False
            
    except Exception as e:
        print(f"❌ Celery config test failed: {e}")
        return False

def main():
    """Run all Redis tests."""
    print("🚀 Upstash Redis Test Suite")
    print("="*50)
    
    tests = [
        ("Redis Connection", test_redis_connection),
        ("Channels Redis", test_channels_redis),
        ("Celery Config", test_celery_config),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}:")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "="*50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Upstash Redis is working!")
    else:
        print("⚠️  Some tests failed. Check configuration.")
    
    print("="*50)

if __name__ == '__main__':
    main()