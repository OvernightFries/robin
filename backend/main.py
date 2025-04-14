from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import os
from datetime import datetime
from alpaca_alp.market_data import MarketData
from alpaca_alp.options_data import OptionsData
from utils.chat_memory import ChatMemory
from rag.ollama_client import call_ollama
from alpaca_alp.data_vectorizer import FinancialDataVectorizer
from rag.vector_store import MarketVectorStore
from dotenv import load_dotenv
from pinecone import Pinecone
from pinecone.core.client.api_client import ApiClient
from pinecone.core.client.models import CreateIndexRequest, ServerlessSpec

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = os.getenv("PINECONE_INDEX_NAME", "robin-ai")

# Check if index exists
if index_name not in pc.list_indexes().names():
    # Create new index
    pc.create_index(
        name=index_name,
        dimension=2048,
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region=os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
        )
    )

# Initialize components
try:
    logger.info("Initializing components...")
    chat_memory = ChatMemory()
    vectorizer = FinancialDataVectorizer()  # For real-time market data
    knowledge_base = MarketVectorStore()    # For pre-processed PDFs
    logger.info("Components initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize components: {str(e)}")
    raise

class QueryRequest(BaseModel):
    symbol: str
    query: Optional[str] = None

@app.post("/initialize_ticker")
async def initialize_ticker(symbol: str) -> Dict[str, Any]:
    """Initialize data for a new ticker symbol."""
    logger.info(f"Initializing data for symbol: {symbol}")
    
    try:
        # Get market data
        market_data = MarketData(symbol)
        market_context = await market_data.get_market_data()
        
        # Get options data
        options_data = OptionsData(symbol)
        options_context = await options_data.get_options_data()
        
        # Vectorize the data in real-time
        await vectorizer.process_ticker_data(symbol)
        
        # Format context for RAG
        formatted_context = market_data.format_for_rag(market_context)
        
        return {
            "status": "success",
            "message": f"Data initialized for {symbol}",
            "market_context": market_context,
            "options_context": options_context
        }
        
    except Exception as e:
        logger.error(f"Error initializing ticker data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def process_query(request: QueryRequest) -> Dict[str, Any]:
    """Process a query using both real-time data and knowledge base."""
    logger.info(f"Processing query for symbol: {request.symbol}")
    
    if not request.query:
        raise HTTPException(status_code=400, detail="Query parameter is required")
    
    try:
        # Get current market context
        market_data = MarketData(request.symbol)
        market_context = await market_data.get_market_data()
        formatted_context = market_data.format_for_rag(market_context)
        logger.info(f"Retrieved market context for {request.symbol}")
        
        # Get relevant knowledge from PDF database
        try:
            knowledge_results = await knowledge_base.search_similar_market_conditions(
                request.query,
                request.symbol,
                top_k=5
            )
            logger.info(f"Retrieved {len(knowledge_results)} relevant knowledge results")
            
            # Combine knowledge base results with market context
            knowledge_context = "\n\nRelevant Trading Knowledge:\n"
            for result in knowledge_results:
                knowledge_context += f"\n{result.metadata['text']}"
        except Exception as e:
            logger.warning(f"Error retrieving knowledge base results: {str(e)}")
            knowledge_context = "\nNo relevant knowledge base results found."
        
        # Generate response using both contexts
        try:
            response = await call_ollama(
                request.query,
                knowledge_context,  # PDF knowledge base context
                formatted_context   # Real-time market data context
            )
            logger.info("Successfully generated response")
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            response = f"Error generating response: {str(e)}"
        
        return {
            "response": response,
            "market_context": market_context,
            "knowledge_context": knowledge_results if 'knowledge_results' in locals() else []
        }
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check if components are initialized
        if not chat_memory:
            raise Exception("Chat memory not initialized")
        if not vectorizer:
            raise Exception("Vectorizer not initialized")
        if not knowledge_base:
            raise Exception("Knowledge base not initialized")
            
        # Check Pinecone connection
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index_name = os.getenv("PINECONE_INDEX_NAME", "robin-ai")
        if index_name not in pc.list_indexes().names():
            raise Exception("Pinecone index not found")
            
        return {
            "status": "healthy",
            "components": {
                "chat_memory": "initialized",
                "vectorizer": "initialized",
                "knowledge_base": "initialized",
                "pinecone": "connected"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
