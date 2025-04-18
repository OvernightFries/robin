FROM python:3.11-slim as builder

WORKDIR /app

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PORT=8080 \
    PYTHONUNBUFFERED=1 \
    TRANSFORMERS_CACHE=/app/model_cache \
    HF_HOME=/app/model_cache \
    PYTHONPATH=/app

# Install build dependencies and curl for healthcheck
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
RUN mkdir -p /app/data/pdfs /app/model_cache && \
    chmod -R 755 /app/data /app/model_cache

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
COPY market_stream/requirements.txt ./market_stream/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r market_stream/requirements.txt && \
    pip install --no-cache-dir huggingface_hub[hf_xet]

# Copy application code
COPY . .

# Pre-download and cache sentence-transformers models
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); \
    SentenceTransformer('BAAI/bge-large-en-v1.5')"

# Test stage to verify the application can start
FROM builder as tester
WORKDIR /app

# Install curl for testing
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Test if the application can start and listen on the port
RUN echo '#!/bin/bash\n\
    set -e\n\
    echo "Testing application startup..."\n\
    python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --log-level info &\n\
    sleep 5\n\
    if ! curl -s http://localhost:${PORT:-8080}/health > /dev/null; then\n\
    echo "Application failed to start or health check failed"\n\
    exit 1\n\
    fi\n\
    echo "Application started successfully"\n\
    ' > /app/test.sh && chmod +x /app/test.sh

# Run the test
RUN /app/test.sh

# Final stage
FROM builder
WORKDIR /app

# Create a simple startup script
RUN echo '#!/bin/bash\n\
    set -e\n\
    echo "Starting application..."\n\
    exec python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --log-level info\n\
    ' > /app/start.sh && chmod +x /app/start.sh

# Health check with longer timeout and better retry logic
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Expose port
EXPOSE 8080

# Run the application
CMD ["/app/start.sh"]
