from pinecone import Pinecone
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
import aiohttp
import json
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class MarketVectorStore:
    def __init__(self):
        try:
            self.pc = Pinecone(
                api_key=os.getenv("PINECONE_API_KEY"),
                timeout=30  # Increased timeout for initialization
            )
            self.index_name = os.getenv("PINECONE_INDEX_NAME", "robindocs")
            
            # Check if index exists
            if self.index_name not in self.pc.list_indexes().names():
                logger.warning(f"Pre-trained index {self.index_name} not found. Some features may be limited.")
                self.index = None
            else:
                self.index = self.pc.Index(self.index_name)
                logger.info(f"Successfully connected to pre-trained index {self.index_name}")
            
            self.embedding_model = "nomic-embed-text"
        except Exception as e:
            logger.error(f"Error initializing MarketVectorStore: {e}")
            self.index = None
            # Don't raise the exception, allow degraded operation

    async def search_similar_market_conditions(self, query: str, symbol: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar market conditions in the vector store."""
        try:
            if not self.index:
                logger.warning("Vector store not available, skipping similarity search")
                return []
                
            # Get query embedding using nomic-embed-text
            query_vector = await self._get_embedding(query)
            
            # Search in Pinecone
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                filter={"symbol": symbol} if symbol != "general" else None
            )
            
            return results.matches
        except Exception as e:
            logger.error(f"Error in search_similar_market_conditions: {str(e)}")
            return []

    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using nomic-embed-text."""
        try:
            async with aiohttp.ClientSession() as session:
                ollama_host = os.getenv("OLLAMA_HOST", "http://35.202.133.28:11434")
                async with session.post(
                    f"{ollama_host}/api/embeddings",
                    json={
                        "model": self.embedding_model,
                        "prompt": text
                    },
                    timeout=30  # Increased timeout for embedding generation
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["embedding"]
                    else:
                        logger.error(f"Error getting embedding: {response.status}")
                        return [0.0] * 2048  # Return zero vector as fallback
        except Exception as e:
            logger.error(f"Error in _get_embedding: {str(e)}")
            return [0.0] * 2048  # Return zero vector as fallback 
