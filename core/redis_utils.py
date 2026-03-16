# core/redis_utils.py
"""
Redis utilities with connection pooling and retry logic for Upstash.
"""
import redis
import time
import logging
from urllib.parse import urlparse
from django.conf import settings
from functools import wraps

logger = logging.getLogger(__name__)

class UpstashRedisClient:
    """
    Redis client optimized for Upstash with connection pooling and retry logic.
    """
    
    def __init__(self):
        self._pool = None
        self._client = None
        self._setup_connection()
    
    def _setup_connection(self):
        """Setup Redis connection with proper configuration for Upstash."""
        try:
            redis_url = settings.REDIS_URL
            parsed = urlparse(redis_url)
            
            # Use the working connection method
            self._client = redis.Redis(
                host=parsed.hostname,
                port=parsed.port,
                username=parsed.username,
                password=parsed.password,
                ssl=True,
                ssl_check_hostname=False,
                decode_responses=True,
                socket_timeout=10,
                socket_connect_timeout=10,
                retry_on_timeout=True,
            )
            
            logger.info("✅ Upstash Redis connection created successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup Redis connection: {e}")
            raise
    
    def get_client(self):
        """Get Redis client with connection validation."""
        if not self._client:
            self._setup_connection()
        return self._client
    
    def ping(self):
        """Test connection with retry logic."""
        return self._execute_with_retry(lambda: self._client.ping())
    
    def _execute_with_retry(self, operation, max_retries=3, delay=1):
        """Execute Redis operation with retry logic."""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return operation()
            except (redis.ConnectionError, redis.TimeoutError) as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger.warning(f"Redis operation failed (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(delay * (attempt + 1))  # Exponential backoff
                    # Try to reconnect
                    try:
                        self._setup_connection()
                    except Exception:
                        pass
                else:
                    logger.error(f"Redis operation failed after {max_retries} attempts: {e}")
        
        raise last_exception

# Global Redis client instance
_redis_client = None

def get_redis_client():
    """Get the global Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = UpstashRedisClient()
    return _redis_client.get_client()

def redis_retry(max_retries=3, delay=1):
    """Decorator for Redis operations with retry logic."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (redis.ConnectionError, redis.TimeoutError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Redis operation {func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}")
                        time.sleep(delay * (attempt + 1))
                    else:
                        logger.error(f"Redis operation {func.__name__} failed after {max_retries} attempts: {e}")
            
            raise last_exception
        return wrapper
    return decorator

# Example usage functions
@redis_retry()
def set_cache(key, value, expire=3600):
    """Set cache value with retry logic."""
    client = get_redis_client()
    return client.set(key, value, ex=expire)

@redis_retry()
def get_cache(key):
    """Get cache value with retry logic."""
    client = get_redis_client()
    return client.get(key)

@redis_retry()
def delete_cache(key):
    """Delete cache value with retry logic."""
    client = get_redis_client()
    return client.delete(key)