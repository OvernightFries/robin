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
COPY market_stream/requirements.txt ./market_stream/

# Install Python dependencies for both services
RUN pip install --no-cache-dir -r requirements.txt && \
  pip install --no-cache-dir -r market_stream/requirements.txt

# Copy the rest of the application
COPY . .

# Create data directories and set permissions
RUN chmod -R 755 /app/data && \
  chmod -R 755 /app/model_cache

# Set environment variables
ENV PORT=8080
ENV STREAM_PORT=8765
ENV PYTHONUNBUFFERED=1

# Health check for main API
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Expose both ports
EXPOSE 8080 8765

# Create a startup script
RUN echo '#!/bin/bash\n\
  python -m uvicorn main:app --host 0.0.0.0 --port 8080 --log-level info & \n\
  python -m market_stream.main & \n\
  wait' > /app/start.sh && chmod +x /app/start.sh

# Run both services
CMD ["/app/start.sh"]
