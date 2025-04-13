import os
from pinecone import Pinecone
from langchain_ollama import OllamaEmbeddings
from langchain_pinecone import PineconeVectorStore
from typing import List
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Pinecone client
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Correctly pass the Ollama URL (critical in Docker)
embedding = OllamaEmbeddings(
    model="llama3",
    base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
)

# Connect to Pinecone index
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

# Create vector store
vectorstore = PineconeVectorStore(index, embedding, "text")

def retrieve_relevant_chunks(query: str, k: int = 3) -> List[str]:
    """Retrieve relevant chunks from the vector store."""
    try:
        docs = vectorstore.similarity_search(query, k=k)
        logger.info(f"Retrieved {len(docs)} docs for query: {query}")
        for i, doc in enumerate(docs):
            logger.info(f"Doc {i+1}: {doc.page_content[:100]}...")
        return [doc.page_content for doc in docs]
    except Exception as e:
        logger.error(f"Error retrieving chunks: {str(e)}")
        return []
