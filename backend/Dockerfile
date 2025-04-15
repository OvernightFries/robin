FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
  build-essential \
  curl \
  git \
  libpq-dev \
  python3-dev \
  cmake \
  pkg-config \
  gcc \
  g++ \
  && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /app/data/pdfs /app/model_cache /app/market_stream

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install all Python dependencies in one step
RUN pip install --no-cache-dir -r requirements.txt && \
  pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
  pip install --no-cache-dir sentence-transformers && \
  python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy the rest of the application
COPY . .

# Create data directories and set permissions
RUN chmod -R 755 /app/data && \
  chmod -R 755 /app/model_cache

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV ALPACA_API_KEY=${ALPACA_API_KEY}
ENV ALPACA_SECRET_KEY=${ALPACA_SECRET_KEY}
ENV ALPACA_ENDPOINT=${ALPACA_ENDPOINT:-https://paper-api.alpaca.markets}
ENV ALPACA_STREAM_ENDPOINT=${ALPACA_STREAM_ENDPOINT:-wss://stream.data.alpaca.markets/v2/iex}
ENV PINECONE_API_KEY=${PINECONE_API_KEY}
ENV PINECONE_ENVIRONMENT=${PINECONE_ENVIRONMENT}
ENV PINECONE_INDEX_NAME=${PINECONE_INDEX_NAME:-robin-ai}
ENV REDIS_URL=redis://redis:6379
ENV OLLAMA_HOST=http://35.202.133.28:11434
ENV MODEL_NAME=llama3
ENV EMBEDDING_MODEL=nomic-embed-text
ENV LOG_LEVEL=INFO
ENV ENABLE_REAL_TIME=true
ENV WS_HOST=0.0.0.0
ENV WS_PORT=8765

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run setup and start server with proper logging
CMD ["sh", "-c", "\
  python rag/setup_pinecone.py && \
  python rag/initialize_embeddings.py && \
  python -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info --workers 4 --ws websockets"]
