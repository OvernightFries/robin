from fastapi import FastAPI, HTTPException, WebSocket
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
from fastapi import Request
from fastapi.responses import JSONResponse
import uuid
import redis
import json
from utils.redis_client import init_redis
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get port from environment variable or default to 8080
PORT = int(os.getenv("PORT", "8080"))
logger.info(f"Starting application on port {PORT}")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InitializeTickerRequest(BaseModel):
    symbol: str

# Register all routes first
@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "API is running",
        "endpoints": {
            "health": "/health",
            "initialize_ticker": "/initialize_ticker"
        }
    }

@app.post("/initialize_ticker")
async def initialize_ticker(request: InitializeTickerRequest) -> Dict[str, Any]:
    """Initialize data for a new ticker symbol."""
    request_id = str(uuid.uuid4())
    logger.info(f"Request {request_id}: Initializing ticker {request.symbol}")
    
    try:
        if not request.symbol:
            raise HTTPException(
                status_code=400,
                detail="Symbol is required",
                headers={"Access-Control-Allow-Origin": "https://robin-khaki.vercel.app"}
            )
            
        # Initialize data clients
        market_data = MarketData(request.symbol)
        options_data = OptionsData(request.symbol)
        
        # Fetch market and options data concurrently
        market_context, options_context = await asyncio.gather(
            market_data.get_market_data(),
            options_data.get_options_data(),
            return_exceptions=True  # Don't raise exceptions, return them instead
        )
        
        # Handle any exceptions from the concurrent calls
        if isinstance(market_context, Exception):
            logger.error(f"Market data error: {str(market_context)}")
            market_context = {"status": "unavailable", "message": str(market_context)}
            
        if isinstance(options_context, Exception):
            logger.error(f"Options data error: {str(options_context)}")
            options_context = {"status": "unavailable", "message": str(options_context)}
        
        # Return response
        response = JSONResponse(
            content={
                "status": "success",
                "message": f"Data initialized for {request.symbol}",
                "market_context": market_context,
                "options_context": options_context,
                "request_id": request_id
            },
            status_code=200
        )
        
        logger.info(f"Successfully initialized ticker {request.symbol}")
        return response
        
    except Exception as e:
        logger.error(f"Error initializing ticker {request.symbol}: {str(e)}")
        return JSONResponse(
            content={
                "status": "partial",
                "message": f"Partial data available for {request.symbol}",
                "market_context": {"status": "unavailable", "message": str(e)},
                "options_context": {"status": "unavailable", "message": "Options data not fetched"},
                "request_id": request_id
            },
            status_code=200
        )

# Initialize components with retry logic
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

