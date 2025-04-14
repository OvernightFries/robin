"""
Initialize Redis cache with initial market data.
"""
import os
import redis
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_cache():
    """Initialize Redis cache with default values."""
    try:
        # Connect to Redis
        redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"))
        
        # Test connection
        redis_client.ping()
        logger.info("Connected to Redis successfully")
        
        # Initialize default market data
        default_data = {
            "timestamp": datetime.now().isoformat(),
            "status": "initialized",
            "cache_version": "1.0"
        }
        
        # Store in Redis
        redis_client.set("market_data", json.dumps(default_data))
        logger.info("Cache initialized successfully")
        
        return True
    except Exception as e:
        logger.error(f"Failed to initialize cache: {str(e)}")
        return False

if __name__ == "__main__":
    initialize_cache() 
