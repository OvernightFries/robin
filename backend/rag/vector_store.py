from pinecone import Pinecone
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
import aiohttp
import json
import logging
import asyncio

load_dotenv()

logger = logging.getLogger(__name__)

class MarketVectorStore:
    def __init__(self):
        self.pc = None
        self.index = None
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "robindocs")
        self.embedding_model = "nomic-embed-text"
        self._initialization_task = None

    async def _initialize_pinecone(self):
        """Initialize Pinecone connection in the background."""
        try:
            self.pc = Pinecone(
                api_key=os.getenv("PINECONE_API_KEY"),
                timeout=30
            )
            
            # Check if index exists with timeout
            try:
                indexes = await asyncio.wait_for(
                    asyncio.to_thread(self.pc.list_indexes),
                    timeout=10
                )
                if self.index_name not in indexes.names():
                    logger.warning(f"Pre-trained index {self.index_name} not found. Some features may be limited.")
                    self.index = None
                else:
                    self.index = self.pc.Index(self.index_name)
                    logger.info(f"Successfully connected to pre-trained index {self.index_name}")
            except asyncio.TimeoutError:
                logger.warning("Pinecone index listing timed out, continuing with basic setup")
                self.index = None
        except Exception as e:
            logger.error(f"Error initializing Pinecone: {e}")
            self.index = None

    async def _ensure_pinecone_initialized(self):
        """Ensure Pinecone is initialized, start initialization if needed."""
        if self.pc is None and self._initialization_task is None:
            self._initialization_task = asyncio.create_task(self._initialize_pinecone())
        if self._initialization_task is not None:
            try:
                await asyncio.wait_for(self._initialization_task, timeout=30)
            except asyncio.TimeoutError:
                logger.warning("Pinecone initialization timed out, continuing with basic setup")
            self._initialization_task = None

    async def search_similar_market_conditions(self, query: str, symbol: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar market conditions in the vector store."""
        try:
            await self._ensure_pinecone_initialized()
            
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
