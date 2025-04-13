import os
import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import requests
from alpaca.data.enums import DataFeed
from typing import Optional, Dict, Any

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import (
    StockBarsRequest,
    StockTradesRequest,
    StockQuotesRequest,
    StockLatestQuoteRequest,
    OptionChainRequest
)
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.trading.stream import TradingStream

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveMarketData:
    def __init__(self, symbol: str):
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")
        self.symbol = symbol.upper()
        self.historical_client = StockHistoricalDataClient(
            api_key=self.api_key,
            secret_key=self.secret_key
        )
        self.stream = TradingStream(self.api_key, self.secret_key)
        logger.info(f"[INIT] MarketData initialized for {self.symbol}")

    def get_bars(self, days: int = 30, interval: str = "hour"):
        """Get historical bars for the symbol."""
        try:
            now = datetime.now(ZoneInfo("America/New_York"))
            unit = TimeFrameUnit.Hour if interval == "hour" else TimeFrameUnit.Day
            req = StockBarsRequest(
                symbol_or_symbols=self.symbol,
                timeframe=TimeFrame(amount=1, unit=unit),
                start=now - timedelta(days=days)
            )
            return self.historical_client.get_stock_bars(req).df
        except Exception as e:
            logger.error(f"Error getting bars: {str(e)}")
            return None

    def get_trades(self, days: int = 5):
        """Get recent trades for the symbol."""
        try:
            now = datetime.now(ZoneInfo("America/New_York"))
            req = StockTradesRequest(
                symbol_or_symbols=self.symbol,
                start=now - timedelta(days=days)
            )
            return self.historical_client.get_stock_trades(req).df
        except Exception as e:
            logger.error(f"Error getting trades: {str(e)}")
            return None

    def get_quotes(self, days: int = 5):
        """Get recent quotes for the symbol."""
        try:
            now = datetime.now(ZoneInfo("America/New_York"))
            req = StockQuotesRequest(
                symbol_or_symbols=self.symbol,
                start=now - timedelta(days=days)
            )
            return self.historical_client.get_stock_quotes(req).df
        except Exception as e:
            logger.error(f"Error getting quotes: {str(e)}")
            return None

    def get_latest_quote(self):
        """Get the latest quote for the symbol."""
        try:
            # Use direct HTTP request to avoid SDK parameter issues
            url = f"https://data.alpaca.markets/v2/stocks/{self.symbol}/quotes/latest"
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key
            }
            params = {
                "feed": "iex"  # Explicitly set feed without limit parameter
            }
            
            logger.info(f"Making direct HTTP request to: {url}")
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            quote_data = response.json()
            logger.info(f"Quote data received: {quote_data}")
            
            return quote_data.get("quote")
        except Exception as e:
            logger.error(f"Error getting latest quote: {str(e)}")
            return None

    def get_options_snapshot(self):
        url = f"https://data.alpaca.markets/v1beta1/options/snapshots/{self.symbol}"
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json().get("snapshots", {})
        logger.info("\n🧠 Showing options chain snapshot...")

        for contract_symbol, info in list(data.items())[:10]:  # Limit to 10 for clarity
            quote = info.get("latestQuote", {})
            trade = info.get("latestTrade", {})
            greeks = info.get("greeks", {})

            print(f"\n📄 Symbol: {contract_symbol}")
            print(f"  Last Price: {trade.get('p')}")
            print(f"  IV: {greeks.get('implied_volatility', 'N/A')}")
            print(f"  Delta: {greeks.get('delta', 'N/A')}")
            print(f"  Theta: {greeks.get('theta', 'N/A')}")
            print(f"  Bid: {quote.get('bp')} | Ask: {quote.get('ap')}")
            print("-" * 40)

    async def _live_stream_handler(self, data):
        logger.info(f"[LIVE STREAM] {data}")

    async def stream_live_data(self):
        logger.info(f"📡 Streaming live data for {self.symbol}")
        await self.stream.subscribe_quotes(self._live_stream_handler, self.symbol)
        await self.stream.subscribe_trades(self._live_stream_handler, self.symbol)
        await self.stream.run()

    def get_options_chain(self, expiration: str = None):
        """Get options chain data formatted for RAG."""
        try:
            req = OptionChainRequest(symbol=self.symbol, expiration=expiration)
            chain = self.historical_client.get_option_chain(req)
            
            docs = []
            for option in chain.options:
                quote = option.latest_quote
                greeks = option.greeks
                
                text = (
                    f"Contract: {option.symbol}\n"
                    f"Type: {option.type}\n"
                    f"Strike: {option.strike_price}\n"
                    f"Expiration: {option.expiration_date}\n"
                    f"Last Price: {quote.last_price if quote else 'N/A'}\n"
                    f"Bid: {quote.bid_price if quote else 'N/A'}, Ask: {quote.ask_price if quote else 'N/A'}\n"
                    f"Delta: {greeks.delta if greeks else 'N/A'}, "
                    f"Theta: {greeks.theta if greeks else 'N/A'}, "
                    f"IV: {greeks.implied_volatility if greeks else 'N/A'}"
                )
                docs.append(text)
            
            return docs
        except Exception as e:
            logger.error(f"Error getting options chain: {str(e)}")
            return []

    def get_options_data(self, symbol: str, strike: Optional[float] = None, expiration: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get options data for a symbol."""
        try:
            # First get the options chain
            url = f"https://data.alpaca.markets/v2/stocks/{symbol}/options/chains"
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key
            }
            
            # Add query parameters if provided
            params = {}
            if strike:
                params['strike_price'] = strike
            if expiration:
                params['expiration'] = expiration
                
            logger.info(f"Fetching options chain for {symbol} with params: {params}")
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            chain_data = response.json()
            logger.info(f"Received chain data: {chain_data}")
            
            if not chain_data or not chain_data.get('chains'):
                logger.warning(f"No options chain found for {symbol}")
                return None
                
            # Get the first chain that matches our criteria
            chain = next(
                (c for c in chain_data['chains']
                 if (strike is None or c['strike_price'] == strike) and
                    (expiration is None or c['expiration_date'] == expiration)),
                chain_data['chains'][0]  # Default to first chain if no match
            )
            
            if not chain:
                logger.warning(f"No matching options chain found for {symbol}")
                return None
                
            # Get the latest quote for this option
            option_symbol = chain['symbol']
            quote_url = f"https://data.alpaca.markets/v2/stocks/{symbol}/options/quotes/latest"
            logger.info(f"Fetching quote for {option_symbol}")
            quote_response = requests.get(quote_url, headers=headers, params={'symbol': option_symbol})
            quote_response.raise_for_status()
            
            quote_data = quote_response.json()
            logger.info(f"Received quote data: {quote_data}")
            
            if not quote_data or not quote_data.get('quotes'):
                logger.warning(f"No quote data found for option {option_symbol}")
                return None
                
            quote = quote_data['quotes'][0]  # Get the first quote
            
            # Get the Greeks
            greeks_url = f"https://data.alpaca.markets/v2/stocks/{symbol}/options/greeks/latest"
            logger.info(f"Fetching Greeks for {option_symbol}")
            greeks_response = requests.get(greeks_url, headers=headers, params={'symbol': option_symbol})
            greeks_response.raise_for_status()
            
            greeks_data = greeks_response.json()
            logger.info(f"Received Greeks data: {greeks_data}")
            
            greeks = greeks_data.get('greeks', [{}])[0] if greeks_data and greeks_data.get('greeks') else {}
            
            # Extract and format the data
            result = {
                'type': 'call' if chain['option_type'] == 'C' else 'put',
                'strike': chain['strike_price'],
                'expiration': chain['expiration_date'],
                'last_price': quote.get('last_price'),
                'volume': quote.get('volume'),
                'open_interest': chain.get('open_interest'),
                'implied_volatility': greeks.get('implied_volatility'),
                'delta': greeks.get('delta'),
                'gamma': greeks.get('gamma'),
                'theta': greeks.get('theta'),
                'vega': greeks.get('vega')
            }
            
            logger.info(f"Returning options data: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting options data: {e}")
            return None


if __name__ == "__main__":
    symbol = "SPY"
    data = ComprehensiveMarketData(symbol)

    print("\n📊 Hourly Bars:")
    print(data.get_bars(days=5, interval="hour").head())

    print("\n📈 Daily Bars:")
    print(data.get_bars(days=30, interval="day").head())

    print("\n💬 Trades:")
    print(data.get_trades(days=3).head())

    print("\n📉 Quotes:")
    print(data.get_quotes(days=3).head())

    print("\n🔍 Latest Quote:")
    print(data.get_latest_quote())

    print("\n💎 Options Snapshot:")
    try:
        data.get_options_snapshot()
    except Exception as e:
        logger.warning(f"❌ Could not fetch options snapshot: {e}")

    print("\n📡 Starting live stream... Press Ctrl+C to exit")
    try:
        asyncio.run(data.stream_live_data())
    except KeyboardInterrupt:
        logger.info("Streaming stopped by user.")
