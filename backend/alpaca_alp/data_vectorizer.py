import numpy as np
import pandas as pd
from datetime import datetime
import json
from typing import List, Dict, Any
import asyncio
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import os
import logging
from alpaca_alp.options_historical import fetch_all_contracts
from functools import lru_cache
import time
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class FinancialDataVectorizer:
    def __init__(self):
        self.model = None
        self._model_loaded = False
        
        # Initialize Pinecone
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = os.getenv("PINECONE_REALTIME_INDEX", "real-time-vectorization")
        self.batch_size = int(os.getenv("VECTOR_BATCH_SIZE", "50"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        
        # Initialize Pinecone client with retry
        self.pc = Pinecone(api_key=self.api_key)
        self.index = None
        
        # Create cache directory if it doesn't exist
        os.makedirs("./data/raw", exist_ok=True)
        os.makedirs("./data/cache", exist_ok=True)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def ensure_index_exists(self):
        """Ensure the real-time index exists, create if it doesn't."""
        try:
            if not self.index:
                try:
                    # List indexes with timeout
                    indexes = await asyncio.wait_for(
                        asyncio.to_thread(self.pc.list_indexes),
                        timeout=10
                    )
                    if self.index_name not in indexes.names():
                        logger.info(f"Creating real-time index {self.index_name}")
                        # Create index with timeout
                        await asyncio.wait_for(
                            asyncio.to_thread(
                                self.pc.create_index,
                                name=self.index_name,
                                dimension=384,  # Dimension for MiniLM model
                                metric='cosine',
                                spec=ServerlessSpec(
                                    cloud='aws',
                                    region=os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
                                )
                            ),
                            timeout=30
                        )
                    self.index = self.pc.Index(self.index_name)
                    logger.info(f"Real-time index {self.index_name} is ready")
                except asyncio.TimeoutError:
                    logger.warning(f"Pinecone index operations timed out for {self.index_name}")
                    self.index = None
        except Exception as e:
            logger.error(f"Error ensuring index exists: {e}")
            raise
    
    @lru_cache(maxsize=1)
    def load_model(self):
        """Load the model from cache with LRU caching"""
        if not self._model_loaded:
            logger.info("Loading sentence transformer model from cache...")
            try:
                self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                self._model_loaded = True
                logger.info("Model loaded from cache successfully")
            except Exception as e:
                logger.error(f"Error loading model: {e}")
                raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def process_options_data(self, contracts: List[Dict[Any, Any]]) -> List[str]:
        """Convert options contracts into text descriptions for embedding"""
        try:
            descriptions = []
            for contract in contracts:
                desc = (
                    f"Option contract for {contract['underlying_symbol']} "
                    f"expiring on {contract['expiration_date']}, "
                    f"{contract['type'].upper()} option with strike price ${contract['strike_price']}. "
                    f"Open interest: {contract['open_interest']}, "
                    f"Last close price: ${contract.get('close_price', 'N/A')}. "
                    f"Contract status: {contract['status']}."
                )
                descriptions.append(desc)
            return descriptions
        except Exception as e:
            logger.error(f"Error processing options data: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def vectorize_options(self, descriptions: List[str], metadata: List[Dict]):
        """Convert options descriptions to vectors and store in Pinecone"""
        try:
            self.load_model()  # Ensure model is loaded
            embeddings = self.model.encode(descriptions)
            
            # Generate IDs for each embedding
            ids = [f"opt_{i}_{datetime.now().strftime('%Y%m%d')}" for i in range(len(descriptions))]
            
            # Prepare vectors for Pinecone
            vectors = []
            for i, (embedding, desc, meta) in enumerate(zip(embeddings, descriptions, metadata)):
                vectors.append({
                    'id': ids[i],
                    'values': embedding.tolist(),
                    'metadata': {
                        **meta,
                        'text': desc,
                        'type': 'options',
                        'timestamp': datetime.now().isoformat()
                    }
                })
            
            # Store in Pinecone in configurable batches
            for i in range(0, len(vectors), self.batch_size):
                batch = vectors[i:i + self.batch_size]
                self.index.upsert(vectors=batch)
                logger.info(f"Upserted batch {i//self.batch_size + 1} of {len(vectors)//self.batch_size + 1}")
                time.sleep(0.1)  # Small delay between batches
        except Exception as e:
            logger.error(f"Error vectorizing options: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def process_market_data(self, market_data: List[Dict]) -> List[str]:
        """Convert market data into text descriptions for embedding"""
        try:
            descriptions = []
            for data in market_data:
                desc = (
                    f"Market data for {data['symbol']} on {data.get('timestamp', 'N/A')}. "
                    f"Price: ${data.get('price', 'N/A')}, "
                    f"Volume: {data.get('volume', 'N/A')}, "
                    f"Market cap: ${data.get('market_cap', 'N/A')}."
                )
                descriptions.append(desc)
            return descriptions
        except Exception as e:
            logger.error(f"Error processing market data: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def vectorize_market_data(self, descriptions: List[str], metadata: List[Dict]):
        """Convert market data descriptions to vectors and store in Pinecone"""
        try:
            self.load_model()  # Ensure model is loaded
            embeddings = self.model.encode(descriptions)
            
            # Generate IDs for each embedding
            ids = [f"mkt_{i}_{datetime.now().strftime('%Y%m%d')}" for i in range(len(descriptions))]
            
            # Prepare vectors for Pinecone
            vectors = []
            for i, (embedding, desc, meta) in enumerate(zip(embeddings, descriptions, metadata)):
                vectors.append({
                    'id': ids[i],
                    'values': embedding.tolist(),
                    'metadata': {
                        **meta,
                        'text': desc,
                        'type': 'market',
                        'timestamp': datetime.now().isoformat()
                    }
                })
            
            # Store in Pinecone in configurable batches
            for i in range(0, len(vectors), self.batch_size):
                batch = vectors[i:i + self.batch_size]
                self.index.upsert(vectors=batch)
                logger.info(f"Upserted batch {i//self.batch_size + 1} of {len(vectors)//self.batch_size + 1}")
                time.sleep(0.1)  # Small delay between batches
        except Exception as e:
            logger.error(f"Error vectorizing market data: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def cleanup_vectors(self, symbol: str):
        """Delete vectors for a specific symbol"""
        try:
            self.index.delete(filter={'symbol': symbol})
            logger.info(f"Deleted vectors for {symbol}")
        except Exception as e:
            logger.error(f"Error cleaning up vectors: {e}")
            raise

    async def process_ticker_data(self, symbol: str):
        """Process and vectorize all data for a given ticker"""
        try:
            logger.info(f"Fetching options data for {symbol}...")
            
            # Ensure index exists before processing
            await self.ensure_index_exists()
            
            # Fetch options data with retry
            options_contracts = await fetch_all_contracts(symbol)
            
            # Limit the number of contracts to process
            if len(options_contracts) > 300:
                logger.info(f"Limiting to 300 most recent contracts out of {len(options_contracts)} total")
                options_contracts = options_contracts[:300]
            
            logger.info(f"Processing {len(options_contracts)} contracts...")
            
            # Process options data
            options_descriptions = self.process_options_data(options_contracts)
            options_metadata = [{
                'symbol': contract['underlying_symbol'],
                'type': contract['type'],
                'strike': contract['strike_price'],
                'expiration': contract['expiration_date']
            } for contract in options_contracts]
            
            # Vectorize and store options data
            logger.info(f"Vectorizing {len(options_descriptions)} options contracts...")
            await self.vectorize_options(options_descriptions, options_metadata)
            
            # Show total vectors stored
            stats = self.index.describe_index_stats()
            logger.info(f"Total vectors stored in index: {stats.total_vector_count}")
            
            logger.info(f"Data vectorization complete for {symbol}")
            
            # Save the raw data as backup
            with open(f"./data/raw/{symbol}_vectorized_{datetime.now().strftime('%Y%m%d')}.json", 'w') as f:
                json.dump({
                    'options_contracts': options_contracts,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            # Cleanup vectors after processing
            self.cleanup_vectors(symbol)
            logger.info(f"Cleaned up vectors for {symbol}")
            
        except Exception as e:
            logger.error(f"Error processing ticker data: {e}")
            raise

async def main():
    # Initialize vectorizer
    vectorizer = FinancialDataVectorizer()
    
    try:
        # Get ticker from user
        symbol = input("Enter ticker symbol to vectorize data (e.g., AAPL): ").upper()
        
        # Process data
        await vectorizer.process_ticker_data(symbol)
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        # Ensure cleanup happens even if there's an error
        vectorizer.cleanup_vectors(symbol)
        raise

if __name__ == "__main__":
    asyncio.run(main()) 
