import aiohttp
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Ollama configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://35.202.133.28:11434")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3:latest")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

# Log the Ollama configuration
logger.info(f"Ollama host: {OLLAMA_HOST}")
logger.info(f"Ollama chat model: {OLLAMA_CHAT_MODEL}")
logger.info(f"Ollama embed model: {OLLAMA_EMBED_MODEL}")

# Ensure we're using the correct host
if "ollama" in OLLAMA_HOST:
    OLLAMA_HOST = "http://35.202.133.28:11434"
    logger.info(f"Updated Ollama host to: {OLLAMA_HOST}")

async def get_embeddings(text: str) -> list:
    """Get embeddings for text using the Ollama embeddings model."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OLLAMA_HOST}/api/embeddings",
                json={
                    "model": OLLAMA_EMBED_MODEL,
                    "prompt": text
                }
            ) as response:
                response.raise_for_status()
                result = await response.json()
                return result["embedding"]
    except Exception as e:
        logger.error(f"Error getting embeddings: {str(e)}")
        raise

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

    # Handle simple greetings and general queries
    query_lower = query.lower()
    if query_lower in ["hello", "hi", "hey"]:
        symbol = "AAPL"  # Default symbol
        if isinstance(market_context, dict) and "current_data" in market_context:
            symbol = market_context.get("current_data", {}).get("symbol", "AAPL")
        return f"""Hey there! 👋 I'm Robin AI, your friendly trading assistant. I can help you analyze {symbol}'s market data, technical indicators, and options strategies. What would you like to know?"""
    
    if query_lower in ["how are you", "how's it going", "what's up"]:
        return "I'm doing great! Ready to help you with your trading questions. What's on your mind?"
    
    if query_lower in ["thanks", "thank you", "thx"]:
        return "You're welcome! Let me know if you need anything else. 😊"
    
    if query_lower in ["bye", "goodbye", "see you"]:
        return "Goodbye! Feel free to come back if you have more questions. Happy trading! 🚀"
    
    if len(query.strip()) < 3:
        return "I'd love to help, but could you please provide a bit more detail in your question?"

    # Format market context if it's a dictionary
    formatted_market_context = ""
    if isinstance(market_context, dict):
        current = market_context.get("current_data", {})
        daily = market_context.get("daily_data", {})
        tech = market_context.get("technical_indicators", {})
        
        # Get latest daily data
        latest_daily = {}
        if daily and "dates" in daily and len(daily["dates"]) > 0:
            latest_idx = -1
            latest_daily = {
                "date": daily["dates"][latest_idx],
                "open": daily["open"][latest_idx],
                "high": daily["high"][latest_idx],
                "low": daily["low"][latest_idx],
                "close": daily["close"][latest_idx],
                "volume": daily["volume"][latest_idx]
            }
        
        formatted_market_context = f"""MARKET OVERVIEW:
Symbol: {current.get("symbol", "AAPL")}
Current Price: ${current.get("price", 0):.2f}
Timestamp: {current.get("timestamp", "N/A")}
Market Status: Open
Exchange: Unknown
Asset Class: Unknown

PRICE ACTION:
Open: ${latest_daily.get("open", 0):.2f}
High: ${latest_daily.get("high", 0):.2f}
Low: ${latest_daily.get("low", 0):.2f}
Close: ${latest_daily.get("close", 0):.2f}
Volume: {latest_daily.get("volume", 0):,}
VWAP: ${current.get("vwap", 0):.2f}

TECHNICAL INDICATORS:
SMA 20: {tech.get("trend", {}).get("sma_20", [0])[-1]:.2f}
SMA 50: {tech.get("trend", {}).get("sma_50", [0])[-1]:.2f}
EMA 20: {tech.get("trend", {}).get("ema_20", [0])[-1]:.2f}
Trend Strength: {tech.get("trend", {}).get("trend_strength", 0):.2f}%
RSI: {tech.get("momentum", {}).get("rsi", [0])[-1]:.1f}
MACD: {tech.get("momentum", {}).get("macd", {}).get("macd_line", [0])[-1]:.2f}
MACD Signal: {tech.get("momentum", {}).get("macd", {}).get("signal_line", [0])[-1]:.2f}
MACD Histogram: {tech.get("momentum", {}).get("macd", {}).get("histogram", [0])[-1]:.2f}
Bollinger Bands:
  Upper: ${tech.get("volatility", {}).get("bollinger_bands", {}).get("upper", [0])[-1]:.2f}
  Middle: ${tech.get("volatility", {}).get("bollinger_bands", {}).get("middle", [0])[-1]:.2f}
  Lower: ${tech.get("volatility", {}).get("bollinger_bands", {}).get("lower", [0])[-1]:.2f}"""
    else:
        formatted_market_context = market_context

    prompt = f"""You are Robin AI, a friendly and knowledgeable trading assistant specializing in technical analysis. Your task is to analyze the provided market data and technical indicators to provide actionable insights.

MARKET DATA:
{formatted_market_context}

KNOWLEDGE BASE:
{context}

QUERY: {query}

RESPONSE GUIDELINES:
1. Start with a clear analysis of the current market conditions
2. Focus on interpreting the technical indicators:
   - RSI: Analyze oversold/overbought conditions (below 30 is oversold, above 70 is overbought)
   - MACD: Identify trend direction and momentum (positive histogram = bullish, negative = bearish)
   - Bollinger Bands: Assess volatility and potential price movements (price near upper band = overbought, near lower band = oversold)
   - Moving Averages: Determine trend strength and support/resistance levels (price above = bullish, below = bearish)
3. Provide specific price levels and indicators to watch
4. Be concise and actionable
5. Use markdown formatting for clarity
6. Include relevant emojis where appropriate

IMPORTANT: Your response MUST incorporate the specific technical indicators provided above. If you don't see the indicators, say so explicitly.

RESPONSE FORMAT:
## Current Market Analysis
[Brief overview of current market conditions]

## Technical Indicators Analysis
### RSI Analysis
[RSI interpretation]

### MACD Analysis
[MACD interpretation]

### Bollinger Bands Analysis
[Bollinger Bands interpretation]

### Moving Averages Analysis
[Moving Averages interpretation]

## Key Levels to Watch
[Support and resistance levels]

## Trading Recommendation
[Actionable trading recommendation based on the analysis]"""

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_ctx": 4096,
                        "num_thread": 12,
                        "temperature": 0.8,  # Slightly increased for more conversational tone
                        "use_mlock": True,
                        "top_p": 0.9,
                        "repeat_penalty": 1.1
                    }
                }
            ) as response:
                response.raise_for_status()
                result = await response.json()
                answer = result["response"]
                
                # Enhanced response cleaning
                answer = answer.replace("\n\n", "\n")
                answer = answer.replace("  ", " ")
                answer = answer.strip()
                
                # Ensure proper markdown formatting
                answer = answer.replace("1. ", "## 1. ")
                answer = answer.replace("2. ", "## 2. ")
                answer = answer.replace("3. ", "## 3. ")
                answer = answer.replace("4. ", "## 4. ")
                answer = answer.replace("a) ", "### a) ")
                answer = answer.replace("b) ", "### b) ")
                answer = answer.replace("c) ", "### c) ")
                
                # Ensure proper bullet points
                answer = answer.replace("- ", "\n- ")
                
                # Add proper spacing between sections
                answer = answer.replace("##", "\n##")
                
                # Ensure the response is not empty
                if not answer.strip():
                    answer = "I'd love to help, but I need a bit more context. Could you rephrase your question?"
                
                logger.info("Successfully generated response")
                return answer
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return "Oops! I ran into a small issue. Could you try asking your question again? 😊"
