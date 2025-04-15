import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Ollama configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://35.202.133.28:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

def initialize_embeddings():
    """Initialize the embeddings model."""
    try:
        logger.info("Starting embeddings initialization...")
        
        # Test the embeddings endpoint
        import requests
        response = requests.post(
            f"{OLLAMA_HOST}/api/embeddings",
            json={
                "model": EMBEDDING_MODEL,
                "prompt": "test"
            }
        )
        response.raise_for_status()
        
        # Check the embedding length
        embedding = response.json()["embedding"]
        logger.info(f"Embeddings endpoint is working correctly")
        logger.info(f"Generated embedding of length: {len(embedding)}")
        
        logger.info("Embeddings initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing embeddings: {str(e)}")
        return False

if __name__ == "__main__":
    initialize_embeddings() 
