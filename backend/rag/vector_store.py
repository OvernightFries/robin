from pinecone import Pinecone
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
import aiohttp
import json

load_dotenv()

class MarketVectorStore:
    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "robin-ai")
        self.index = self.pc.Index(self.index_name)
        self.embedding_model = "nomic-embed-text"

    async def search_similar_market_conditions(self, query: str, symbol: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar market conditions in the vector store."""
        try:
            # Get query embedding using nomic-embed-text
            query_vector = await self._get_embedding(query)
            
            # Search in Pinecone
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                filter={"symbol": symbol}
            )
            
            return results.matches
        except Exception as e:
            print(f"Error in search_similar_market_conditions: {str(e)}")
            return []

    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using nomic-embed-text."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://ollama:11434/api/embeddings",
                    json={
                        "model": self.embedding_model,
                        "prompt": text
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["embedding"]
                    else:
                        print(f"Error getting embedding: {response.status}")
                        return [0.0] * 2048
        except Exception as e:
            print(f"Error in _get_embedding: {str(e)}")
            return [0.0] * 2048 
