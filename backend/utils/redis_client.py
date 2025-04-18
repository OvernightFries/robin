import os
import logging
import redis
from typing import Optional

logger = logging.getLogger(__name__)

def init_redis() -> Optional[redis.Redis]:
    """Initialize Redis client with proper configuration for Google Cloud Memorystore."""
    try:
        # Get Redis connection details from environment variables
        redis_host = os.getenv("REDIS_HOST", "localhost")  # Default to localhost for local development
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD")  # Optional for local development
        
        logger.info(f"Attempting to connect to Redis at {redis_host}:{redis_port}")
        
        # Determine if we're using Memorystore (production) or local Redis
        is_memorystore = redis_host not in ["localhost", "127.0.0.1"]
        
        if is_memorystore:
            # Google Cloud Memorystore configuration
            logger.info("Configuring for Google Cloud Memorystore")
            client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                ssl=False,  # SSL not required for this instance
                socket_timeout=10,  # Increased timeout
                socket_connect_timeout=10,  # Increased timeout
                retry_on_timeout=True,
                decode_responses=True
            )
        else:
            # Local Redis configuration
            logger.info("Configuring for local Redis")
            client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                decode_responses=True
            )
        
        # Test the connection
        client.ping()
        logger.info("Redis connection established successfully")
        return client
        
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {str(e)}")
        return None 
