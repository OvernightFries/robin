import os
from pinecone import Pinecone
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug: Print environment variables
logger.info(f"PINECONE_API_KEY: {os.getenv('PINECONE_API_KEY')}")
logger.info(f"PINECONE_ENVIRONMENT: {os.getenv('PINECONE_ENVIRONMENT')}")
logger.info(f"PINECONE_INDEX_NAME: {os.getenv('PINECONE_INDEX_NAME')}")

# Initialize Pinecone client
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Create index if it doesn't exist
index_name = os.getenv("PINECONE_INDEX_NAME")
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=4096, 
        metric="cosine",
        spec=pc.IndexSpec(
            serverless=pc.ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
    )
    print(f"Created index {index_name}")
else:
    print(f" Index exists: {index_name}")
