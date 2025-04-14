import os
import sys
import logging
from typing import List, Optional
import aiohttp
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get environment variables
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://ollama:11434')
MODEL_NAME = os.getenv('MODEL_NAME', 'llama3')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'nomic-embed-text')

async def get_embedding(text: str, session: Optional[aiohttp.ClientSession] = None) -> List[float]:
    """Get embedding for a given text using Ollama's embedding endpoint."""
    url = f"{OLLAMA_HOST}/api/embeddings"
    payload = {
        "model": EMBEDDING_MODEL,
        "prompt": text
    }
    
    try:
        if session is None:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('embedding', [])
                    else:
                        logger.error(f"Failed to get embedding: {response.status}")
                        return []
        else:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('embedding', [])
                else:
                    logger.error(f"Failed to get embedding: {response.status}")
                    return []
    except Exception as e:
        logger.error(f"Error getting embedding: {str(e)}")
        return []

async def test_embeddings():
    """Test the embeddings endpoint with a sample text."""
    test_text = "This is a test to verify the embeddings endpoint is working."
    embedding = await get_embedding(test_text)
    
    if embedding:
        logger.info("Embeddings endpoint is working correctly")
        logger.info(f"Generated embedding of length: {len(embedding)}")
        return True
    else:
        logger.error("Failed to get embedding from the endpoint")
        return False

async def main():
    """Main function to initialize and test embeddings."""
    logger.info("Starting embeddings initialization...")
    
    # Test the embeddings endpoint
    success = await test_embeddings()
    
    if success:
        logger.info("Embeddings initialization completed successfully")
        sys.exit(0)
    else:
        logger.error("Embeddings initialization failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 
