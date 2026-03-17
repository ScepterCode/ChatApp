#!/usr/bin/env python3
"""
WebSocket Connection Test for Render Deployment
Run this script to test if WebSocket connections work on Render
"""

import asyncio
import websockets
import json
import sys
from urllib.parse import urlencode

async def test_websocket_connection():
    """Test WebSocket connection to Render deployment"""
    
    # Test configuration
    RENDER_URL = "wss://chatapp-1-kctm.onrender.com"
    TEST_ROOM = "test"
    
    # You'll need to get a real JWT token from your login API
    # For now, we'll test without authentication
    TEST_TOKEN = "your_jwt_token_here"  # Replace with real token
    
    # Build WebSocket URL
    params = {"token": TEST_TOKEN} if TEST_TOKEN != "your_jwt_token_here" else {}
    query_string = urlencode(params)
    ws_url = f"{RENDER_URL}/ws/chat/{TEST_ROOM}/"
    if query_string:
        ws_url += f"?{query_string}"
    
    print(f"🔌 Testing WebSocket connection to: {ws_url}")
    
    try:
        # Test connection with timeout
        async with websockets.connect(
            ws_url,
            timeout=10,
            ping_interval=20,
            ping_timeout=10
        ) as websocket:
            print("✅ WebSocket connection successful!")
            
            # Send a test message
            test_message = {
                "type": "chat_message",
                "content": "Hello from test script!"
            }
            
            await websocket.send(json.dumps(test_message))
            print("📤 Test message sent")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                print(f"📥 Received: {data}")
                
                if data.get('type') == 'system_message':
                    print("✅ WebSocket is working correctly!")
                    return True
                    
            except asyncio.TimeoutError:
                print("⏰ No response received within 5 seconds")
                
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ WebSocket connection closed: {e}")
        return False
        
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ WebSocket connection failed with status: {e}")
        if e.status_code == 403:
            print("   This might be an authentication issue")
        elif e.status_code == 404:
            print("   WebSocket endpoint not found")
        return False
        
    except Exception as e:
        print(f"❌ WebSocket connection error: {e}")
        return False

async def test_http_endpoints():
    """Test HTTP endpoints to verify deployment"""
    import aiohttp
    
    base_url = "https://chatapp-1-kctm.onrender.com"
    
    async with aiohttp.ClientSession() as session:
        # Test health check
        try:
            async with session.get(f"{base_url}/health/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check: {data}")
                else:
                    print(f"❌ Health check failed: {response.status}")
        except Exception as e:
            print(f"❌ Health check error: {e}")
        
        # Test WebSocket info endpoint
        try:
            async with session.get(f"{base_url}/ws-test/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ WebSocket test endpoint: {data}")
                else:
                    print(f"❌ WebSocket test endpoint failed: {response.status}")
        except Exception as e:
            print(f"❌ WebSocket test endpoint error: {e}")

async def main():
    """Main test function"""
    print("🚀 Starting Render WebSocket Tests")
    print("=" * 50)
    
    # Test HTTP endpoints first
    print("\n📡 Testing HTTP endpoints...")
    await test_http_endpoints()
    
    # Test WebSocket connection
    print("\n🔌 Testing WebSocket connection...")
    success = await test_websocket_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! WebSocket is working on Render.")
    else:
        print("❌ WebSocket tests failed. Check the configuration.")
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure you have a valid JWT token")
        print("2. Check Render logs for WebSocket errors")
        print("3. Verify Redis (Upstash) is connected")
        print("4. Try upgrading to Render's paid plan for better WebSocket support")

if __name__ == "__main__":
    # Install required packages if not available
    try:
        import websockets
        import aiohttp
    except ImportError:
        print("❌ Missing required packages. Install with:")
        print("pip install websockets aiohttp")
        sys.exit(1)
    
    asyncio.run(main())