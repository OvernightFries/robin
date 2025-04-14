import aiohttp
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Ollama configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3")

async def call_ollama(query: str, context: str, market_context: str, model: str = None):
    """Generate response using both RAG context and market data."""
    # Log the inputs
    logger.info("Generating response with:")
    logger.info(f"Query: {query}")
    logger.info(f"RAG Context length: {len(context)} chars")
    logger.info(f"Market Context: {market_context}")

    # Use environment variable for model if not specified
    if model is None:
        model = OLLAMA_CHAT_MODEL

    prompt = f"""You are Robin AI, an advanced trading assistant powered by Llama 3. Your task is to provide detailed, accurate, and actionable trading insights by combining real-time market data with your extensive knowledge base.

Current Market Data:
{market_context}

Relevant Trading Knowledge:
{context}

Question: {query}

Guidelines for Response:
1. Always start by acknowledging the current market conditions and prices
2. Use the provided knowledge base to explain trading concepts and strategies
3. When discussing options:
   - Reference current implied volatility
   - Consider the Greeks (delta, gamma, theta, vega)
   - Suggest appropriate strategies based on market conditions
4. For technical analysis:
   - Reference current indicators and patterns
   - Explain the significance of the patterns
   - Provide specific price levels and targets
5. For fundamental analysis:
   - Reference key metrics from the market data
   - Compare with historical values
   - Consider sector and market context
6. Always provide specific, actionable recommendations when appropriate
7. Use markdown formatting for better readability
8. Include relevant calculations and formulas when explaining concepts
9. Maintain a professional and educational tone
10. If uncertain about any aspect, clearly state the limitations

Format your response with clear sections and bullet points for better readability."""

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_ctx": 4096,  # Increased context window for Llama 3
                        "num_thread": 12,
                        "temperature": 0.7,
                        "use_mlock": True,
                        "top_p": 0.9,
                        "repeat_penalty": 1.1
                    }
                }
            ) as response:
                response.raise_for_status()
                result = await response.json()
                answer = result["response"]
                logger.info("Successfully generated response")
                return answer
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return f"Error generating response: {str(e)}"
