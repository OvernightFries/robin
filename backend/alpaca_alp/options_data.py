import os
import asyncio
import json
import websockets
import msgpack
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.requests import OptionChainRequest, OptionLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
import pytz
from typing import Dict, Any

load_dotenv()
logger = logging.getLogger(__name__)

API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_SECRET_KEY")

REAL_OPRA_SYMBOLS = [
    "AAPL240419C00190000",
    "AAPL240419P00190000"
]

FAKE_OPRA_SYMBOLS = ["FAKEPACA"]

# Updated WebSocket URLs
REAL_WS_URL = "wss://stream.data.alpaca.markets/v2/iex"
TEST_WS_URL = "wss://stream.data.alpaca.markets/v2/iex"  # Use same endpoint for testing

class OptionsData:
    def __init__(self, symbol: str, api_key: str = None, api_secret: str = None):
        """Initialize the OptionsData instance."""
        self.symbol = symbol.upper()
        self.api_key = api_key or os.getenv("ALPACA_API_KEY")
        self.api_secret = api_secret or os.getenv("ALPACA_SECRET_KEY")
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca API key and secret key must be provided")
            
        # Initialize Option Historical Data Client
        self.api = OptionHistoricalDataClient(self.api_key, self.api_secret)
        
    async def get_options_data(self):
        """Fetch current options data with enhanced processing"""
        try:
            # Get options chain for next 30 days
            end_date = datetime.now(pytz.UTC) + timedelta(days=30)
            start_date = datetime.now(pytz.UTC)
            
            # Get options chain
            params = OptionChainRequest(
                symbol_or_symbols=self.symbol,
                start=start_date,
                end=end_date,
                limit=100  # Limit to 100 contracts
            )
            
            chain = self.api.get_option_chain(params)
            df = chain.df
            
            if df.empty:
                logger.warning(f"No options data available for {self.symbol}")
                return self._get_default_response("No options data available")
            
            # Get latest quotes for all contracts
            quote_params = OptionLatestQuoteRequest(symbol_or_symbols=df.index.tolist())
            quotes = self.api.get_option_latest_quote(quote_params)
            
            # Process the options chain
            processed_data = self._process_option_chain(df, quotes)
            
            return {
                "symbol": self.symbol,
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "message": "Data retrieved successfully",
                "options_data": processed_data
            }
                
        except Exception as e:
            logger.error(f"Error fetching options data: {str(e)}")
            return self._get_default_response(str(e))

    def _get_default_response(self, message: str) -> Dict[str, Any]:
        """Return a default response when data is unavailable."""
        return {
            "symbol": self.symbol,
            "timestamp": datetime.now().isoformat(),
            "status": "partial",
            "message": message,
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
        """Process the options chain data and calculate metrics"""
        try:
            if df.empty:
                raise ValueError("Empty DataFrame provided")
            
            # Calculate moneyness and days to expiry
            df["moneyness"] = df["strike_price"] / df["underlying_price"]
            df["days_to_expiry"] = (df["expiration_date"] - datetime.now(pytz.UTC)).dt.days
            
            # Calculate Greeks and other metrics
            df["delta"] = df["delta"].fillna(0)
            df["gamma"] = df["gamma"].fillna(0)
            df["theta"] = df["theta"].fillna(0)
            df["vega"] = df["vega"].fillna(0)
            df["rho"] = df["rho"].fillna(0)
            
            # Calculate volume and open interest metrics
            total_volume = df["volume"].sum()
            total_open_interest = df["open_interest"].sum()
            
            # Calculate put/call ratio
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
                
                # Add latest quote if available
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
            logger.error(f"Error processing options chain: {str(e)}")
            return {
                "contracts": [],
                "metrics": {
                    "total_volume": 0,
                    "total_open_interest": 0,
                    "put_call_ratio": 0
                }
            }

    def format_for_rag(self, data: Dict[str, Any]) -> str:
        """Format options data for RAG in a structured, vectorizable format."""
        try:
            sections = []
            
            # Get current timestamp
            timestamp = datetime.now().isoformat()
            
            # Options Overview Section
            overview = [
                f"OPTIONS OVERVIEW:",
                f"Symbol: {self.symbol}",
                f"Timestamp: {timestamp}",
                f"Status: {data.get('status', 'unknown')}"
            ]
            sections.append("\n".join(overview))

            # Options Metrics Section
            if 'options_data' in data and 'metrics' in data['options_data']:
                metrics = ["OPTIONS METRICS:"]
                m = data['options_data']['metrics']
                metrics.extend([
                    f"Total Volume: {m.get('total_volume', 0):,}",
                    f"Total Open Interest: {m.get('total_open_interest', 0):,}",
                    f"Put/Call Ratio: {m.get('put_call_ratio', 0):.2f}"
                ])
                sections.append("\n".join(metrics))

            # Contracts Section
            if 'options_data' in data and 'contracts' in data['options_data']:
                contracts = ["OPTIONS CONTRACTS:"]
                for contract in data['options_data']['contracts'][:5]:  # Show first 5 contracts
                    contracts.extend([
                        f"Contract: {contract.get('symbol', 'N/A')}",
                        f"  Type: {contract.get('option_type', 'N/A')}",
                        f"  Strike: ${contract.get('strike_price', 0):.2f}",
                        f"  Expiry: {contract.get('expiration_date', 'N/A')}",
                        f"  Moneyness: {contract.get('moneyness', 0):.2f}",
                        f"  Days to Expiry: {contract.get('days_to_expiry', 0)}",
                        f"  Volume: {contract.get('volume', 0):,}",
                        f"  Open Interest: {contract.get('open_interest', 0):,}",
                        f"  Greeks:",
                        f"    Delta: {contract.get('greeks', {}).get('delta', 0):.4f}",
                        f"    Gamma: {contract.get('greeks', {}).get('gamma', 0):.4f}",
                        f"    Theta: {contract.get('greeks', {}).get('theta', 0):.4f}",
                        f"    Vega: {contract.get('greeks', {}).get('vega', 0):.4f}",
                        f"    Rho: {contract.get('greeks', {}).get('rho', 0):.4f}"
                    ])
                sections.append("\n".join(contracts))

            return "\n\n".join(sections)
            
        except Exception as e:
            logger.error(f"Error formatting options data for RAG: {str(e)}")
            return f"Error formatting options data: {str(e)}"

def is_market_open_now():
    now = datetime.utcnow()
    return now.weekday() < 5 and 13 <= now.hour <= 20  # 9AM–4PM ET in UTC

async def stream_opra(ws_url, symbols, use_msgpack=True):
    async with websockets.connect(ws_url) as ws:
        # Auth
        auth_msg = {
            "action": "auth",
            "key": API_KEY,
            "secret": API_SECRET
        }
        await ws.send(msgpack.packb(auth_msg) if use_msgpack else json.dumps(auth_msg))

        raw_auth = await ws.recv()
        auth_response = (
            msgpack.unpackb(raw_auth, strict_map_key=False)
            if use_msgpack else
            json.loads(raw_auth)
        )
        print("✅ Auth:", auth_response)

        # Subscribe
        sub_msg = {"action": "subscribe", "quotes": symbols}
        await ws.send(msgpack.packb(sub_msg) if use_msgpack else json.dumps(sub_msg))

        raw_sub = await ws.recv()
        sub_response = (
            msgpack.unpackb(raw_sub, strict_map_key=False)
            if use_msgpack else
            json.loads(raw_sub)
        )
        print("📡 Subscribed:", sub_response)

        # Listen
        print("📈 Streaming:", symbols)
        while True:
            msg = await ws.recv()
            decoded = (
                msgpack.unpackb(msg, strict_map_key=False)
                if use_msgpack else
                json.loads(msg)
            )
            print(decoded)


async def main():
    if is_market_open_now():
        print("🟢 Market open — streaming real OPRA")
        await stream_opra(REAL_WS_URL, REAL_OPRA_SYMBOLS, use_msgpack=True)
    else:
        print("🟡 Market closed — streaming FAKEPACA for dev")
        await stream_opra(TEST_WS_URL, FAKE_OPRA_SYMBOLS, use_msgpack=False)

if __name__ == "__main__":
    asyncio.run(main())
