from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from query_interpreter import QueryInterpreter
from alpaca_alp.market_data import ComprehensiveMarketData
from rag.retriever import retrieve_relevant_chunks
from rag.ollama_client import call_ollama

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
query_interpreter = QueryInterpreter()

class Query(BaseModel):
    text: str

async def generate_response(query: str, context: str) -> str:
    """Generate a response using Ollama."""
    try:
        response = call_ollama(
            query=query,
            context=context,
            market_context=""  # Market context is already included in the context parameter
        )
        return response
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "I apologize, but I encountered an error while generating a response."

@app.post("/query")
async def query(query: Query):
    """Process a natural language query about trading."""
    try:
        # Initialize market data client
        market_data = ComprehensiveMarketData(symbol="AAPL")  # Default symbol, will be updated
        
        # Interpret the query
        interpreted = query_interpreter.interpret(query.text)
        
        # If the query is ambiguous, ask for clarification
        if interpreted.get('needs_clarification'):
            return {
                "status": "clarification_needed",
                "message": interpreted['clarification_message'],
                "options": interpreted.get('clarification_options', [])
            }
        
        # Try to get market data first
        market_context = None
        try:
            market_context = _generate_market_context(market_data, interpreted)
        except Exception as e:
            logger.warning(f"Failed to get market data: {e}")
            # Continue to RAG fallback
        
        # If we have market data, use it
        if market_context and market_context != "No market data available":
            # Get relevant chunks from RAG for additional context
            relevant_chunks = retrieve_relevant_chunks(query.text)
            
            # Combine market data with RAG context
            full_context = f"Market Data:\n{market_context}\n\nAdditional Context:\n{relevant_chunks}"
            
            # Generate response using Ollama
            response = await generate_response(
                query=query.text,
                context=full_context
            )
            
            return {
                "status": "success",
                "response": response,
                "market_context": market_context,
                "source": "live_data"
            }
        
        # Fallback to RAG if market data fails
        logger.info("Falling back to RAG for general knowledge")
        relevant_chunks = retrieve_relevant_chunks(query.text)
        
        # Generate response using Ollama with RAG context
        response = await generate_response(
            query=query.text,
            context=relevant_chunks
        )
        
        return {
            "status": "success",
            "response": response,
            "market_context": "Using general knowledge from RAG",
            "source": "rag"
        }
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return {
            "status": "error",
            "message": "An error occurred while processing your query. Please try again."
        }

@staticmethod
def _generate_market_context(market_data: ComprehensiveMarketData, interpreted: Dict[str, Any]) -> str:
    """Generate market context based on interpreted query."""
    context_parts = []
    
    # Handle options-specific queries
    if 'options' in interpreted['intent']:
        # Get options data
        options_data = market_data.get_options_data(
            symbol=interpreted['symbol'],
            strike=interpreted.get('parameters', {}).get('strike_price'),
            expiration=interpreted.get('parameters', {}).get('expiration')
        )
        
        if options_data:
            # Add Greeks if requested
            greeks = interpreted.get('parameters', {}).get('greeks', [])
            if 'delta' in greeks:
                context_parts.append(f"Delta: {options_data.get('delta', 'N/A')}")
            if 'gamma' in greeks:
                context_parts.append(f"Gamma: {options_data.get('gamma', 'N/A')}")
            if 'theta' in greeks:
                context_parts.append(f"Theta: {options_data.get('theta', 'N/A')}")
            if 'vega' in greeks:
                context_parts.append(f"Vega: {options_data.get('vega', 'N/A')}")
            
            # Add basic options info
            context_parts.append(f"Option Type: {options_data.get('type', 'N/A')}")
            context_parts.append(f"Strike Price: ${options_data.get('strike', 'N/A')}")
            context_parts.append(f"Expiration: {options_data.get('expiration', 'N/A')}")
            context_parts.append(f"Last Price: ${options_data.get('last_price', 'N/A')}")
            context_parts.append(f"Volume: {options_data.get('volume', 'N/A')}")
            context_parts.append(f"Open Interest: {options_data.get('open_interest', 'N/A')}")
            context_parts.append(f"Implied Volatility: {options_data.get('implied_volatility', 'N/A')}%")
        else:
            context_parts.append("No options data available for the specified parameters")
    else:
        # Add basic price information for non-options queries
        quote = market_data.get_latest_quote()
        if quote:
            context_parts.append(f"Current price of {interpreted['symbol']}: ${quote.get('ask_price', 'N/A')}")
        
        # Add timeframe-specific data
        timeframe = interpreted['timeframe']
        if timeframe['timeframe'] != 'day':
            bars = market_data.get_bars(
                days=timeframe['days'],
                interval=timeframe['timeframe']
            )
            if bars is not None and not bars.empty:
                context_parts.append(f"{timeframe['timeframe'].capitalize()} data for the last {timeframe['days']} days available")
        
        # Add technical indicators
        for indicator in interpreted.get('technical_indicators', []):
            if indicator['name'] == 'RSI':
                # Calculate RSI
                pass
            elif indicator['name'] == 'MACD':
                # Calculate MACD
                pass
            # Add more indicator calculations
        
        # Add strategy components
        if interpreted.get('strategy_components'):
            strategy_type = interpreted['strategy_components'].get('strategy_type')
            if strategy_type:
                context_parts.append(f"Strategy type: {strategy_type}")
        
        # Add risk parameters
        if interpreted.get('risk_parameters'):
            risk_info = []
            if 'stop_loss' in interpreted['risk_parameters']:
                risk_info.append(f"Stop loss: {interpreted['risk_parameters']['stop_loss']}%")
            if 'take_profit' in interpreted['risk_parameters']:
                risk_info.append(f"Take profit: {interpreted['risk_parameters']['take_profit']}%")
            if risk_info:
                context_parts.append("Risk parameters: " + ", ".join(risk_info))
    
    return "\n".join(context_parts) if context_parts else "No market data available"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
