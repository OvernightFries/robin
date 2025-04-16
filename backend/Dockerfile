FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PORT=8080 \
    STREAM_PORT=8765 \
    PYTHONUNBUFFERED=1

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
RUN mkdir -p /app/data/pdfs /app/model_cache /app/market_stream && \
    chmod -R 755 /app/data /app/model_cache

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
COPY market_stream/requirements.txt ./market_stream/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r market_stream/requirements.txt

# Copy application code
COPY . .

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
