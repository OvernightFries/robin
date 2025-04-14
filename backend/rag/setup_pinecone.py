import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

def init_pinecone():
    """Initialize Pinecone with API key and environment."""
    api_key = os.getenv("PINECONE_API_KEY")
    environment = os.getenv("PINECONE_ENVIRONMENT")
    
    if not api_key or not environment:
        raise ValueError("Pinecone API key and environment must be set in environment variables")
    
    pc = Pinecone(api_key=api_key)
    return pc

if __name__ == "__main__":
    init_pinecone() 
