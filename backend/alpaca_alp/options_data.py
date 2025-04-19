import os
import asyncio
import json
import websockets
import msgpack
import aiohttp
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_SECRET_KEY")

REAL_OPRA_SYMBOLS = [
    "AAPL240419C00190000",
    "AAPL240419P00190000"
]

FAKE_OPRA_SYMBOLS = ["FAKEPACA"]

REAL_WS_URL = "wss://stream.data.alpaca.markets/v1beta1/opra"
TEST_WS_URL = "wss://stream.data.alpaca.markets/v2/test"

HEADERS = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": API_SECRET,
    "Content-Type": "application/json"
}

BASE_URL_V2 = "https://api.alpaca.markets/v2/options/contracts"

class OptionsData:
    def __init__(self, symbol: str, api_key: str = None, api_secret: str = None):
        self.symbol = symbol.upper()
        self.api_key = api_key or API_KEY
        self.api_secret = api_secret or API_SECRET
        self.base_url = os.getenv("ALPACA_BASE_URL", "https://api.alpaca.markets/v2")
        self.options_url = os.getenv("ALPACA_OPTIONS_URL", "https://api.alpaca.markets/v2/options/contracts")
        self.stream_url = os.getenv("ALPACA_STREAM_ENDPOINT", "wss://stream.data.alpaca.markets/v2/iex")
        self.headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
            "Content-Type": "application/json"
        }

    async def get_options_data(self):
        """Fetch all available options data for the symbol"""
        try:
            contracts = await self._fetch_all_contracts()
            return {
                "symbol": self.symbol,
                "contracts": contracts,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error fetching options data: {str(e)}")
            return {
                "symbol": self.symbol,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _fetch_all_contracts(self):
        """Fetch all option contracts for a given symbol with automatic pagination"""
        all_contracts = []
        page_token = None
        date_ranges = self._generate_date_ranges()
        
        for start_date, end_date in date_ranges:
            while True:
                contracts, next_token = await self._fetch_contracts_page(start_date, end_date, page_token)
                if contracts:
                    all_contracts.extend(contracts)
                    print(f"Fetched {len(contracts)} contracts for {self.symbol} ({start_date} to {end_date})")
                
                if not next_token:
                    break
                page_token = next_token
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
        
        return all_contracts

    def _generate_date_ranges(self):
        """Generate a list of date ranges covering the next 2 years"""
        today = datetime.today()
        ranges = []
        
        # Generate 8 quarterly ranges (2 years)
        for i in range(8):
            start = today + timedelta(days=90 * i)
            end = start + timedelta(days=90)
            ranges.append((
                start.strftime("%Y-%m-%d"),
                end.strftime("%Y-%m-%d")
            ))
        
        return ranges

    async def _fetch_contracts_page(self, start_date: str, end_date: str, page_token: str = None):
        """Fetch a single page of option contracts"""
        params = {
            "underlying_symbols": self.symbol,
            "status": "active",
            "expiration_date_gte": start_date,
            "expiration_date_lte": end_date,
            "limit": 300  # Maximum allowed by API
        }
        
        if page_token:
            params["page_token"] = page_token
        
        print(f"Fetching options for {self.symbol} from {start_date} to {end_date}")
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(self.options_url, params=params) as response:
                if response.status != 200:
                    print(f"Error: Status {response.status}")
                    return [], None
                    
                data = await response.json()
                contracts = data.get("option_contracts", [])
                next_page_token = data.get("next_page_token")
                
                return contracts, next_page_token

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
