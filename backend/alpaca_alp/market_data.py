import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
from zoneinfo import ZoneInfo
import time
import asyncio
from alpaca_trade_api.rest import REST, TimeFrame
import aiohttp

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketData:
    def __init__(self, symbol: str, api_key: str = None, api_secret: str = None):
        """Initialize the MarketData instance."""
        self.symbol = symbol.upper()
        self.api_key = api_key or os.getenv("ALPACA_API_KEY")
        self.api_secret = api_secret or os.getenv("ALPACA_SECRET_KEY")
        self.base_url = os.getenv("ALPACA_BASE_URL", "https://api.alpaca.markets/v2")
        self.data_url = os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets/v2")
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca API key and secret key must be provided")
            
        # Initialize REST client
        self.api = REST(
            self.api_key,
            self.api_secret,
            base_url=self.base_url,
            api_version='v2'
        )
        
    async def get_market_data(self):
        """Fetch current market data with retry logic"""
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                # Get current market data using the data endpoint
                headers = {
                    "APCA-API-KEY-ID": self.api_key,
                    "APCA-API-SECRET-KEY": self.api_secret
                }
                
                # Get last 2 days of data to ensure we have the latest
                end_date = datetime.now()
                start_date = end_date - timedelta(days=2)
                
                async with aiohttp.ClientSession() as session:
                    try:
                        # Use the exact URL format from Alpaca API
                        url = f"{self.data_url}/stocks/{self.symbol}/bars"
                        params = {
                            "timeframe": "1D",
                            "start": start_date.strftime("%Y-%m-%d"),
                            "end": end_date.strftime("%Y-%m-%d")
                        }
                        
                        logger.info(f"Requesting: {url} with params: {params}")
                        
                        async with session.get(
                            url,
                            params=params,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=30)
                        ) as response:
                            if response.status != 200:
                                logger.warning(f"Failed to fetch data: {await response.text()}")
                                return self._get_default_response("API returned non-200 status")
                                
                            data = await response.json()
                            if not data.get("bars"):
                                logger.warning(f"No data available for {self.symbol}")
                                return self._get_default_response("No market data available")
                                
                            # Convert to DataFrame
                            df = pd.DataFrame(data["bars"])
                            df["t"] = pd.to_datetime(df["t"])
                            df.set_index("t", inplace=True)
                            
                            return {
                                "symbol": self.symbol,
                                "current_price": df["c"].iloc[-1] if not df.empty else None,
                                "volume": df["v"].iloc[-1] if not df.empty else None,
                                "timestamp": datetime.now().isoformat(),
                                "status": "success",
                                "message": "Data retrieved successfully"
                            }
                    except asyncio.TimeoutError:
                        logger.warning(f"Timeout while fetching data for {self.symbol}")
                        return self._get_default_response("Request timed out")
                
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Error fetching market data after {max_retries} attempts: {str(e)}")
                    return self._get_default_response(f"Failed after {max_retries} attempts")
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff

    def _get_default_response(self, message: str) -> Dict[str, Any]:
        """Return a default response when data is unavailable."""
        return {
            "symbol": self.symbol,
            "current_price": None,
            "volume": None,
            "timestamp": datetime.now().isoformat(),
            "status": "partial",
            "message": message,
            "historical_data": [],
            "technical_indicators": {
                "sma_20": None,
                "sma_50": None,
                "ema_20": None,
                "rsi": None,
                "macd": None,
                "macd_signal": None,
                "bollinger_upper": None,
                "bollinger_lower": None
            }
        }

    async def _get_historical_data(self):
        """Fetch historical market data with retry logic"""
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                # Get daily data
                daily_data = self.api.get_bars(
                    self.symbol,
                    timeframe=TimeFrame.Day,
                    limit=200
                ).df
                
                if daily_data.empty:
                    raise ValueError(f"No historical data available for {self.symbol}")
                
                # Get hourly data
                hourly_data = self.api.get_bars(
                    self.symbol,
                    timeframe=TimeFrame.Hour,
                    limit=24
                ).df
                
                # Get minute data
                minute_data = self.api.get_bars(
                    self.symbol,
                    timeframe=TimeFrame.Minute,
                    limit=60
                ).df
                
                return pd.concat([daily_data, hourly_data, minute_data])
                
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Error fetching historical data after {max_retries} attempts: {str(e)}")
                    raise
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff

    def _calculate_technical_indicators(self, df):
        """Calculate technical indicators with error handling"""
        try:
            if df.empty:
                raise ValueError("Empty DataFrame provided")
            
            if not all(col in df.columns for col in ['close', 'high', 'low', 'volume']):
                raise ValueError("Missing required columns in DataFrame")
            
            if len(df) < 200:
                raise ValueError("Insufficient data points for calculations")
            
            # Calculate indicators
            sma_20 = self._calculate_sma(df['close'], 20)
            sma_50 = self._calculate_sma(df['close'], 50)
            ema_20 = self._calculate_ema(df['close'], 20)
            rsi = self._calculate_rsi(df['close'])
            macd, signal = self._calculate_macd(df['close'])
            upper_band, lower_band = self._calculate_bollinger_bands(df['close'])
            
            return {
                "sma_20": sma_20.iloc[-1],
                "sma_50": sma_50.iloc[-1],
                "ema_20": ema_20.iloc[-1],
                "rsi": rsi.iloc[-1],
                "macd": macd.iloc[-1],
                "macd_signal": signal.iloc[-1],
                "bollinger_upper": upper_band.iloc[-1],
                "bollinger_lower": lower_band.iloc[-1]
            }
            
        except Exception as e:
            print(f"Error calculating technical indicators: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _calculate_sma(self, data, window):
        """Calculate Simple Moving Average"""
        try:
            return data.rolling(window=window).mean()
        except Exception as e:
            print(f"Error calculating SMA: {str(e)}")
            return pd.Series([np.nan] * len(data))

    def _calculate_ema(self, data, window):
        """Calculate Exponential Moving Average"""
        try:
            return data.ewm(span=window, adjust=False).mean()
        except Exception as e:
            print(f"Error calculating EMA: {str(e)}")
            return pd.Series([np.nan] * len(data))

    def _calculate_rsi(self, data, window=14):
        """Calculate Relative Strength Index"""
        try:
            delta = data.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        except Exception as e:
            print(f"Error calculating RSI: {str(e)}")
            return pd.Series([np.nan] * len(data))

    def _calculate_macd(self, data, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        try:
            exp1 = data.ewm(span=fast, adjust=False).mean()
            exp2 = data.ewm(span=slow, adjust=False).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=signal, adjust=False).mean()
            return macd, signal_line
        except Exception as e:
            print(f"Error calculating MACD: {str(e)}")
            return pd.Series([np.nan] * len(data)), pd.Series([np.nan] * len(data))

    def _calculate_bollinger_bands(self, data, window=20, num_std=2):
        """Calculate Bollinger Bands"""
        try:
            sma = data.rolling(window=window).mean()
            std = data.rolling(window=window).std()
            upper_band = sma + (std * num_std)
            lower_band = sma - (std * num_std)
            return upper_band, lower_band
        except Exception as e:
            print(f"Error calculating Bollinger Bands: {str(e)}")
            return pd.Series([np.nan] * len(data)), pd.Series([np.nan] * len(data))

    def format_for_rag(self, data: Dict[str, Any]) -> str:
        """Format market data for RAG in a structured, vectorizable format."""
        try:
            sections = []
            
            # Get current timestamp in NY timezone
            current_time = datetime.now(ZoneInfo('America/New_York'))
            timestamp = current_time.isoformat()
            
            # Market Overview Section
            overview = [
                f"MARKET OVERVIEW:",
                f"Symbol: {self.symbol}",
                f"Current Price: ${data.get('current_price', 0):.2f}",
                f"Timestamp: {timestamp}",
                f"Market Status: {'Closed' if data.get('current_data', {}).get('market_closed', False) else 'Open'}",
                f"Exchange: {data.get('current_data', {}).get('exchange', 'Unknown')}",
                f"Asset Class: {data.get('current_data', {}).get('asset_class', 'Unknown')}"
            ]
            sections.append("\n".join(overview))

            # Price Action Section
            price_action = ["PRICE ACTION:"]
            if 'historical_data' in data:
                historical_data = data['historical_data']
                price_action.extend([
                    f"Open: ${historical_data[0]['open']:.2f}",
                    f"High: ${historical_data[0]['high']:.2f}",
                    f"Low: ${historical_data[0]['low']:.2f}",
                    f"Close: ${historical_data[0]['close']:.2f}",
                    f"Volume: {historical_data[0]['volume']:,}",
                    f"VWAP: ${historical_data[0]['vwap']:.2f}"
                ])
            sections.append("\n".join(price_action))

            # Technical Indicators Section
            if 'technical_indicators' in data:
                indicators = ["TECHNICAL INDICATORS:"]
                tech = data['technical_indicators']
                indicators.extend([
                    f"SMA 20: {tech['sma_20']:.2f}",
                    f"SMA 50: {tech['sma_50']:.2f}",
                    f"EMA 20: {tech['ema_20']:.2f}",
                    f"RSI: {tech['rsi']:.1f}",
                    f"MACD: {tech['macd']:.2f}",
                    f"MACD Signal: {tech['macd_signal']:.2f}",
                    f"Bollinger Bands:",
                    f"  Upper: ${tech['bollinger_upper']:.2f}",
                    f"  Lower: ${tech['bollinger_lower']:.2f}"
                ])
                sections.append("\n".join(indicators))

            return "\n\n".join(sections)
            
        except Exception as e:
            logger.error(f"Error formatting market data for RAG: {str(e)}")
            return f"Error formatting market data: {str(e)}"
