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

# Create model cache directory
RUN mkdir -p /app/model_cache

# Pre-download the model during build and fail if it can't download
RUN python -c "import sys; \
    from sentence_transformers import SentenceTransformer; \
    try: \
    print('Downloading model...'); \
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); \
    print('Model downloaded successfully'); \
    except Exception as e: \
    print(f'Error downloading model: {str(e)}'); \
    sys.exit(1)"

# Copy application code
COPY . .

# Create a robust startup script with error handling
RUN echo '#!/bin/bash\n\
    set -e\n\
    echo "Starting application..."\n\
    \n\
    # Function to check if port is available\n\
    check_port() {\n\
    while ! nc -z localhost 8080; do\n\
    echo "Waiting for port 8080..."\n\
    sleep 1\n\
    done\n\
    }\n\
    \n\
    # Start the FastAPI server in the background\n\
    echo "Starting FastAPI server..."\n\
    uvicorn main:app --host 0.0.0.0 --port 8080 --log-level info &\n\
    \n\
    # Wait for server to start\n\
    check_port\n\
    \n\
    # Start model loading in background\n\
    echo "Starting model loading..."\n\
    python -c "from sentence_transformers import SentenceTransformer; \\\n\
    print(\"Loading model...\"); \\\n\
    model = SentenceTransformer(\"sentence-transformers/all-MiniLM-L6-v2\", cache_folder=\"/app/model_cache\"); \\\n\
    print(\"Model loaded successfully\")" &\n\
    \n\
    # Keep the container running\n\
    tail -f /dev/null\n\
    ' > /app/start.sh && chmod +x /app/start.sh

# Install netcat for port checking
RUN apt-get update && apt-get install -y netcat-traditional && rm -rf /var/lib/apt/lists/*

# Health check with longer timeout and better retry logic
HEALTHCHECK --interval=30s --timeout=30s --start-period=300s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Run the application using the startup script
CMD ["/app/start.sh"]
