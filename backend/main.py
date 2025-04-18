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
from fastapi import Request
from fastapi.responses import JSONResponse
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI()

# Add debug logging for route registration
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup - registered routes:")
    for route in app.routes:
        logger.info(f"Route: {route.path} - Methods: {route.methods}")

# Add root endpoint
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

# Global OPTIONS handler for all paths - MUST be before CORS middleware
@app.options("/{path:path}")
async def options_handler(path: str):
    logger.info(f"Handling OPTIONS request for path: {path}")
    response = JSONResponse(
        content={"status": "ok", "message": "CORS preflight request handled"},
        status_code=200
    )
    response.headers["Access-Control-Allow-Origin"] = "https://robin-khaki.vercel.app"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Max-Age"] = "600"
    return response

# Configure CORS
origins = [
    "https://robin-khaki.vercel.app",
    "http://localhost:3000",
    "https://robin-463504869309.us-central1.run.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["*"],
    max_age=600
)

# Add middleware to handle CORS for all responses
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "https://robin-khaki.vercel.app"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Max-Age"] = "600"
    return response

# Custom exception handler that includes CORS headers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error handling request: {str(exc)}", exc_info=True)
    response = JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "status": "error"
        }
    )
    response.headers["Access-Control-Allow-Origin"] = "https://robin-khaki.vercel.app"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# Add middleware to log all requests and responses
@app.middleware("http")
async def log_requests_and_responses(request: Request, call_next):
    request_id = str(uuid.uuid4())
    logger.info(f"Request {request_id}: {request.method} {request.url.path}", extra={
        "request_id": request_id,
        "headers": dict(request.headers),
        "query_params": dict(request.query_params)
    })
    
    try:
        response = await call_next(request)
        logger.info(f"Response {request_id}: {response.status_code}", extra={
            "request_id": request_id,
            "status_code": response.status_code
        })
        return response
    except Exception as e:
        logger.error(f"Error in request {request_id}: {str(e)}", exc_info=True, extra={
            "request_id": request_id,
            "error": str(e)
        })
        raise

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = os.getenv("PINECONE_INDEX_NAME", "robindocs")  # Using PINECONE_INDEX_NAME from .env

# Check if index exists
if index_name not in pc.list_indexes().names():
    # Create new index
    pc.create_index(
        name=index_name,
        dimension=2048,
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region=os.getenv("PINECONE_ENVIRONMENT")
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
    # Don't raise the exception, allow the service to start without Redis
    chat_memory = None
    vectorizer = None
    knowledge_base = None

class QueryRequest(BaseModel):
    query: str
    symbol: Optional[str] = None

class InitializeTickerRequest(BaseModel):
    symbol: str

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
            
        # Get market data
        market_data = MarketData(request.symbol)
        market_context = await market_data.get_market_data()
        
        # Get options data
        options_data = OptionsData(request.symbol)
        options_context = await options_data.get_options_data()
        
        # Vectorize the data
        await vectorizer.process_ticker_data(request.symbol)
        
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
        raise HTTPException(
            status_code=500,
            detail=str(e),
            headers={"Access-Control-Allow-Origin": "https://robin-khaki.vercel.app"}
        )

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

@app.get("/health")
async def health_check():
    """Health check endpoint with detailed status."""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        # Check Pinecone connection
        try:
            pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
            index_name = os.getenv("PINECONE_INDEX_NAME")
            if index_name not in pc.list_indexes().names():
                raise Exception("Pinecone index not found")
            health_status["components"]["pinecone"] = "healthy"
        except Exception as e:
            logger.error(f"Pinecone health check failed: {str(e)}")
            health_status["components"]["pinecone"] = "unhealthy"
            health_status["status"] = "degraded"
        
        # Check other components
        for component in ["chat_memory", "vectorizer", "knowledge_base"]:
            try:
                if globals().get(component) is None:
                    raise Exception(f"{component} not initialized")
                health_status["components"][component] = "healthy"
            except Exception as e:
                logger.error(f"{component} health check failed: {str(e)}")
                health_status["components"][component] = "unhealthy"
                health_status["status"] = "degraded"
        
        return JSONResponse(content=health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
