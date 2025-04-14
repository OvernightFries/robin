import os
import aiohttp
import asyncio
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_SECRET_KEY")

HEADERS = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": API_SECRET
}

BASE_URL_V2 = "https://api.alpaca.markets/v2/options/contracts"

async def fetch_all_contracts(symbol: str):
    """Fetch all option contracts for a given symbol with automatic pagination and date handling"""
    all_contracts = []
    page_token = None
    date_ranges = generate_date_ranges()
    
    for start_date, end_date in date_ranges:
        while True:
            contracts, next_token = await fetch_contracts_page(symbol, start_date, end_date, page_token)
            if contracts:
                all_contracts.extend(contracts)
                print(f"Fetched {len(contracts)} contracts for {symbol} ({start_date} to {end_date})")
            
            if not next_token:
                break
            page_token = next_token
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)
    
    return all_contracts

def generate_date_ranges():
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

async def fetch_contracts_page(symbol: str, start_date: str, end_date: str, page_token: str = None):
    """Fetch a single page of option contracts"""
    params = {
        "underlying_symbols": symbol,
        "status": "active",
        "expiration_date_gte": start_date,
        "expiration_date_lte": end_date,
        "limit": 300  # Maximum allowed by API
    }
    
    if page_token:
        params["page_token"] = page_token
    
    print(f"Fetching options for {symbol} from {start_date} to {end_date}")
    
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(BASE_URL_V2, params=params) as response:
            if response.status != 200:
                print(f"Error: Status {response.status}")
                return [], None
                
            data = await response.json()
            contracts = data.get("option_contracts", [])
            next_page_token = data.get("next_page_token")
            
            return contracts, next_page_token

async def main():
    # Get ticker from user input
    symbol = input("Enter ticker symbol (e.g., AAPL): ").upper()
    
    print(f"Fetching all available options data for {symbol}...")
    contracts = await fetch_all_contracts(symbol)
    
    # Save results to a file
    filename = f"{symbol}_options_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(contracts, f, indent=2)
    
    print(f"\nFetched {len(contracts)} total contracts")
    print(f"Results saved to {filename}")
    
    return contracts

if __name__ == "__main__":
    asyncio.run(main())
