FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PORT=8000 \
    PYTHONUNBUFFERED=1 \
    SENTENCE_TRANSFORMERS_HOME=/app/model_cache

# Install build dependencies
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

# Pre-download the model during build and verify it's available
RUN python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder='/app/model_cache'); print('Model loaded successfully')"

# Copy application code
COPY . .

# Create a startup script
RUN echo '#!/bin/bash\n\
    echo "Starting application..."\n\
    python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer(\"all-MiniLM-L6-v2\", cache_folder=\"/app/model_cache\"); print(\"Model verified in container\")"\n\
    uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info\n\
    ' > /app/start.sh && chmod +x /app/start.sh

# Health check with longer timeout
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Expose port
EXPOSE 8000

# Run the application using the startup script
CMD ["/app/start.sh"]
