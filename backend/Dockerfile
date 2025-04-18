FROM python:3.11-slim

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

# Pre-download and cache sentence-transformers models during build
RUN python -c "from sentence_transformers import SentenceTransformer; \
    print('Downloading models...'); \
    SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', cache_folder='/app/model_cache'); \
    SentenceTransformer('BAAI/bge-large-en-v1.5', cache_folder='/app/model_cache'); \
    print('Models downloaded successfully')"

# Create a simple startup script that starts the server directly
RUN echo '#!/bin/bash\n\
    echo "Starting FastAPI server..."\n\
    exec uvicorn main:app --host 0.0.0.0 --port 8080 --log-level info\n\
    ' > /app/start.sh && chmod +x /app/start.sh

# Health check with longer timeout and better retry logic
HEALTHCHECK --interval=30s --timeout=30s --start-period=300s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Run the application using the startup script
CMD ["/app/start.sh"]
