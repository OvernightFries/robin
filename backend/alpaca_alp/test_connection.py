from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_connection():
    """Test basic Alpaca API connection."""
    try:
        # Initialize client
        client = StockHistoricalDataClient(
            api_key=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY')
        )
        logger.info("Successfully initialized Alpaca client")

        # Test getting latest quote for SPY
        request = StockLatestQuoteRequest(symbol_or_symbols=["SPY"])
        latest_quote = client.get_stock_latest_quote(request)
        
        if "SPY" in latest_quote:
            quote = latest_quote["SPY"]
            logger.info(f"Current SPY Price: ${quote.last_price}")
            logger.info(f"Bid: ${quote.bid_price}")
            logger.info(f"Ask: ${quote.ask_price}")
            return True
        else:
            logger.error("No data found for SPY")
            return False
    except Exception as e:
        logger.error(f"Error testing connection: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_connection()
    if success:
        logger.info("✅ Connection test successful!")
    else:
        logger.error("❌ Connection test failed!") 
