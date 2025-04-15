# API Documentation

## Overview
This document provides detailed information about the REST and WebSocket APIs available in the Robin AI platform.

## REST API

### Base URL
```
http://localhost:8000
```

### Authentication
All API endpoints require authentication using a Bearer token:
```
Authorization: Bearer <token>
```

### Endpoints

#### Health Check
```http
GET /health
```
- **Description**: Check service health status
- **Response**:
  ```json
  {
    "status": "healthy",
    "services": {
      "redis": "healthy",
      "pinecone": "healthy",
      "ollama": "healthy"
    }
  }
  ```

#### Stock Analysis
```http
POST /analyze
```
- **Description**: Analyze a stock symbol
- **Request Body**:
  ```json
  {
    "symbol": "AAPL",
    "query": "options data"
  }
  ```
- **Response**:
  ```json
  {
    "symbol": "AAPL",
    "analysis": {
      "price": 150.25,
      "volume": 1000000,
      "indicators": {
        "rsi": 65.5,
        "macd": 2.5
      },
      "options": {
        "chain": [...],
        "greeks": {...}
      }
    }
  }
  ```

#### Options Data
```http
GET /options/{symbol}
```
- **Description**: Get options chain data
- **Path Parameters**:
  - `symbol`: Stock symbol
- **Response**:
  ```json
  {
    "symbol": "AAPL",
    "chain": [
      {
        "expiration": "2024-03-15",
        "strike": 150,
        "type": "call",
        "price": 2.5,
        "volume": 1000,
        "open_interest": 500
      }
    ]
  }
  ```

#### Chat Interaction
```http
POST /chat
```
- **Description**: Send a chat message
- **Request Body**:
  ```json
  {
    "message": "What's the RSI for AAPL?",
    "context": {
      "symbol": "AAPL"
    }
  }
  ```
- **Response**:
  ```json
  {
    "response": "The RSI for AAPL is currently 65.5, indicating it may be overbought.",
    "context": {
      "symbol": "AAPL",
      "indicators": {
        "rsi": 65.5
      }
    }
  }
  ```

## WebSocket API

### Base URL
```
ws://localhost:8000
```

### Endpoints

#### Market Data Stream
```javascript
ws://localhost:8000/ws/market
```
- **Description**: Real-time market data updates
- **Messages**:
  ```json
  {
    "type": "market_update",
    "data": {
      "symbol": "AAPL",
      "price": 150.25,
      "volume": 1000000,
      "timestamp": "2024-02-20T12:00:00Z"
    }
  }
  ```

#### Chat Stream
```javascript
ws://localhost:8000/ws/chat
```
- **Description**: Real-time chat updates
- **Messages**:
  ```json
  {
    "type": "chat_message",
    "data": {
      "role": "assistant",
      "content": "The RSI for AAPL is 65.5",
      "timestamp": "2024-02-20T12:00:00Z"
    }
  }
  ```

## Data Models

### Market Data
```python
class MarketData(BaseModel):
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    indicators: Dict[str, float]
```

### Options Data
```python
class OptionsData(BaseModel):
    symbol: str
    expiration: date
    strike: float
    type: str
    price: float
    volume: int
    open_interest: int
```

### Chat Message
```python
class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime
    context: Dict[str, Any]
```

### Technical Indicators
```python
class TechnicalIndicators(BaseModel):
    rsi: float
    macd: float
    macd_signal: float
    macd_hist: float
    sma_20: float
    sma_50: float
    sma_200: float
```

## Error Responses

### Common Errors
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description",
    "details": {
      "field": "error details"
    }
  }
}
```

### Error Codes
- `INVALID_REQUEST`: Invalid request parameters
- `UNAUTHORIZED`: Authentication required
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `RATE_LIMITED`: Too many requests
- `SERVICE_ERROR`: Internal server error

## Rate Limiting

### Limits
- REST API: 100 requests per minute
- WebSocket: 1000 messages per minute

### Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1620000000
```

## Pagination

### Query Parameters
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 10)

### Response Headers
```
X-Total-Count: 100
X-Page-Count: 10
X-Current-Page: 1
```

## WebSocket Protocol

### Connection
1. **Establish Connection**
   ```javascript
   const ws = new WebSocket('ws://localhost:8000/ws/market');
   ```

2. **Authentication**
   ```javascript
   ws.send(JSON.stringify({
     type: 'auth',
     token: 'your-token'
   }));
   ```

3. **Subscribe to Symbols**
   ```javascript
   ws.send(JSON.stringify({
     type: 'subscribe',
     symbols: ['AAPL', 'MSFT']
   }));
   ```

### Message Types
1. **Market Updates**
   ```json
   {
     "type": "market_update",
     "data": {
       "symbol": "AAPL",
       "price": 150.25
     }
   }
   ```

2. **Error Messages**
   ```json
   {
     "type": "error",
     "error": {
       "code": "ERROR_CODE",
       "message": "Error description"
     }
   }
   ```

3. **System Messages**
   ```json
   {
     "type": "system",
     "message": "Connection established"
   }
   ```

## Examples

### REST API Example
```python
import requests

# Health check
response = requests.get('http://localhost:8000/health')
print(response.json())

# Stock analysis
response = requests.post('http://localhost:8000/analyze', json={
    'symbol': 'AAPL',
    'query': 'options data'
})
print(response.json())
```

### WebSocket Example
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/market');

ws.onopen = () => {
    // Authenticate
    ws.send(JSON.stringify({
        type: 'auth',
        token: 'your-token'
    }));

    // Subscribe to symbols
    ws.send(JSON.stringify({
        type: 'subscribe',
        symbols: ['AAPL', 'MSFT']
    }));
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log(message);
};
``` 
