FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PORT=8080 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TRANSFORMERS_CACHE=/app/model_cache \
    HF_HOME=/app/model_cache \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    python3-dev \
    cmake \
    pkg-config \
    gcc \
    g++ \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Create model cache directory
RUN mkdir -p /app/model_cache

# Create necessary directories
RUN mkdir -p /app/data/pdfs && \
    chmod -R 755 /app/data

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
COPY market_stream/requirements.txt ./market_stream/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r market_stream/requirements.txt && \
    pip install --no-cache-dir huggingface_hub[hf_xet]

# Download and verify the model
RUN python -c "from sentence_transformers import SentenceTransformer; \
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); \
    embeddings = model.encode('This is a test sentence'); \
    print('Model loaded and encoded successfully')"

# Copy application code
COPY . .

# Create a simple startup script
RUN echo '#!/bin/bash\n\
    set -e\n\
    echo "Starting application..."\n\
    \n\
    # Start the FastAPI server\n\
    echo "Starting FastAPI server..."\n\
    uvicorn main:app --host 0.0.0.0 --port 8080 --log-level info\n\
    ' > /app/start.sh && chmod +x /app/start.sh

# Health check with longer timeout
HEALTHCHECK --interval=30s --timeout=30s --start-period=300s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Run the application using the startup script
CMD ["/app/start.sh"]
