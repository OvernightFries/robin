# Build stage
FROM python:3.11-slim as builder

# Add build arguments for cache busting
ARG CACHE_BUST=1
ARG PIP_CACHE_DIR=/root/.cache/pip

WORKDIR /app

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

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
COPY market_stream/requirements.txt ./market_stream/

# Install Python dependencies with cache
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r market_stream/requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create necessary directories
RUN mkdir -p /app/data/pdfs /app/model_cache /app/market_stream && \
    chmod -R 755 /app/data /app/model_cache

# Copy application code
COPY . .

# Set environment variables
ENV PORT=8080 \
    STREAM_PORT=8765 \
    PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose ports
EXPOSE 8080 8765

# Create and set up startup script
RUN echo '#!/bin/bash\n\
cd /app && uvicorn main:app --host 0.0.0.0 --port 8080 --log-level info &\n\
python -m market_stream.main &\n\
wait' > /app/start.sh && chmod +x /app/start.sh

# Run the application
CMD ["/app/start.sh"]
