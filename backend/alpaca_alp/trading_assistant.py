import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TradingAssistant:
    def __init__(self):
        self.client = StockHistoricalDataClient(
            api_key=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY')
        )
        logger.info("✅ TradingAssistant initialized successfully")

    def get_market_snapshot(self, symbol: str) -> Optional[Dict]:
        """Get a comprehensive market snapshot for a symbol."""
        try:
            # Get latest quote
            quote_req = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
            latest_quote = self.client.get_stock_latest_quote(quote_req)

            if symbol not in latest_quote:
                logger.error(f"❌ No quote data found for {symbol}")
                return None

            quote = latest_quote[symbol]

            # ✅ Get historical bars directly (no StockBarsRequest)
            bars = self.client.get_stock_bars(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=datetime.now() - timedelta(days=30),
                end=datetime.now()
            ).data

            symbol_bars = bars.get(symbol)
            volatility = None

            if symbol_bars and len(symbol_bars) > 1:
                prices = [bar.close for bar in symbol_bars]
                returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]
                volatility = (sum(r ** 2 for r in returns) / len(returns)) ** 0.5 * (252 ** 0.5)

            return {
                'symbol': symbol,
                'current_price': quote.last_price,
                'bid': quote.bid_price,
                'ask': quote.ask_price,
                'volume': quote.volume,
                'timestamp': quote.timestamp,
                'volatility': volatility
            }

        except Exception as e:
            logger.error(f"❌ Error getting market snapshot for {symbol}: {str(e)}")
            return None

    def analyze_market_conditions(self, symbol: str) -> Optional[str]:
        """Analyze market conditions and provide trading insights."""
        try:
            snapshot = self.get_market_snapshot(symbol)
            if not snapshot:
                return None

            analysis = [f"📈 Market Analysis for {symbol}:"]
            analysis.append(f"Current Price: ${snapshot['current_price']}")
            analysis.append(f"Bid-Ask Spread: ${snapshot['ask'] - snapshot['bid']:.2f}")

            if snapshot['volatility'] is not None:
                analysis.append(f"30-day Annualized Volatility: {snapshot['volatility']:.2%}")
                if snapshot['volatility'] > 0.3:
                    analysis.append("⚠️ High volatility detected — consider hedging or options strategies.")
                else:
                    analysis.append("✅ Low volatility — directional trades may be favorable.")
            else:
                analysis.append("ℹ️ Not enough data to calculate volatility.")

            return "\n".join(analysis)

        except Exception as e:
            logger.error(f"❌ Error analyzing market conditions: {str(e)}")
            return None

# Debug/test entry point
if __name__ == "__main__":
    assistant = TradingAssistant()
    symbol = "SPY"
    analysis = assistant.analyze_market_conditions(symbol)

    if analysis:
        logger.info(analysis)
    else:
        logger.error(f"❌ Failed to analyze market conditions for {symbol}")
