# Robin AI Trading Assistant

A sophisticated AI-powered trading assistant that combines real-time market data, RAG (Retrieval-Augmented Generation), and advanced analytics to provide intelligent trading insights and recommendations.

## Features

- **Real-time Market Data Streaming**
  - Live market data from Alpaca
  - WebSocket-based updates
  - Redis caching for performance
  - Historical data preservation

- **AI-Powered Analysis**
  - Llama 3 for RAG-based insights
  - Nomic embeddings for semantic search
  - Pinecone vector database integration
  - PDF knowledge base support

- **Modern Architecture**
  - Docker-based microservices
  - GPU acceleration for AI models
  - Health monitoring and auto-recovery
  - Scalable design

## 🛠️ Tech Stack

### Core Services
- **Backend**: FastAPI (Python)
- **Frontend**: Next.js (TypeScript)
- **AI Model**: Llama 3 via Ollama
- **Vector DB**: Pinecone
- **Cache**: Redis
- **Market Data**: Alpaca API

### Key Dependencies
- **Python Packages**:
  - `aiohttp`: Async HTTP client
  - `websockets>=9.0,<11`: WebSocket support (compatible with alpaca-trade-api)
  - `alpaca-trade-api>=3.0.2`: Market data integration
  - `fastapi`: API framework
  - `pydantic`: Data validation
  - `msgpack`: Efficient serialization

- **Frontend**:
  - Next.js 14
  - TypeScript
  - Tailwind CSS
  - WebSocket client

## 📋 Prerequisites

1. **API Keys**:
   - Alpaca API key and secret
   - Pinecone API key and environment

2. **Hardware**:
   - NVIDIA GPU (for Ollama)
   - 8GB+ RAM
   - 20GB+ disk space

3. **Software**:
   - Docker and Docker Compose
   - NVIDIA Container Toolkit
   - Git

## 🚀 Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/robin-ai.git
   cd robin-ai
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your API keys:
   ```env
   ALPACA_API_KEY=your_key
   ALPACA_SECRET_KEY=your_secret
   PINECONE_API_KEY=your_key
   PINECONE_ENVIRONMENT=your_env
   ```

3. **Create required directories**:
   ```bash
   mkdir -p data/pdfs
   mkdir -p backend/model_cache
   mkdir -p backend/market_stream
   mkdir -p backend/utils
   ```

4. **Start the services**:
   ```bash
   docker-compose down -v
   docker-compose build
   docker-compose up -d
   ```

5. **Verify services**:
   ```bash
   docker-compose ps
   ```

## Service Architecture

### Market Stream Service
- Port: 8001
- Handles real-time market data
- WebSocket streaming
- Redis caching
- Health monitoring

### Backend Service
- Port: 8000 (API), 8765 (WebSocket)
- RAG system integration
- PDF processing
- AI model management
- Health monitoring

### Frontend Service
- Port: 3000
- Real-time updates
- Interactive UI
- WebSocket client
- Health monitoring

### Ollama Service
- Port: 11434
- GPU-accelerated
- Llama 3 model
- Health monitoring

### Redis Service
- Port: 6379
- Data persistence
- Real-time caching
- Health monitoring

## 🔧 Configuration

### Environment Variables
```env
# Alpaca Configuration
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_ENDPOINT=https://paper-api.alpaca.markets
ALPACA_STREAM_ENDPOINT=wss://stream.data.alpaca.markets/v2/iex

# Pinecone Configuration
PINECONE_API_KEY=your_key
PINECONE_ENVIRONMENT=your_env
PINECONE_INDEX_NAME=robin-ai

# Service Configuration
REDIS_URL=redis://redis:6379
OLLAMA_HOST=http://ollama:11434
MODEL_NAME=llama3
EMBEDDING_MODEL=nomic-embed-text
LOG_LEVEL=INFO
ENABLE_REAL_TIME=true
WS_HOST=0.0.0.0
WS_PORT=8765
```

##Troubleshooting

### Common Issues

1. **Dependency Conflicts**
   - If you encounter package version conflicts, ensure you're using compatible versions:
     ```bash
     pip install "websockets>=9.0,<11" "alpaca-trade-api>=3.0.2"
     ```

2. **Docker Build Failures**
   - Clean up Docker cache and rebuild:
     ```bash
     docker-compose down -v
     docker system prune -a
     docker-compose build --no-cache
     ```

3. **Ollama Model Issues**
   - Verify model is properly loaded:
     ```bash
     docker exec robin-ollama-1 ollama list
     ```
   - If model is missing, pull it:
     ```bash
     docker exec robin-ollama-1 ollama pull llama3
     ```

4. **WebSocket Connection Issues**
   - Check if ports are available:
     ```bash
     netstat -tuln | grep -E '8001|8765'
     ```
   - Verify firewall settings allow these ports

5. **Redis Connection Issues**
   - Check Redis service status:
     ```bash
     docker exec robin-redis-1 redis-cli ping
     ```
   - Verify Redis URL in environment variables

### Health Check Endpoints

Each service provides health check endpoints:
- Backend: `http://localhost:8000/health`
- Market Stream: `http://localhost:8001/health`
- Frontend: `http://localhost:3000`
- Ollama: `http://localhost:11434/api/tags`
- Redis: Internal ping

### Logs

View service logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f market_stream
docker-compose logs -f frontend
docker-compose logs -f ollama
docker-compose logs -f redis
```

## Knowledge Base

The system supports PDF-based knowledge bases:
1. Place PDF files in `data/pdfs/`
2. The system automatically processes and indexes them
3. Use the API to query the knowledge base

##  Monitoring

Each service includes health checks:
- Backend: `http://localhost:8000/health`
- Market Stream: `http://localhost:8001/health`
- Frontend: `http://localhost:3000`
- Ollama: `http://localhost:11434/api/tags`
- Redis: Internal ping

##  Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Alpaca](https://alpaca.markets) for market data
- [Ollama](https://ollama.ai) for Llama 3 integration
- [Pinecone](https://www.pinecone.io) for vector database
- [FastAPI](https://fastapi.tiangolo.com) for backend framework
- [Next.js](https://nextjs.org) for frontend framework
