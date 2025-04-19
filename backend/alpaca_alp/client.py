import os
import logging
import time
import threading
import datetime as dt
from pytz import timezone
import re
import pandas as pd
import numpy as np
import redis
from typing import Dict, Any, List, Optional, Union, Tuple
from dotenv import load_dotenv
from sklearn.preprocessing import MinMaxScaler
import pinecone
from sklearn.feature_extraction.text import TfidfVectorizer

from alpaca.trading.client import TradingClient
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.historical.crypto import CryptoHistoricalDataClient
from alpaca.data.requests import (
    StockBarsRequest,
    StockLatestQuoteRequest,
    OptionChainRequest,
    OptionLatestQuoteRequest,
    CryptoBarsRequest,
    CryptoLatestQuoteRequest
)
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.trading.enums import AssetClass

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlpacaClient:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            # Initialize trading client (paper trading only)
            self.trading_client = TradingClient(
                os.getenv("ALPACA_API_KEY"),
                os.getenv("ALPACA_SECRET_KEY"),
                paper=True
            )
            
            # Initialize historical data clients
            self.stock_client = StockHistoricalDataClient(
                os.getenv("ALPACA_API_KEY"),
                os.getenv("ALPACA_SECRET_KEY")
            )
            self.option_client = OptionHistoricalDataClient(
                os.getenv("ALPACA_API_KEY"),
                os.getenv("ALPACA_SECRET_KEY")
            )
            self.crypto_client = CryptoHistoricalDataClient(
                os.getenv("ALPACA_API_KEY"),
                os.getenv("ALPACA_SECRET_KEY")
            )
            
            # Initialize Redis client
            self.redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            
            # Initialize Pinecone
            pinecone.init(
                api_key=os.getenv("PINECONE_API_KEY"),
                environment=os.getenv("PINECONE_ENVIRONMENT")
            )
            self.pinecone_index = pinecone.Index(os.getenv("PINECONE_INDEX_NAME"))
            
            # Test connections
            try:
                self.redis_client.ping()
                logger.info("Successfully connected to Redis")
                
                # Test Pinecone connection
                self.pinecone_index.describe_index_stats()
                logger.info("Successfully connected to Pinecone")
            except Exception as e:
                logger.error(f"Failed to initialize services: {e}")
                raise
            
            self.initialized = True

    def check_alpaca_status(self) -> bool:
        """Check if Alpaca API is accessible"""
        try:
            account_info = self.trading_client.get_account()
            return True
        except Exception as e:
            logger.error(f"Error checking Alpaca API status: {e}")
            return False

    def rate_limiter(self, key: str, limit: int, window: int) -> bool:
        """Implement rate limiting using Redis"""
        current_time = int(time.time())
        pipeline = self.redis_client.pipeline()
        pipeline.zadd(key, {current_time: current_time})
        pipeline.zremrangebyscore(key, 0, current_time - window)
        pipeline.zcard(key)
        pipeline.expire(key, window + 1)
        _, _, count, _ = pipeline.execute()
        return count <= limit

    def call_with_rate_limit(self, func, *args, **kwargs):
        """Execute a function with rate limiting"""
        key = "api_call_limit"
        limit = 200  # 200 calls per minute
        window = 60  # 60 seconds

        while True:
            if self.rate_limiter(key, limit, window):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in rate-limited call: {e}")
                    time.sleep(5)
            else:
                logger.warning("Rate limit exceeded. Retrying in 5 seconds...")
                time.sleep(5)

    def trading_hours(self, resume_time: int = 3, pause_time: int = 16) -> bool:
        """Check if current time is within trading hours"""
        current_time = dt.datetime.now(timezone('US/Eastern'))
        if dt.time(pause_time, 0) <= current_time.time():
            return False
        if current_time.time() <= dt.time(resume_time, 0):
            return False
        if current_time.weekday() >= 5:
            return False
        return True

    def parse_option_symbol(self, symbol: str) -> tuple:
        """Parse an option symbol into its components"""
        try:
            match = re.match(r'^([A-Za-z]+)(\d{6})([PC])(\d+)$', symbol)
            base_symbol, expiry, option_type, strike_price = match.groups()
            strike_price = int(strike_price) / 1000.0
            expiry = f"20{expiry[:2]}-{expiry[2:4]}-{expiry[4:6]}"
            expiry_date = dt.datetime.strptime(expiry, "%Y-%m-%d")
            days_to_expiry = (expiry_date - dt.datetime.now()).days + 1
            option_type = "put" if option_type == 'P' else "call"
            return base_symbol, strike_price, days_to_expiry, option_type
        except Exception as e:
            logger.error(f"Error parsing option symbol {symbol}: {e}")
            return None

    def get_market_data(self, symbol: str, timeframe: TimeFrame = None) -> Dict[str, Any]:
        """Get market data for a symbol"""
        try:
            if timeframe is None:
                timeframe = TimeFrame(1, TimeFrameUnit.Day)

            # Get bars data
            params = StockBarsRequest(
                symbol_or_symbols=symbol,
                start=dt.datetime.now(timezone('UTC')) - dt.timedelta(days=2),
                timeframe=timeframe,
                adjustment="split"
            )
            
            bars = self.stock_client.get_stock_bars(params)
            df = bars.df
            
            if df.empty:
                logger.warning(f"No data available for {symbol}")
                return self._get_default_market_response(symbol)

            # Get latest quote
            quote_params = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quote = self.stock_client.get_stock_latest_quote(quote_params)
            
            # Calculate metrics
            df["log_returns"] = np.log(df["close"]).diff()
            df["log_returns"] = df["log_returns"].fillna(0)
            value_at_risk = df["log_returns"].quantile(0.05)
            losses_below_var = df[df["log_returns"] < value_at_risk]["log_returns"]
            cvar = losses_below_var.mean()
            
            return {
                "symbol": symbol,
                "current_price": quote[symbol].ask_price if quote else df["close"].iloc[-1],
                "volume": df["volume"].iloc[-1],
                "timestamp": dt.datetime.now().isoformat(),
                "status": "success",
                "message": "Data retrieved successfully",
                "metrics": {
                    "value_at_risk": value_at_risk,
                    "cvar": cvar,
                    "log_returns": df["log_returns"].iloc[-1]
                }
            }
                
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return self._get_default_market_response(symbol)

    def get_options_data(self, symbol: str) -> Dict[str, Any]:
        """Get options data for a symbol"""
        try:
            # Get options chain for next 30 days
            end_date = dt.datetime.now(timezone('UTC')) + dt.timedelta(days=30)
            start_date = dt.datetime.now(timezone('UTC'))
            
            params = OptionChainRequest(
                symbol_or_symbols=symbol,
                start=start_date,
                end=end_date,
                limit=100
            )
            
            chain = self.option_client.get_option_chain(params)
            df = chain.df
            
            if df.empty:
                logger.warning(f"No options data available for {symbol}")
                return self._get_default_options_response(symbol)
            
            # Get latest quotes
            quote_params = OptionLatestQuoteRequest(symbol_or_symbols=df.index.tolist())
            quotes = self.option_client.get_option_latest_quote(quote_params)
            
            # Process the options chain
            processed_data = self._process_option_chain(df, quotes)
            
            return {
                "symbol": symbol,
                "timestamp": dt.datetime.now().isoformat(),
                "status": "success",
                "message": "Data retrieved successfully",
                "options_data": processed_data
            }
                
        except Exception as e:
            logger.error(f"Error fetching options data: {e}")
            return self._get_default_options_response(symbol)

    def _get_default_market_response(self, symbol: str) -> Dict[str, Any]:
        """Return default response for market data"""
        return {
            "symbol": symbol,
            "current_price": None,
            "volume": None,
            "timestamp": dt.datetime.now().isoformat(),
            "status": "partial",
            "message": "No market data available",
            "metrics": {
                "value_at_risk": None,
                "cvar": None,
                "log_returns": None
            }
        }

    def _get_default_options_response(self, symbol: str) -> Dict[str, Any]:
        """Return default response for options data"""
        return {
            "symbol": symbol,
            "timestamp": dt.datetime.now().isoformat(),
            "status": "partial",
            "message": "No options data available",
            "options_data": {
                "contracts": [],
                "metrics": {
                    "total_volume": 0,
                    "total_open_interest": 0,
                    "put_call_ratio": 0
                }
            }
        }

    def _process_option_chain(self, df: pd.DataFrame, quotes: Dict) -> Dict[str, Any]:
        """Process options chain data"""
        try:
            if df.empty:
                raise ValueError("Empty DataFrame provided")
            
            # Calculate moneyness and days to expiry
            df["moneyness"] = df["strike_price"] / df["underlying_price"]
            df["days_to_expiry"] = (df["expiration_date"] - dt.datetime.now(timezone('UTC'))).dt.days
            
            # Calculate Greeks
            df["delta"] = df["delta"].fillna(0)
            df["gamma"] = df["gamma"].fillna(0)
            df["theta"] = df["theta"].fillna(0)
            df["vega"] = df["vega"].fillna(0)
            df["rho"] = df["rho"].fillna(0)
            
            # Calculate metrics
            total_volume = df["volume"].sum()
            total_open_interest = df["open_interest"].sum()
            
            puts = df[df["option_type"] == "put"]
            calls = df[df["option_type"] == "call"]
            put_call_ratio = len(puts) / len(calls) if len(calls) > 0 else 0
            
            # Format contracts data
            contracts = []
            for idx, row in df.iterrows():
                contract = {
                    "symbol": idx,
                    "strike_price": row["strike_price"],
                    "expiration_date": row["expiration_date"].isoformat(),
                    "option_type": row["option_type"],
                    "moneyness": row["moneyness"],
                    "days_to_expiry": row["days_to_expiry"],
                    "volume": row["volume"],
                    "open_interest": row["open_interest"],
                    "greeks": {
                        "delta": row["delta"],
                        "gamma": row["gamma"],
                        "theta": row["theta"],
                        "vega": row["vega"],
                        "rho": row["rho"]
                    }
                }
                
                if idx in quotes:
                    quote = quotes[idx]
                    contract.update({
                        "bid_price": quote.bid_price,
                        "ask_price": quote.ask_price,
                        "mid_price": (quote.bid_price + quote.ask_price) / 2,
                        "spread": quote.ask_price - quote.bid_price
                    })
                
                contracts.append(contract)
            
            return {
                "contracts": contracts,
                "metrics": {
                    "total_volume": total_volume,
                    "total_open_interest": total_open_interest,
                    "put_call_ratio": put_call_ratio
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing options chain: {e}")
            return {
                "contracts": [],
                "metrics": {
                    "total_volume": 0,
                    "total_open_interest": 0,
                    "put_call_ratio": 0
                }
            }

    def format_for_llm(self, data: Dict[str, Any], data_type: str = "market") -> str:
        """Format data for LLM consumption"""
        try:
            sections = []
            
            if data_type == "market":
                sections.extend([
                    f"MARKET DATA OVERVIEW:",
                    f"Symbol: {data.get('symbol', 'N/A')}",
                    f"Current Price: ${data.get('current_price', 0):.2f}",
                    f"Volume: {data.get('volume', 0):,}",
                    f"Timestamp: {data.get('timestamp', 'N/A')}",
                    f"Status: {data.get('status', 'unknown')}"
                ])

                if 'metrics' in data:
                    metrics = data['metrics']
                    sections.extend([
                        "\nMARKET METRICS:",
                        f"Value at Risk: {metrics.get('value_at_risk', 0):.4f}",
                        f"Conditional VaR: {metrics.get('cvar', 0):.4f}",
                        f"Log Returns: {metrics.get('log_returns', 0):.4f}"
                    ])

            elif data_type == "options":
                sections.extend([
                    f"OPTIONS DATA OVERVIEW:",
                    f"Symbol: {data.get('symbol', 'N/A')}",
                    f"Timestamp: {data.get('timestamp', 'N/A')}",
                    f"Status: {data.get('status', 'unknown')}"
                ])

                if 'options_data' in data and 'metrics' in data['options_data']:
                    metrics = data['options_data']['metrics']
                    sections.extend([
                        "\nOPTIONS METRICS:",
                        f"Total Volume: {metrics.get('total_volume', 0):,}",
                        f"Total Open Interest: {metrics.get('total_open_interest', 0):,}",
                        f"Put/Call Ratio: {metrics.get('put_call_ratio', 0):.2f}"
                    ])

                    if 'contracts' in data['options_data']:
                        sections.append("\nTOP CONTRACTS:")
                        for contract in data['options_data']['contracts'][:5]:
                            sections.extend([
                                f"Contract: {contract.get('symbol', 'N/A')}",
                                f"  Type: {contract.get('option_type', 'N/A')}",
                                f"  Strike: ${contract.get('strike_price', 0):.2f}",
                                f"  Expiry: {contract.get('expiration_date', 'N/A')}",
                                f"  Moneyness: {contract.get('moneyness', 0):.2f}",
                                f"  Days to Expiry: {contract.get('days_to_expiry', 0)}",
                                f"  Greeks:",
                                f"    Delta: {contract.get('greeks', {}).get('delta', 0):.4f}",
                                f"    Gamma: {contract.get('greeks', {}).get('gamma', 0):.4f}",
                                f"    Theta: {contract.get('greeks', {}).get('theta', 0):.4f}",
                                f"    Vega: {contract.get('greeks', {}).get('vega', 0):.4f}",
                                f"    Rho: {contract.get('greeks', {}).get('rho', 0):.4f}"
                            ])

            return "\n".join(sections)
            
        except Exception as e:
            logger.error(f"Error formatting data for LLM: {e}")
            return f"Error formatting data: {str(e)}"

    def vectorize_for_training(self, data: Dict[str, Any], data_type: str = "market") -> Tuple[np.ndarray, Dict[str, Any]]:
        """Convert data into vectorized format for training"""
        try:
            if data_type == "market":
                # Extract numerical features
                features = {
                    'price': data.get('current_price', 0),
                    'volume': data.get('volume', 0),
                    'value_at_risk': data.get('metrics', {}).get('value_at_risk', 0),
                    'cvar': data.get('metrics', {}).get('cvar', 0),
                    'log_returns': data.get('metrics', {}).get('log_returns', 0)
                }
                
                # Convert to numpy array
                feature_array = np.array(list(features.values())).reshape(1, -1)
                
                # Normalize features
                scaler = MinMaxScaler()
                normalized_features = scaler.fit_transform(feature_array)
                
                return normalized_features, features

            elif data_type == "options":
                if 'options_data' not in data:
                    raise ValueError("No options data available")
                
                # Extract numerical features
                features = {
                    'total_volume': data['options_data']['metrics'].get('total_volume', 0),
                    'total_open_interest': data['options_data']['metrics'].get('total_open_interest', 0),
                    'put_call_ratio': data['options_data']['metrics'].get('put_call_ratio', 0)
                }
                
                # Add contract-level features
                contracts = data['options_data'].get('contracts', [])
                if contracts:
                    for i, contract in enumerate(contracts[:5]):  # Use top 5 contracts
                        features.update({
                            f'contract_{i}_strike': contract.get('strike_price', 0),
                            f'contract_{i}_moneyness': contract.get('moneyness', 0),
                            f'contract_{i}_days_to_expiry': contract.get('days_to_expiry', 0),
                            f'contract_{i}_delta': contract.get('greeks', {}).get('delta', 0),
                            f'contract_{i}_gamma': contract.get('greeks', {}).get('gamma', 0),
                            f'contract_{i}_theta': contract.get('greeks', {}).get('theta', 0),
                            f'contract_{i}_vega': contract.get('greeks', {}).get('vega', 0),
                            f'contract_{i}_rho': contract.get('greeks', {}).get('rho', 0)
                        })
                
                # Convert to numpy array
                feature_array = np.array(list(features.values())).reshape(1, -1)
                
                # Normalize features
                scaler = MinMaxScaler()
                normalized_features = scaler.fit_transform(feature_array)
                
                return normalized_features, features

        except Exception as e:
            logger.error(f"Error vectorizing data: {e}")
            return np.array([]), {}

    def get_training_data(self, symbol: str, lookback_days: int = 30) -> Dict[str, Any]:
        """Get historical data for training purposes"""
        try:
            # Get historical market data
            timeframe = TimeFrame(1, TimeFrameUnit.Day)
            start_date = dt.datetime.now(timezone('UTC')) - dt.timedelta(days=lookback_days)
            
            params = StockBarsRequest(
                symbol_or_symbols=symbol,
                start=start_date,
                timeframe=timeframe,
                adjustment="split"
            )
            
            bars = self.stock_client.get_stock_bars(params)
            df = bars.df
            
            if df.empty:
                raise ValueError(f"No historical data available for {symbol}")
            
            # Calculate technical indicators
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['rsi'] = self._calculate_rsi(df['close'])
            df['macd'], df['macd_signal'] = self._calculate_macd(df['close'])
            
            # Calculate returns and volatility
            df['returns'] = df['close'].pct_change()
            df['volatility'] = df['returns'].rolling(window=20).std()
            
            # Get options data
            options_data = self.get_options_data(symbol)
            
            # Vectorize the data
            market_vectors, market_features = self.vectorize_for_training(
                self.get_market_data(symbol),
                "market"
            )
            options_vectors, options_features = self.vectorize_for_training(
                options_data,
                "options"
            )
            
            return {
                'symbol': symbol,
                'market_data': {
                    'raw': df.to_dict('records'),
                    'vectors': market_vectors.tolist(),
                    'features': market_features
                },
                'options_data': {
                    'raw': options_data,
                    'vectors': options_vectors.tolist(),
                    'features': options_features
                },
                'timestamp': dt.datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting training data: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'timestamp': dt.datetime.now().isoformat()
            }

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series]:
        """Calculate MACD"""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        return macd, signal_line

# Create a singleton instance
api = AlpacaClient() 
