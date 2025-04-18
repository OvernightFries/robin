import os
import logging
from pinecone import Pinecone
from dotenv import load_dotenv
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)
load_dotenv()

_pinecone_client = None

def init_pinecone() -> Optional[Pinecone]:
    """Initialize Pinecone with API key and environment."""
    global _pinecone_client
    
    if _pinecone_client is not None:
        return _pinecone_client
        
    api_key = os.getenv("PINECONE_API_KEY")
    environment = os.getenv("PINECONE_ENVIRONMENT")
    
    if not api_key or not environment:
        logger.warning("Pinecone API key or environment not set, Pinecone features will be disabled")
        return None
    
    try:
        logger.info("Initializing Pinecone client...")
        _pinecone_client = Pinecone(
            api_key=api_key,
            environment=environment,
            timeout=10  # Set a reasonable timeout
        )
        logger.info("Pinecone client initialized successfully")
        return _pinecone_client
    except Exception as e:
        logger.error(f"Failed to initialize Pinecone: {str(e)}")
        return None

def get_pinecone_client() -> Optional[Pinecone]:
    """Get the Pinecone client instance."""
    return _pinecone_client

if __name__ == "__main__":
    init_pinecone() 
