import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
from zoneinfo import ZoneInfo

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketData:
    def __init__(self, symbol: str, api_key: str = None, secret_key: str = None):
        """Initialize the MarketData instance."""
        self.symbol = symbol.upper()
        self.api_key = api_key or os.getenv("ALPACA_API_KEY")
        self.secret_key = secret_key or os.getenv("ALPACA_SECRET_KEY")
        
        if not self.api_key or not self.secret_key:
            raise ValueError("Alpaca API key and secret key must be provided")
            
        # Initialize REST client for stocks
        self.api = tradeapi.REST(
            self.api_key,
            self.secret_key,
            base_url='https://paper-api.alpaca.markets'
        )
        
    async def get_market_data(self) -> Dict[str, Any]:
        """Get comprehensive market data."""
        try:
            # Get current market data
            try:
                current_trade = self.api.get_latest_trade(self.symbol)
                current_quote = self.api.get_latest_quote(self.symbol)
                current_data = {
                    "price": current_trade.price,
                    "volume": current_trade.size,
                    "bid": current_quote.bid_price,  # bid price
                    "ask": current_quote.ask_price,  # ask price
                    "bid_size": current_quote.bid_size,  # bid size
                    "ask_size": current_quote.ask_size,  # ask size
                    "timestamp": datetime.now().strftime('%Y-%m-%d')
                }
            except Exception as e:
                logger.warning(f"Could not get current market data: {str(e)}")
                # Get the last close price instead
                last_bars = self.api.get_bars(self.symbol, timeframe='1D', limit=1).df
                if not last_bars.empty:
                    current_data = {
                        "price": last_bars['close'].iloc[-1],
                        "volume": last_bars['volume'].iloc[-1],
                        "bid": last_bars['close'].iloc[-1],
                        "ask": last_bars['close'].iloc[-1],
                        "bid_size": 0,
                        "ask_size": 0,
                        "timestamp": last_bars.index[-1].strftime('%Y-%m-%d'),
                        "market_closed": True
                    }
                else:
                    raise ValueError(f"No historical data available for {self.symbol}")
            
            # Get historical data with error handling
            try:
                # Get data for the last 30 days
                end_date = datetime.now(ZoneInfo('America/New_York'))
                start_date = end_date - timedelta(days=30)
                
                daily_data = self.api.get_bars(
                    self.symbol,
                    timeframe='1D',
                    start=start_date.strftime('%Y-%m-%d'),
                    end=end_date.strftime('%Y-%m-%d')
                ).df
                
                # Get data for the last 7 days
                start_date = end_date - timedelta(days=7)
                hourly_data = self.api.get_bars(
                    self.symbol,
                    timeframe='1H',
                    start=start_date.strftime('%Y-%m-%d'),
                    end=end_date.strftime('%Y-%m-%d')
                ).df
                
                # Get data for the last day
                start_date = end_date - timedelta(days=1)
                minute_data = self.api.get_bars(
                    self.symbol,
                    timeframe='15Min',
                    start=start_date.strftime('%Y-%m-%d'),
                    end=end_date.strftime('%Y-%m-%d')
                ).df
                
                # Check if we got any data
                if daily_data.empty:
                    logger.error(f"No daily data available for {self.symbol}")
                    raise ValueError(f"No daily data available for {self.symbol}")
                
                # Log data info
                logger.info(f"Daily data shape: {daily_data.shape}, columns: {daily_data.columns.tolist()}")
                logger.info(f"Sample of daily data:\n{daily_data.head()}")
                
                # Ensure required columns exist
                required_columns = ['close', 'high', 'low', 'open', 'volume']
                for df in [daily_data, hourly_data, minute_data]:
                    if not df.empty:  # Only check non-empty DataFrames
                        missing_cols = [col for col in required_columns if col not in df.columns]
                        if missing_cols:
                            raise ValueError(f"Missing required columns: {missing_cols}")
                
                # Calculate technical indicators
                technical_indicators = self._calculate_technical_indicators(daily_data)
                
                return {
                    "current_data": current_data,
                    "daily_data": {
                        "dates": daily_data.index.strftime('%Y-%m-%d').tolist(),
                        "open": daily_data['open'].tolist(),
                        "high": daily_data['high'].tolist(),
                        "low": daily_data['low'].tolist(),
                        "close": daily_data['close'].tolist(),
                        "volume": daily_data['volume'].tolist()
                    },
                    "hourly_data": {
                        "dates": hourly_data.index.strftime('%Y-%m-%d %H:%M').tolist() if not hourly_data.empty else [],
                        "open": hourly_data['open'].tolist() if not hourly_data.empty else [],
                        "high": hourly_data['high'].tolist() if not hourly_data.empty else [],
                        "low": hourly_data['low'].tolist() if not hourly_data.empty else [],
                        "close": hourly_data['close'].tolist() if not hourly_data.empty else [],
                        "volume": hourly_data['volume'].tolist() if not hourly_data.empty else []
                    },
                    "minute_data": {
                        "dates": minute_data.index.strftime('%Y-%m-%d %H:%M').tolist() if not minute_data.empty else [],
                        "open": minute_data['open'].tolist() if not minute_data.empty else [],
                        "high": minute_data['high'].tolist() if not minute_data.empty else [],
                        "low": minute_data['low'].tolist() if not minute_data.empty else [],
                        "close": minute_data['close'].tolist() if not minute_data.empty else [],
                        "volume": minute_data['volume'].tolist() if not minute_data.empty else []
                    },
                    "technical_indicators": technical_indicators
                }
                
            except Exception as e:
                logger.error(f"Error getting historical data: {str(e)}")
                raise ValueError(f"Failed to get historical data for {self.symbol}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error getting market data: {str(e)}")
            raise
            
    def _calculate_technical_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators using numpy."""
        try:
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
            volume = data['volume'].values
            
            # Calculate SMA
            def sma(data, period):
                return np.convolve(data, np.ones(period)/period, mode='valid')
            
            # Calculate EMA
            def ema(data, period):
                return pd.Series(data).ewm(span=period, adjust=False).mean().values
            
            # Calculate RSI
            def rsi(data, period=14):
                delta = np.diff(data)
                gain = np.where(delta > 0, delta, 0)
                loss = np.where(delta < 0, -delta, 0)
                avg_gain = np.mean(gain[:period])
                avg_loss = np.mean(loss[:period])
                rs = avg_gain / avg_loss if avg_loss != 0 else 0
                rsi_value = 100 - (100 / (1 + rs))
                return [rsi_value] * len(data)  # Return a list of the same length as input data
            
            # Calculate MACD
            def macd(data, fast=12, slow=26, signal=9):
                ema_fast = ema(data, fast)
                ema_slow = ema(data, slow)
                macd_line = ema_fast - ema_slow
                signal_line = ema(macd_line, signal)
                return macd_line, signal_line, macd_line - signal_line
            
            # Calculate Bollinger Bands
            def bollinger_bands(data, period=20, std_dev=2):
                sma_20 = sma(data, period)
                std = np.std(data[-period:])
                upper = sma_20 + (std * std_dev)
                lower = sma_20 - (std * std_dev)
                return upper, sma_20, lower
            
            return {
                "trend": {
                    "sma_20": sma(close, 20).tolist(),
                    "sma_50": sma(close, 50).tolist(),
                    "sma_200": sma(close, 200).tolist(),
                    "ema_20": ema(close, 20).tolist(),
                    "ema_50": ema(close, 50).tolist(),
                    "trend_strength": ((sma(close, 20)[-1] - sma(close, 50)[-1]) / sma(close, 50)[-1]) * 100
                },
                "momentum": {
                    "rsi": rsi(close),
                    "macd": {
                        "macd_line": macd(close)[0].tolist(),
                        "signal_line": macd(close)[1].tolist(),
                        "histogram": macd(close)[2].tolist()
                    }
                },
                "volatility": {
                    "bollinger_bands": {
                        "upper": bollinger_bands(close)[0].tolist(),
                        "middle": bollinger_bands(close)[1].tolist(),
                        "lower": bollinger_bands(close)[2].tolist()
                    }
                },
                "volume": {
                    "volume_sma": sma(volume, 20).tolist()
                }
            }
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {str(e)}")
            raise
            
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
                f"Current Price: ${data.get('current_data', {}).get('price', 0):.2f}",
                f"Timestamp: {timestamp}",
                f"Market Status: {'Closed' if data.get('current_data', {}).get('market_closed', False) else 'Open'}",
                f"Exchange: {data.get('current_data', {}).get('exchange', 'Unknown')}",
                f"Asset Class: {data.get('current_data', {}).get('asset_class', 'Unknown')}"
            ]
            sections.append("\n".join(overview))

            # Price Action Section
            price_action = ["PRICE ACTION:"]
            if 'daily_data' in data:
                daily = data['daily_data']
                price_action.extend([
                    f"Open: ${daily.get('open', [0])[-1]:.2f}",
                    f"High: ${daily.get('high', [0])[-1]:.2f}",
                    f"Low: ${daily.get('low', [0])[-1]:.2f}",
                    f"Close: ${daily.get('close', [0])[-1]:.2f}",
                    f"Volume: {daily.get('volume', [0])[-1]:,}",
                    f"VWAP: ${daily.get('vwap', 0):.2f}"
                ])
            sections.append("\n".join(price_action))

            # Technical Indicators Section
            if 'technical_indicators' in data:
                indicators = ["TECHNICAL INDICATORS:"]
                tech = data['technical_indicators']
                if 'trend' in tech:
                    indicators.extend([
                        f"SMA 20: {tech['trend'].get('sma_20', [0])[-1]:.2f}",
                        f"SMA 50: {tech['trend'].get('sma_50', [0])[-1]:.2f}",
                        f"EMA 20: {tech['trend'].get('ema_20', [0])[-1]:.2f}",
                        f"Trend Strength: {tech['trend'].get('trend_strength', 0):.2f}%"
                    ])
                if 'momentum' in tech:
                    momentum = tech['momentum']
                    indicators.extend([
                        f"RSI: {momentum.get('rsi', [0])[-1]:.1f}",
                        f"MACD: {momentum.get('macd', {}).get('macd_line', [0])[-1]:.2f}",
                        f"MACD Signal: {momentum.get('macd', {}).get('signal_line', [0])[-1]:.2f}",
                        f"MACD Histogram: {momentum.get('macd', {}).get('histogram', [0])[-1]:.2f}"
                    ])
                if 'volatility' in tech:
                    volatility = tech['volatility']
                    bb = volatility.get('bollinger_bands', {})
                    indicators.extend([
                        f"Bollinger Bands:",
                        f"  Upper: ${bb.get('upper', [0])[-1]:.2f}",
                        f"  Middle: ${bb.get('middle', [0])[-1]:.2f}",
                        f"  Lower: ${bb.get('lower', [0])[-1]:.2f}"
                    ])
                sections.append("\n".join(indicators))

            return "\n\n".join(sections)
            
        except Exception as e:
            logger.error(f"Error formatting market data for RAG: {str(e)}")
            return f"Error formatting market data: {str(e)}"
