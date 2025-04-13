import requests
import logging

logger = logging.getLogger(__name__)

def call_ollama(query: str, context: str, market_context: str, model: str = "llama3"):
    """Generate response using both RAG context and market data."""
    # Log the inputs
    logger.info("Generating response with:")
    logger.info(f"Query: {query}")
    logger.info(f"RAG Context length: {len(context)} chars")
    logger.info(f"Market Context: {market_context}")

    prompt = f"""You are a trading assistant. Use both the provided market data and knowledge base to answer the question.

Current Market Data:
{market_context}

Relevant Knowledge:
{context}

Question: {query}

Guidelines:
1. Always reference the current market data when relevant
2. Use the knowledge base to provide trading strategies and insights
3. If the market is closed, mention this and focus on historical data
4. For options-related questions, consider the volatility data
5. Be specific about prices, percentages, and timeframes
"""

    try:
        response = requests.post(
            f"http://host.docker.internal:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_ctx": 2048,
                    "num_thread": 4,
                    "num_gpu": 1,
                    "temperature": 0.7
                }
            }
        )
        response.raise_for_status()
        answer = response.json()["response"]
        logger.info("Successfully generated response")
        return answer
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return f"Error generating response: {str(e)}"
