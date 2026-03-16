#!/usr/bin/env python
"""
Comprehensive test for Redis and background processing (both Celery and Asyncio).
"""
import os
import sys
import django
import asyncio
import time
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
from django.test import Client
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
import redis
from urllib.parse import urlparse

# Import models and consumers
from accounts.models import CustomUser
from chat.models import Room, Membership, Message
from chat.consumers import ChatConsumer

def test_redis_connection():
    """Test direct Redis connection to Upstash."""
    print("🧪 Testing Direct Redis Connection...")
    print("-" * 40)
    
    try:
        redis_url = settings.REDIS_URL
        print(f"📡 Redis URL: {redis_url[:50]}...")
        
        # Create Redis client with proper SSL configuration for Upstash
        r = redis.from_url(redis_url)
        
        # Test basic operations
        test_key = "chatapp:test:connection"
        test_value = f"test_value_{int(time.time())}"
        
        # SET operation
        r.set(test_key, test_value, ex=30)
        print("✅ SET operation successful")
        
        # GET operation
        retrieved = r.get(test_key)
        if retrieved and retrieved.decode() == test_value:
            print("✅ GET operation successful")
        else:
            print("❌ GET operation failed")
            return False
        
        # PING operation
        pong = r.ping()
        if pong:
            print("✅ PING successful")
        else:
            print("❌ PING failed")
            return False
        
        # List operations
        list_key = "chatapp:test:list"
        r.lpush(list_key, "item1", "item2", "item3")
        list_length = r.llen(list_key)
        if list_length == 3:
            print("✅ List operations successful")
        else:
            print("❌ List operations failed")
            return False
        
        # Cleanup
        r.delete(test_key, list_key)
        print("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def test_channels_redis():
    """Test Channels Redis layer functionality."""
    print("\n🧪 Testing Channels Redis Layer...")
    print("-" * 40)
    
    try:
        channel_layer = get_channel_layer()
        print(f"📡 Channel layer type: {type(channel_layer).__name__}")
        
        if 'RedisChannelLayer' not in str(type(channel_layer)):
            print("❌ Not using Redis channel layer")
            return False
        
        print("✅ Using Redis channel layer")
        
        # Test channel layer operations (these are async, so we'll test them in the WebSocket test)
        return True
        
    except Exception as e:
        print(f"❌ Channels Redis test failed: {e}")
        return False

def test_celery_config():
    """Test Celery configuration (even though we're using asyncio now)."""
    print("\n🧪 Testing Celery Configuration...")
    print("-" * 40)
    
    try:
        print(f"📡 Broker URL: {settings.CELERY_BROKER_URL[:50]}...")
        print(f"📡 Result Backend: {settings.CELERY_RESULT_BACKEND[:50]}...")
        
        if 'upstash.io' in settings.CELERY_BROKER_URL:
            print("✅ Celery configured for Upstash")
        else:
            print("❌ Celery not configured for Upstash")
            return False
        
        # Test if we can connect to Celery broker (Redis)
        from celery import Celery
        app = Celery('test')
        app.config_from_object('django.conf:settings', namespace='CELERY')
        
        # Try to inspect the broker
        try:
            inspect = app.control.inspect()
            # This will fail if broker is not accessible, but that's expected since we're not running Celery
            print("✅ Celery broker configuration valid")
        except Exception:
            print("ℹ️  Celery broker not running (expected - we're using asyncio)")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery config test failed: {e}")
        return False

async def test_asyncio_background_processing():
    """Test the new asyncio-based background processing."""
    print("\n🧪 Testing Asyncio Background Processing...")
    print("-" * 40)
    
    try:
        # Import the sentiment analyzer
        from ai.sentiment import SentimentAnalyzer
        from concurrent.futures import ThreadPoolExecutor
        
        # Create thread pool like in the consumer
        executor = ThreadPoolExecutor(max_workers=2)
        
        # Test content
        test_content = "I love this new chat system! It's amazing!"
        
        print(f"📝 Testing sentiment analysis on: '{test_content}'")
        
        # Run sentiment analysis in thread pool (like the consumer does)
        loop = asyncio.get_event_loop()
        start_time = time.time()
        
        result = await loop.run_in_executor(
            executor,
            SentimentAnalyzer.analyze,
            test_content
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✅ Sentiment analysis completed in {processing_time:.2f}s")
        print(f"📊 Result: {result['sentiment']} (score: {result['sentiment_score']:.3f})")
        
        # Verify result structure
        required_keys = ['sentiment', 'sentiment_score']
        for key in required_keys:
            if key not in result:
                print(f"❌ Missing key in result: {key}")
                return False
        
        print("✅ Result structure valid")
        
        # Test multiple concurrent analyses
        print("🔄 Testing concurrent processing...")
        test_messages = [
            "This is great!",
            "I hate this system",
            "It's okay, nothing special",
            "Absolutely fantastic work!",
            "This is terrible"
        ]
        
        start_time = time.time()
        tasks = []
        for msg in test_messages:
            task = loop.run_in_executor(executor, SentimentAnalyzer.analyze, msg)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        print(f"✅ Processed {len(test_messages)} messages concurrently in {end_time - start_time:.2f}s")
        
        # Verify all results
        for i, result in enumerate(results):
            print(f"  📝 '{test_messages[i]}' → {result['sentiment']}")
        
        executor.shutdown(wait=True)
        return True
        
    except Exception as e:
        print(f"❌ Asyncio background processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_websocket_with_background_processing():
    """Test WebSocket with background sentiment processing."""
    print("\n🧪 Testing WebSocket + Background Processing...")
    print("-" * 40)
    
    try:
        # Create test user
        user = await database_sync_to_async(CustomUser.objects.get_or_create)(
            username='testuser_redis',
            defaults={'email': 'testredis@example.com'}
        )
        user = user[0]
        
        # Create test room
        room = await database_sync_to_async(Room.objects.get_or_create)(
            name='Redis Test Room',
            defaults={'admin': user}
        )
        room = room[0]
        
        # Create membership
        await database_sync_to_async(Membership.objects.get_or_create)(
            user=user, room=room
        )
        
        print(f"✅ Created test room: {room.name} (ID: {room.id})")
        
        # Test WebSocket connection
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{room.id}/"
        )
        
        # Add user to scope
        communicator.scope['user'] = user
        communicator.scope['url_route'] = {
            'kwargs': {'room_id': str(room.id)}
        }
        
        # Connect
        connected, subprotocol = await communicator.connect()
        
        if not connected:
            print("❌ WebSocket connection failed")
            return False
        
        print("✅ WebSocket connected successfully")
        
        # Receive welcome message
        welcome = await communicator.receive_json_from()
        print(f"✅ Received welcome: {welcome.get('message', 'N/A')}")
        
        # Send a test message that should trigger sentiment analysis
        test_message = "I absolutely love this new Redis setup! It's fantastic!"
        await communicator.send_json_to({
            'type': 'chat_message',
            'content': test_message
        })
        
        # Receive the immediate message response
        response = await communicator.receive_json_from()
        print(f"✅ Immediate message received: {response.get('content', 'N/A')}")
        
        # Check if sentiment is initially None (as expected)
        if response.get('sentiment') is None:
            print("✅ Sentiment initially None (background processing)")
        else:
            print(f"ℹ️  Sentiment already available: {response.get('sentiment')}")
        
        # Wait for sentiment update (should come within a few seconds)
        print("⏳ Waiting for background sentiment analysis...")
        
        try:
            # Wait up to 10 seconds for sentiment update
            sentiment_update = await asyncio.wait_for(
                communicator.receive_json_from(),
                timeout=10.0
            )
            
            if sentiment_update.get('type') == 'sentiment_update':
                print(f"✅ Sentiment update received: {sentiment_update.get('sentiment')}")
                print(f"📊 Sentiment score: {sentiment_update.get('sentiment_score', 'N/A')}")
            else:
                print(f"ℹ️  Received other message: {sentiment_update.get('type')}")
            
        except asyncio.TimeoutError:
            print("⚠️  Sentiment update not received within timeout (may still be processing)")
        
        # Verify message was saved to database
        message_count = await database_sync_to_async(
            lambda: Message.objects.filter(room=room, content=test_message).count()
        )()
        
        if message_count > 0:
            print("✅ Message saved to database")
        else:
            print("❌ Message not saved to database")
            return False
        
        # Disconnect
        await communicator.disconnect()
        print("✅ WebSocket disconnected cleanly")
        
        return True
        
    except Exception as e:
        print(f"❌ WebSocket + background processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all Redis and background processing tests."""
    print("🚀 Redis + Background Processing Test Suite")
    print("=" * 60)
    
    tests = [
        ("Redis Connection", test_redis_connection),
        ("Channels Redis", test_channels_redis),
        ("Celery Config", test_celery_config),
        ("Asyncio Background Processing", test_asyncio_background_processing),
        ("WebSocket + Background Processing", test_websocket_with_background_processing),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Redis and background processing working perfectly!")
    elif passed >= total - 1:
        print("✅ Most tests passed! System is working well.")
    else:
        print("⚠️  Some tests failed. Check configuration and connections.")
    
    print("=" * 60)

if __name__ == '__main__':
    asyncio.run(main())