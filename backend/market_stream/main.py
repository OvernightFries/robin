"""
Market Stream Service - Handles real-time market data streaming
"""
import os
import asyncio
import logging
from fastapi import FastAPI, WebSocket
from redis import Redis 
from typing import Dict, Any
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI()

# Initialize Redis with retry logic
redis_client = None

async def init_redis():
    global redis_client
    try:
        # Get Redis connection details from environment variables
        redis_host = os.getenv("REDIS_HOST", "localhost")  # Default to localhost for local development
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD")  # Optional for local development
        
        logger.info(f"Attempting to connect to Redis at {redis_host}:{redis_port}")
        
        # Determine if we're using Memorystore (production) or local Redis
        is_memorystore = redis_host != "localhost" and redis_host != "127.0.0.1"
        
        if is_memorystore:
            # Google Cloud Memorystore configuration
            logger.info("Configuring for Google Cloud Memorystore")
            redis_client = Redis(
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
            redis_client = Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                decode_responses=True
            )
        
        # Test the connection with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Testing Redis connection (attempt {attempt + 1}/{max_retries})")
                redis_client.ping()
                logger.info("Redis connection established successfully")
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"Redis connection attempt {attempt + 1} failed: {str(e)}")
                await asyncio.sleep(1)  # Wait before retrying
                
    except Exception as e:
        logger.error(f"Redis connection failed after all retries: {str(e)}")
        redis_client = None

@app.on_event("startup")
async def startup_event():
    await init_redis()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        if redis_client:
            redis_client.ping()
            return {"status": "healthy", "redis": "connected"}
        return {"status": "healthy", "redis": "not_connected", "warning": "Redis not configured"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "healthy", "redis": "not_connected", "warning": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for streaming market data."""
    await websocket.accept()
    try:
        while True:
            if redis_client:
                try:
                    market_data = redis_client.get("market_data")
                    if market_data:
                        await websocket.send_text(market_data)
                except Exception as e:
                    logger.error(f"Redis error: {str(e)}")
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port) 
