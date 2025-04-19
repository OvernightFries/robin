import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
import pytz
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketData:
    def __init__(self, symbol: str, api_key: str = None, api_secret: str = None):
        """Initialize the MarketData instance for stock market data."""
        self.symbol = symbol.upper()
        self.api_key = api_key or os.getenv("ALPACA_API_KEY")
        self.api_secret = api_secret or os.getenv("ALPACA_SECRET_KEY")
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca API key and secret key must be provided")
            
        # Initialize Stock Historical Data Client
        self.api = StockHistoricalDataClient(self.api_key, self.api_secret)
        
    async def get_market_data(self):
        """Fetch current stock market data with enhanced processing"""
        try:
            # Get last 2 days of data
            end_date = datetime.now(pytz.UTC)
            start_date = end_date - timedelta(days=2)
            
            # Get bars data
            params = StockBarsRequest(
                symbol_or_symbols=self.symbol,
                start=start_date,
                timeframe=TimeFrame(1, TimeFrameUnit.Day),
                adjustment="split"
            )
            
            bars = self.api.get_stock_bars(params)
            df = bars.df
            
            if df.empty:
                logger.warning(f"No data available for {self.symbol}")
                return self._get_default_response("No market data available")
            
            # Get latest quote for current price
            quote_params = StockLatestQuoteRequest(symbol_or_symbols=self.symbol)
            quote = self.api.get_stock_latest_quote(quote_params)
            
            # Calculate metrics
            df["log_returns"] = np.log(df["close"]).diff()
            df["log_returns"] = df["log_returns"].fillna(0)
            value_at_risk = df["log_returns"].quantile(0.05)
            losses_below_var = df[df["log_returns"] < value_at_risk]["log_returns"]
            cvar = losses_below_var.mean()
            
            # Calculate technical indicators
            indicators = self._calculate_technical_indicators(df)
            
            return {
                "symbol": self.symbol,
                "current_price": quote[self.symbol].ask_price if quote else df["close"].iloc[-1],
                "volume": df["volume"].iloc[-1],
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "message": "Data retrieved successfully",
                "metrics": {
                    "value_at_risk": value_at_risk,
                    "cvar": cvar,
                    "log_returns": df["log_returns"].iloc[-1],
                    "technical_indicators": indicators
                }
            }
                
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            return self._get_default_response(str(e))

    def _get_default_response(self, message: str) -> Dict[str, Any]:
        """Return a default response when data is unavailable."""
        return {
            "symbol": self.symbol,
            "current_price": None,
            "volume": None,
            "timestamp": datetime.now().isoformat(),
            "status": "partial",
            "message": message,
            "metrics": {
                "value_at_risk": None,
                "cvar": None,
                "log_returns": None,
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
        }

    def _calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate technical indicators from price data"""
        try:
            if df.empty:
                raise ValueError("Empty DataFrame provided")
            
            # Calculate SMAs
            sma_20 = df["close"].rolling(window=20).mean()
            sma_50 = df["close"].rolling(window=50).mean()
            
            # Calculate EMA
            ema_20 = df["close"].ewm(span=20, adjust=False).mean()
            
            # Calculate RSI
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Calculate MACD
            exp1 = df["close"].ewm(span=12, adjust=False).mean()
            exp2 = df["close"].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            
            # Calculate Bollinger Bands
            sma = df["close"].rolling(window=20).mean()
            std = df["close"].rolling(window=20).std()
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)
            
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
            logger.error(f"Error calculating technical indicators: {str(e)}")
            return {
                "sma_20": None,
                "sma_50": None,
                "ema_20": None,
                "rsi": None,
                "macd": None,
                "macd_signal": None,
                "bollinger_upper": None,
                "bollinger_lower": None
            }

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
                f"Volume: {data.get('volume', 0):,}"
            ]
            sections.append("\n".join(overview))

            # Metrics Section
            if 'metrics' in data:
                metrics = ["METRICS:"]
                m = data['metrics']
                metrics.extend([
                    f"Value at Risk: {m.get('value_at_risk', 0):.4f}",
                    f"CVaR: {m.get('cvar', 0):.4f}",
                    f"Log Returns: {m.get('log_returns', 0):.4f}"
                ])
                sections.append("\n".join(metrics))

            # Technical Indicators Section
            if 'metrics' in data and 'technical_indicators' in data['metrics']:
                indicators = ["TECHNICAL INDICATORS:"]
                tech = data['metrics']['technical_indicators']
                indicators.extend([
                    f"SMA 20: {tech.get('sma_20', 0):.2f}",
                    f"SMA 50: {tech.get('sma_50', 0):.2f}",
                    f"EMA 20: {tech.get('ema_20', 0):.2f}",
                    f"RSI: {tech.get('rsi', 0):.1f}",
                    f"MACD: {tech.get('macd', 0):.2f}",
                    f"MACD Signal: {tech.get('macd_signal', 0):.2f}",
                    f"Bollinger Bands:",
                    f"  Upper: ${tech.get('bollinger_upper', 0):.2f}",
                    f"  Lower: ${tech.get('bollinger_lower', 0):.2f}"
                ])
                sections.append("\n".join(indicators))

            return "\n\n".join(sections)
            
        except Exception as e:
            logger.error(f"Error formatting market data for RAG: {str(e)}")
            return f"Error formatting market data: {str(e)}"
