# Robin AI Backend

This is the backend service for the Robin AI application, providing market data and options analysis through Alpaca API and vectorized data storage using Pinecone.

## Local Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on `.env.example` and fill in your credentials

4. Run the server:
```bash
uvicorn main:app --reload
```

## Railway Deployment

1. Create a new project on Railway
2. Connect your GitHub repository
3. Add the following environment variables in Railway's dashboard:
   - ALPACA_API_KEY
   - ALPACA_SECRET_KEY
   - ALPACA_BASE_URL
   - PINECONE_API_KEY
   - PINECONE_ENVIRONMENT
   - PINECONE_INDEX_NAME
   - PINECONE_REALTIME_INDEX
   - CORS_ORIGIN

4. Deploy the project

## API Documentation

Once deployed, visit `/docs` endpoint for interactive API documentation.

## Environment Variables

- `ALPACA_API_KEY`: Your Alpaca API key
- `ALPACA_SECRET_KEY`: Your Alpaca secret key
- `ALPACA_BASE_URL`: Alpaca API base URL (default: https://paper-api.alpaca.markets/v2)
- `PINECONE_API_KEY`: Your Pinecone API key
- `PINECONE_ENVIRONMENT`: Your Pinecone environment
- `PINECONE_INDEX_NAME`: Name of the Pinecone index for document storage
- `PINECONE_REALTIME_INDEX`: Name of the Pinecone index for real-time data
- `CORS_ORIGIN`: CORS origin setting (default: *)
- `PORT`: Server port (default: 8000) 
