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
try:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = Redis.from_url(
        redis_url,
        socket_timeout=5,
        socket_connect_timeout=5,
        retry_on_timeout=True,
        decode_responses=True
    )
    # Test connection
    redis_client.ping()
    logger.info("Redis connection established")
except Exception as e:
    logger.warning(f"Redis connection failed: {str(e)}")
    redis_client = None

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
