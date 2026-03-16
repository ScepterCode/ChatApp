#!/usr/bin/env python
"""
Deep debugging for Upstash Redis connection issues.
"""
import os
import sys
import django
import time
import ssl

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
import redis
from urllib.parse import urlparse

def parse_redis_url():
    """Parse and analyze the Redis URL."""
    print("🔍 Analyzing Redis URL...")
    print("-" * 50)
    
    redis_url = settings.REDIS_URL
    parsed = urlparse(redis_url)
    
    print(f"📡 Full URL: {redis_url}")
    print(f"🌐 Scheme: {parsed.scheme}")
    print(f"🏠 Hostname: {parsed.hostname}")
    print(f"🔌 Port: {parsed.port}")
    print(f"👤 Username: {parsed.username}")
    print(f"🔑 Password: {'*' * len(parsed.password) if parsed.password else 'None'}")
    print(f"📂 Path: {parsed.path}")
    
    return parsed

def test_basic_connection():
    """Test basic Redis connection with different configurations."""
    print("\n🧪 Testing Basic Redis Connection...")
    print("-" * 50)
    
    redis_url = settings.REDIS_URL
    
    # Test 1: Basic connection
    print("1️⃣ Testing basic connection...")
    try:
        r = redis.from_url(redis_url)
        result = r.ping()
        print(f"✅ Basic connection successful: {result}")
        return r
    except Exception as e:
        print(f"❌ Basic connection failed: {e}")
    
    # Test 2: With explicit SSL
    print("\n2️⃣ Testing with explicit SSL...")
    try:
        r = redis.from_url(redis_url, ssl_cert_reqs=None)
        result = r.ping()
        print(f"✅ SSL connection successful: {result}")
        return r
    except Exception as e:
        print(f"❌ SSL connection failed: {e}")
    
    # Test 3: With SSL context
    print("\n3️⃣ Testing with SSL context...")
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        r = redis.from_url(redis_url, ssl_context=ssl_context)
        result = r.ping()
        print(f"✅ SSL context connection successful: {result}")
        return r
    except Exception as e:
        print(f"❌ SSL context connection failed: {e}")
    
    # Test 4: Manual connection parameters
    print("\n4️⃣ Testing with manual parameters...")
    try:
        parsed = urlparse(redis_url)
        r = redis.Redis(
            host=parsed.hostname,
            port=parsed.port,
            username=parsed.username,
            password=parsed.password,
            ssl=True,
            ssl_cert_reqs=None,
            decode_responses=True
        )
        result = r.ping()
        print(f"✅ Manual connection successful: {result}")
        return r
    except Exception as e:
        print(f"❌ Manual connection failed: {e}")
    
    # Test 5: With connection pool
    print("\n5️⃣ Testing with connection pool...")
    try:
        pool = redis.ConnectionPool.from_url(
            redis_url,
            max_connections=10,
            retry_on_timeout=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        r = redis.Redis(connection_pool=pool)
        result = r.ping()
        print(f"✅ Connection pool successful: {result}")
        return r
    except Exception as e:
        print(f"❌ Connection pool failed: {e}")
    
    return None

def test_redis_operations(redis_client):
    """Test various Redis operations."""
    print("\n🧪 Testing Redis Operations...")
    print("-" * 50)
    
    if not redis_client:
        print("❌ No Redis client available")
        return False
    
    try:
        # Test 1: Basic SET/GET
        print("1️⃣ Testing SET/GET...")
        test_key = f"chatapp:test:{int(time.time())}"
        test_value = "Hello Upstash!"
        
        redis_client.set(test_key, test_value, ex=60)
        retrieved = redis_client.get(test_key)
        
        if retrieved == test_value:
            print("✅ SET/GET working")
        else:
            print(f"❌ SET/GET failed: expected '{test_value}', got '{retrieved}'")
            return False
        
        # Test 2: List operations
        print("\n2️⃣ Testing LIST operations...")
        list_key = f"chatapp:list:{int(time.time())}"
        
        redis_client.lpush(list_key, "item1", "item2", "item3")
        length = redis_client.llen(list_key)
        items = redis_client.lrange(list_key, 0, -1)
        
        if length == 3 and len(items) == 3:
            print(f"✅ LIST operations working: {items}")
        else:
            print(f"❌ LIST operations failed: length={length}, items={items}")
            return False
        
        # Test 3: Hash operations
        print("\n3️⃣ Testing HASH operations...")
        hash_key = f"chatapp:hash:{int(time.time())}"
        
        redis_client.hset(hash_key, mapping={
            "field1": "value1",
            "field2": "value2",
            "field3": "value3"
        })
        
        hash_data = redis_client.hgetall(hash_key)
        if len(hash_data) == 3:
            print(f"✅ HASH operations working: {hash_data}")
        else:
            print(f"❌ HASH operations failed: {hash_data}")
            return False
        
        # Test 4: Pub/Sub (basic test)
        print("\n4️⃣ Testing PUB/SUB...")
        channel = f"chatapp:channel:{int(time.time())}"
        
        # Just test if we can publish (don't test subscribe as it's complex)
        result = redis_client.publish(channel, "test message")
        print(f"✅ PUB/SUB publish working: {result} subscribers")
        
        # Test 5: Expiration
        print("\n5️⃣ Testing EXPIRATION...")
        exp_key = f"chatapp:exp:{int(time.time())}"
        
        redis_client.set(exp_key, "expires soon", ex=2)
        ttl = redis_client.ttl(exp_key)
        
        if ttl > 0:
            print(f"✅ EXPIRATION working: TTL={ttl}s")
        else:
            print(f"❌ EXPIRATION failed: TTL={ttl}")
            return False
        
        # Cleanup
        redis_client.delete(test_key, list_key, hash_key, exp_key)
        print("\n✅ All Redis operations successful!")
        return True
        
    except Exception as e:
        print(f"❌ Redis operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_connection_stability():
    """Test connection stability over time."""
    print("\n🧪 Testing Connection Stability...")
    print("-" * 50)
    
    redis_url = settings.REDIS_URL
    
    try:
        r = redis.from_url(redis_url)
        
        print("Testing connection stability over 30 seconds...")
        for i in range(6):  # Test every 5 seconds for 30 seconds
            try:
                start_time = time.time()
                result = r.ping()
                end_time = time.time()
                latency = (end_time - start_time) * 1000  # Convert to ms
                
                print(f"✅ Ping {i+1}/6: {result} (latency: {latency:.2f}ms)")
                
                if i < 5:  # Don't sleep after the last iteration
                    time.sleep(5)
                    
            except Exception as e:
                print(f"❌ Ping {i+1}/6 failed: {e}")
                return False
        
        print("✅ Connection stability test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Connection stability test failed: {e}")
        return False

def test_channels_redis_config():
    """Test the Channels Redis configuration."""
    print("\n🧪 Testing Channels Redis Configuration...")
    print("-" * 50)
    
    try:
        from channels.layers import get_channel_layer
        from channels_redis.core import RedisChannelLayer
        
        # Get the channel layer
        channel_layer = get_channel_layer()
        print(f"📡 Channel layer type: {type(channel_layer).__name__}")
        
        if isinstance(channel_layer, RedisChannelLayer):
            print("✅ Using RedisChannelLayer")
            
            # Try to get the Redis connection from the channel layer
            try:
                # Access the internal Redis connection
                redis_connection = channel_layer.connection(0)
                print(f"✅ Channel layer Redis connection: {redis_connection}")
                return True
            except Exception as e:
                print(f"⚠️ Channel layer Redis connection issue: {e}")
                return False
        else:
            print("❌ Not using RedisChannelLayer")
            return False
            
    except Exception as e:
        print(f"❌ Channels Redis test failed: {e}")
        return False

def main():
    """Run comprehensive Redis debugging."""
    print("🚀 Redis Deep Debug Suite")
    print("=" * 60)
    print("Debugging Upstash Redis connection issues...")
    print("=" * 60)
    
    # Step 1: Parse URL
    parsed_url = parse_redis_url()
    
    # Step 2: Test connections
    redis_client = test_basic_connection()
    
    # Step 3: Test operations (if connection works)
    operations_ok = False
    if redis_client:
        operations_ok = test_redis_operations(redis_client)
    
    # Step 4: Test stability (if operations work)
    stability_ok = False
    if operations_ok:
        stability_ok = test_connection_stability()
    
    # Step 5: Test Channels configuration
    channels_ok = test_channels_redis_config()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Debug Results Summary:")
    print("-" * 60)
    print(f"🔗 Redis Connection: {'✅ Working' if redis_client else '❌ Failed'}")
    print(f"⚙️ Redis Operations: {'✅ Working' if operations_ok else '❌ Failed'}")
    print(f"🔄 Connection Stability: {'✅ Stable' if stability_ok else '❌ Unstable'}")
    print(f"📡 Channels Configuration: {'✅ Working' if channels_ok else '❌ Failed'}")
    
    if redis_client and operations_ok:
        print("\n🎉 Redis is working! Connection issues may be intermittent.")
        print("💡 Recommendation: Use connection pooling and retry logic.")
    elif redis_client:
        print("\n⚠️ Redis connects but operations fail. Check permissions.")
    else:
        print("\n❌ Redis connection completely failed. Check:")
        print("   • Network connectivity")
        print("   • Upstash credentials")
        print("   • SSL/TLS configuration")
        print("   • Firewall settings")
    
    print("=" * 60)

if __name__ == '__main__':
    main()