async def initialize_with_retry(initializer, component_name):
    """Initialize a component with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Initializing {component_name} (attempt {attempt + 1}/{MAX_RETRIES})")
            result = await initializer()
            logger.info(f"Successfully initialized {component_name}")
            return result
        except Exception as e:
            logger.error(f"Error initializing {component_name} (attempt {attempt + 1}): {e}")
            if attempt < MAX_RETRIES - 1:
                retry_delay = RETRY_DELAY * (attempt + 1)  # Exponential backoff
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Failed to initialize {component_name} after {MAX_RETRIES} attempts")
                return None

# Initialize Redis and components after route registration
redis_client = init_redis()
chat_memory = None
vectorizer = None
knowledge_base = None

async def initialize_components():
    """Initialize components in the background with retry logic."""
    global chat_memory, vectorizer, knowledge_base
    
    # Initialize Redis for chat memory
    async def init_chat_memory():
        return ChatMemory(redis_client=init_redis())
    
    # Initialize vectorizer with timeout handling
    async def init_vectorizer():
        vec = FinancialDataVectorizer()
        try:
            await asyncio.wait_for(vec.ensure_index_exists(), timeout=30)
        except asyncio.TimeoutError:
            logger.warning("Vectorizer initialization timed out, continuing with basic setup")
        return vec
    
    # Initialize knowledge base with timeout handling
    async def init_knowledge_base():
        kb = MarketVectorStore()
        try:
            await asyncio.wait_for(kb._ensure_pinecone_initialized(), timeout=30)
        except asyncio.TimeoutError:
            logger.warning("Knowledge base initialization timed out, continuing with basic setup")
        return kb
    
    # Initialize components with retry
    chat_memory_task = initialize_with_retry(init_chat_memory, "chat memory")
    vectorizer_task = initialize_with_retry(init_vectorizer, "vectorizer")
    knowledge_base_task = initialize_with_retry(init_knowledge_base, "knowledge base")
    
    # Wait for all initializations to complete
    chat_memory = await chat_memory_task
    vectorizer = await vectorizer_task
    knowledge_base = await knowledge_base_task
    
    # Log final status
    logger.info("Component initialization complete:")
    logger.info(f"Chat Memory: {'Initialized' if chat_memory else 'Failed'}")
    logger.info(f"Vectorizer: {'Initialized' if vectorizer else 'Failed'}")
    logger.info(f"Knowledge Base: {'Initialized' if knowledge_base else 'Failed'}")

# Start component initialization in the background
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(initialize_components())

@app.get("/health")
async def health_check():
    """Health check endpoint with detailed status."""
    try:
        status = {
            "status": "healthy",
            "server": "running",
            "components": {
                "chat_memory": "initialized" if chat_memory else "not initialized",
                "vectorizer": "initialized" if vectorizer else "not initialized",
                "knowledge_base": "initialized" if knowledge_base else "not initialized"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.debug(f"Health check status: {status}")
        return status
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "status": "degraded",
            "server": "running",
            "components": {
                "chat_memory": "error",
                "vectorizer": "error",
                "knowledge_base": "error"
            },
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

class QueryRequest(BaseModel):
    query: str
    symbol: Optional[str] = None

@app.post("/query")
async def query(request: QueryRequest):
    logger.debug(f"Received query request: {request}")
    try:
        # Get market data
        market_data_instance = MarketData(request.symbol)
        market_context = await market_data_instance.get_market_data()
        logger.debug(f"Retrieved market data: {market_context}")
        
        # Get knowledge results
        knowledge_results = await knowledge_base.search_similar_market_conditions(
            request.query,
            request.symbol if request.symbol else "general",
            top_k=5
        )
        logger.debug(f"Retrieved knowledge results: {knowledge_results}")
        
        # Format knowledge results
        knowledge_context = "\n\nRelevant Trading Knowledge:\n"
        for result in knowledge_results:
            knowledge_context += f"\n{result.metadata['text']}"
        
        # Generate response
        response = await call_ollama(
            query=request.query,
            context=knowledge_context,
            market_context=market_context
        )
        logger.debug(f"Generated response: {response}")
        
        return {
            "status": "success",
            "response": response,
            "market_context": market_context,
            "knowledge_context": knowledge_context
        }
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-redis")
async def test_redis():
    """Test Redis connection and basic operations."""
    try:
        if not redis_client:
            return JSONResponse(
                status_code=503,
                content={"status": "error", "message": "Redis client not initialized"}
            )
        
        # Test basic operations
        test_key = "test:connection"
        test_value = {"timestamp": datetime.utcnow().isoformat()}
        
        # Test set
        redis_client.setex(
            test_key,
            60,  # 1 minute TTL
            json.dumps(test_value)
        )
        
        # Test get
        retrieved = redis_client.get(test_key)
        if not retrieved:
            raise Exception("Failed to retrieve test value")
            
        # Test delete
        redis_client.delete(test_key)
        
        return JSONResponse(
            content={
                "status": "success",
                "message": "Redis operations successful",
                "test_value": test_value,
                "retrieved_value": json.loads(retrieved),
                "redis_config": {
                    "host": os.getenv("REDIS_HOST", "not set"),
                    "port": os.getenv("REDIS_PORT", "not set"),
                    "is_memorystore": os.getenv("REDIS_HOST", "localhost") not in ["localhost", "127.0.0.1"]
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Redis test failed: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "redis_config": {
                    "host": os.getenv("REDIS_HOST", "not set"),
                    "port": os.getenv("REDIS_PORT", "not set")
                }
            }
        )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for streaming market data."""
    await websocket.accept()
    try:
        while True:
            if redis_client:
                try:
                    market_data = redis_client.get("market_data")
                    if market_data:
                        await websocket.send_text(market_data)
                except Exception as e:
                    logger.error(f"Redis error: {str(e)}")
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        await websocket.close()

# Start the application
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        log_level="info",
        reload=False
    )
