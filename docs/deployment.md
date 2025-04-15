# Deployment and Infrastructure Documentation

## Overview
This document details the deployment process, infrastructure setup, and scaling strategies for the Robin AI platform.

## Infrastructure Architecture

### System Components
1. **Frontend Service**
   - Next.js application
   - Nginx reverse proxy
   - Static file serving
   - SSL termination

2. **Backend Service**
   - FastAPI application
   - Gunicorn server
   - Redis cache
   - Database connections

3. **AI Services**
   - Ollama containers
   - Model management
   - GPU acceleration
   - Resource allocation

4. **Data Services**
   - Redis cache
   - Pinecone vector store
   - File storage
   - Backup systems

## Docker Configuration

### Frontend Service
```yaml
# Frontend Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Backend Service
```yaml
# Backend Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  frontend:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - PINECONE_API_KEY=${PINECONE_API_KEY}
    depends_on:
      - redis
      - ollama

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  redis_data:
  ollama_data:
```

## Deployment Process

### Development Environment
1. **Local Setup**
   ```bash
   # Clone repository
   git clone https://github.com/your-org/robin-ai.git
   cd robin-ai

   # Install dependencies
   npm install
   cd backend && pip install -r requirements.txt

   # Start services
   docker-compose up
   ```

2. **Environment Variables**
   ```env
   # Frontend
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_WS_URL=ws://localhost:8000

   # Backend
   ALPACA_API_KEY=your_api_key
   ALPACA_SECRET_KEY=your_secret_key
   PINECONE_API_KEY=your_pinecone_key
   REDIS_URL=redis://redis:6379
   ```

### Production Environment
1. **Build Process**
   ```bash
   # Build Docker images
   docker-compose build

   # Push to registry
   docker push your-registry/frontend:latest
   docker push your-registry/backend:latest
   ```

2. **Deployment**
   ```bash
   # Pull latest images
   docker-compose pull

   # Start services
   docker-compose up -d
   ```

## Scaling Strategy

### Horizontal Scaling
1. **Frontend Scaling**
   - Load balancer configuration
   - Session management
   - Static asset distribution
   - Health checks

2. **Backend Scaling**
   - Worker processes
   - Database connection pooling
   - Cache distribution
   - Load balancing

### Vertical Scaling
1. **Resource Allocation**
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
   ```

2. **Performance Tuning**
   - Worker count optimization
   - Cache size adjustment
   - Database connection limits
   - Memory management

## Monitoring

### Health Checks
1. **Service Health**
   ```python
   @app.get("/health")
   async def health_check():
       return {
           "status": "healthy",
           "services": {
               "redis": check_redis(),
               "pinecone": check_pinecone(),
               "ollama": check_ollama()
           }
       }
   ```

2. **Performance Metrics**
   - Response times
   - Error rates
   - Resource usage
   - Queue lengths

### Logging
1. **Application Logs**
   ```python
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('app.log'),
           logging.StreamHandler()
       ]
   )
   ```

2. **Audit Logs**
   - API access
   - System changes
   - Security events
   - Performance issues

## Security

### Authentication
1. **API Authentication**
   ```python
   @app.middleware("http")
   async def auth_middleware(request: Request, call_next):
       # Authentication logic
       return await call_next(request)
   ```

2. **WebSocket Authentication**
   ```python
   @app.websocket("/ws")
   async def websocket_endpoint(websocket: WebSocket):
       # WebSocket authentication
       await websocket.accept()
   ```

### Data Protection
1. **Input Validation**
   ```python
   class MarketData(BaseModel):
       symbol: str = Field(..., min_length=1, max_length=10)
       price: float = Field(..., gt=0)
       volume: int = Field(..., ge=0)
   ```

2. **Output Protection**
   - Data masking
   - Rate limiting
   - Access control
   - Error handling

## Backup and Recovery

### Data Backup
1. **Database Backup**
   ```bash
   # Redis backup
   redis-cli SAVE
   cp /var/lib/redis/dump.rdb /backup/redis/

   # Pinecone backup
   pinecone backup --index your-index --path /backup/pinecone/
   ```

2. **File Backup**
   ```bash
   # Document backup
   tar -czf /backup/docs/$(date +%Y%m%d).tar.gz /data/docs/

   # Configuration backup
   cp .env /backup/config/
   ```

### Recovery Process
1. **Database Recovery**
   ```bash
   # Redis recovery
   cp /backup/redis/dump.rdb /var/lib/redis/
   redis-cli SHUTDOWN
   redis-server

   # Pinecone recovery
   pinecone restore --index your-index --path /backup/pinecone/
   ```

2. **Service Recovery**
   ```bash
   # Stop services
   docker-compose down

   # Restore data
   # (Follow backup recovery steps)

   # Start services
   docker-compose up -d
   ```

## Maintenance

### Regular Tasks
1. **System Updates**
   ```bash
   # Update dependencies
   npm update
   pip install -U -r requirements.txt

   # Rebuild containers
   docker-compose build
   docker-compose up -d
   ```

2. **Data Cleanup**
   ```python
   def cleanup_old_data():
       # Clean old logs
       # Remove old backups
       # Clean cache
       pass
   ```

### Monitoring Tasks
1. **Performance Monitoring**
   - Resource usage
   - Response times
   - Error rates
   - Cache hit rates

2. **Security Monitoring**
   - Access logs
   - Error logs
   - Security events
   - System changes 
