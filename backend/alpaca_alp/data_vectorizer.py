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

logger = logging.getLogger(__name__)

class FinancialDataVectorizer:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize Pinecone
        self.api_key = os.getenv("PINECONE_API_KEY")
        # Use a different env var for real-time index to avoid conflicts with PDF index
        self.index_name = os.getenv("PINECONE_REALTIME_INDEX", "real-time-vectorization")
        
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=self.api_key)
        
        # Create index if it doesn't exist
        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=384,  # Dimension for MiniLM model
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-west-2'
                )
            )
            
        self.index = self.pc.Index(self.index_name)
    
    def process_options_data(self, contracts: List[Dict[Any, Any]]) -> List[str]:
        """Convert options contracts into text descriptions for embedding"""
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
    
    def vectorize_options(self, descriptions: List[str], metadata: List[Dict]):
        """Convert options descriptions to vectors and store in Pinecone"""
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
        
        # Store in Pinecone in batches
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)
            logger.info(f"Upserted batch {i//batch_size + 1} of {len(vectors)//batch_size + 1}")
    
    def process_market_data(self, market_data: List[Dict]) -> List[str]:
        """Convert market data into text descriptions for embedding"""
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
    
    def vectorize_market_data(self, descriptions: List[str], metadata: List[Dict]):
        """Convert market data descriptions to vectors and store in Pinecone"""
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
        
        # Store in Pinecone in batches
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)
            logger.info(f"Upserted batch {i//batch_size + 1} of {len(vectors)//batch_size + 1}")
    
    def cleanup_vectors(self, symbol: str):
        """Delete vectors for a specific symbol"""
        # Delete vectors by filtering on metadata
        self.index.delete(filter={'symbol': symbol})
        logger.info(f"Deleted vectors for {symbol}")

    async def process_ticker_data(self, symbol: str):
        """Process and vectorize all data for a given ticker"""
        logger.info(f"Fetching options data for {symbol}...")
        
        # Fetch options data
        options_contracts = await fetch_all_contracts(symbol)
        
        # Limit the number of contracts to process (e.g., most recent 300)
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
        self.vectorize_options(options_descriptions, options_metadata)
        
        # Show total vectors stored
        stats = self.index.describe_index_stats()
        logger.info(f"Total vectors stored in index: {stats.total_vector_count}")
        
        logger.info(f"Data vectorization complete for {symbol}")
        
        # Save the raw data as backup
        os.makedirs("./data/raw", exist_ok=True)
        with open(f"./data/raw/{symbol}_vectorized_{datetime.now().strftime('%Y%m%d')}.json", 'w') as f:
            json.dump({
                'options_contracts': options_contracts,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
            
        # Cleanup vectors after processing
        self.cleanup_vectors(symbol)
        logger.info(f"Cleaned up vectors for {symbol}")

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
