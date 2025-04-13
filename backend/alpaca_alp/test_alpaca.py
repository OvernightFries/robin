import os
from pathlib import Path  
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from current directory
env_path = Path(__file__).resolve().parents[1] / ".env"
logger.info(f"Loading .env from: {env_path}")
load_dotenv(dotenv_path=env_path)

# Verify environment variables
api_key = os.getenv('ALPACA_API_KEY')
secret_key = os.getenv('ALPACA_SECRET_KEY')
if not api_key or not secret_key:
    logger.error("Missing Alpaca API credentials in .env file")
    exit(1)

def test_alpaca_connection():
    """Test Alpaca API connection and data retrieval."""
    try:
        # Initialize clients
        logger.info("Initializing Alpaca clients...")
        data_client = StockHistoricalDataClient(
            api_key=api_key,
            secret_key=secret_key
        )
        trading_client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=True
        )
        logger.info("Successfully initialized Alpaca clients")

        # Check market status
        clock = trading_client.get_clock()
        logger.info(f"Market is {'open' if clock.is_open else 'closed'}")
        if not clock.is_open:
            logger.warning("Market is closed - testing with historical data only")
            logger.info(f"Next market open: {clock.next_open}")
            logger.info(f"Next market close: {clock.next_close}")

        # Test historical data retrieval first (works even when market is closed)
        logger.info("Fetching historical data...")
        symbol = "SPY"
        request = StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=TimeFrame.Day,
            start=datetime.now() - timedelta(days=30),
            end=datetime.now()
        )
        bars = data_client.get_stock_bars(request)
        
        if symbol in bars and len(bars[symbol]) > 0:
            prices = [bar.close for bar in bars[symbol]]
            returns = [(prices[i] - prices[i-1])/prices[i-1] for i in range(1, len(prices))]
            volatility = (sum(r**2 for r in returns) / len(returns))**0.5 * (252**0.5)
            logger.info(f"30-day Annualized Volatility: {volatility:.2%}")
            logger.info(f"Last closing price: ${prices[-1]}")
        else:
            logger.error(f"No historical data found for {symbol}")

        # Only try to get real-time quotes if market is open
        if clock.is_open:
            logger.info(f"Fetching latest quote for {symbol}...")
            request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
            latest_quote = data_client.get_stock_latest_quote(request)
            
            if symbol in latest_quote:
                quote = latest_quote[symbol]
                logger.info(f"Current {symbol} Price: ${quote.last_price}")
                logger.info(f"Bid: ${quote.bid_price}")
                logger.info(f"Ask: ${quote.ask_price}")
            else:
                logger.error(f"No real-time data found for {symbol}")
        else:
            logger.info("Skipping real-time quotes (market is closed)")

        return True
    except Exception as e:
        logger.error(f"Error testing Alpaca connection: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        if hasattr(e, 'status_code'):
            logger.error(f"Status code: {e.status_code}")
        if hasattr(e, 'response'):
            logger.error(f"Response: {e.response}")
        return False

if __name__ == "__main__":
    success = test_alpaca_connection()
    if success:
        logger.info("✅ All tests passed successfully!")
    else:
        logger.error("❌ Tests failed!") 
