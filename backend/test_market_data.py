import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

symbol = "SPY"

url = f"https://data.alpaca.markets/v1beta1/options/snapshots/{symbol}"

headers = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY,
}

logger.info(f"📅 Fetching snapshot for {symbol}")
try:
    res = requests.get(url, headers=headers)  # 🔥 Fixed: no params
    res.raise_for_status()
    logger.info("✅ Data fetched successfully")

    snapshots = res.json().get("snapshots", {})
    if not snapshots:
        logger.warning("⚠️ No options data returned.")
    else:
        print(f"\n🧠 Showing options snapshot for {symbol} ({len(snapshots)} contracts)...\n")
        for contract_symbol, data in list(snapshots.items())[:10]:  # Show first 10
            quote = data.get("latestQuote", {})
            greeks = data.get("greeks", {})
            last_price = data.get("latestTrade", {}).get("p")

            print(f"📄 Symbol: {contract_symbol}")
            print(f"  Last Price: {last_price}")
            print(f"  Bid: {quote.get('bp')} | Ask: {quote.get('ap')}")
            print(f"  Delta: {greeks.get('delta')} | Theta: {greeks.get('theta')} | IV: {greeks.get('implied_volatility')}")
            print("-" * 40)

except requests.RequestException as e:
    logger.error(f"❌ Request failed: {e}")
