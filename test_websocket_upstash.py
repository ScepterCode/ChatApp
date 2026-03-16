#!/usr/bin/env python
"""
Test WebSocket functionality with Upstash Redis.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import TestCase
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from chat.consumers import ChatConsumer
from accounts.models import CustomUser
from chat.models import Room, Membership
import json

async def test_websocket_with_upstash():
    """Test WebSocket consumer with Upstash Redis."""
    print("🧪 Testing WebSocket with Upstash Redis...")
    print("="*50)
    
    try:
        # Create test user
        user = await database_sync_to_async(CustomUser.objects.get_or_create)(
            username='testuser',
            defaults={'email': 'test@example.com'}
        )
        user = user[0]
        
        # Create test room
        room = await database_sync_to_async(Room.objects.get_or_create)(
            name='Test Room',
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
        
        if connected:
            print("✅ WebSocket connected successfully")
            
            # Receive welcome message
            welcome = await communicator.receive_json_from()
            print(f"✅ Received welcome: {welcome.get('message', 'N/A')}")
            
            # Send a test message
            await communicator.send_json_to({
                'type': 'chat_message',
                'content': 'Hello Upstash Redis!'
            })
            
            # Receive the message back
            response = await communicator.receive_json_from()
            print(f"✅ Message sent and received: {response.get('content', 'N/A')}")
            
            # Disconnect
            await communicator.disconnect()
            print("✅ WebSocket disconnected cleanly")
            
            return True
        else:
            print("❌ WebSocket connection failed")
            return False
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run WebSocket test."""
    print("🚀 WebSocket + Upstash Test")
    print("="*50)
    
    success = await test_websocket_with_upstash()
    
    print("\n" + "="*50)
    if success:
        print("🎉 WebSocket + Upstash working!")
    else:
        print("⚠️  WebSocket test failed")
    print("="*50)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())