import os
import requests
import logging
from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv

load_dotenv()

class OptionsScanner:
    def __init__(self):
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        self.client = StockHistoricalDataClient(api_key=self.api_key, secret_key=self.secret_key)
        self.options_url = "https://data.alpaca.markets/v1beta1/options/snapshots/"
        logging.info("OptionsScanner initialized successfully")

    def scan_high_iv_options(self, symbol: str) -> list:
        """Scan for options with high implied volatility using Alpaca snapshot."""
        try:
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key
            }
            url = f"{self.options_url}{symbol.upper()}"
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            snapshots = res.json().get("snapshots", {})

            high_iv_contracts = []
            for contract, data in snapshots.items():
                greeks = data.get("greeks", {})
                iv = greeks.get("implied_volatility")
                if iv and iv > 0.5:
                    high_iv_contracts.append({
                        "symbol": contract,
                        "iv": iv,
                        "delta": greeks.get("delta"),
                        "theta": greeks.get("theta")
                    })
            return high_iv_contracts
        except Exception as e:
            logging.error(f"Error scanning high IV options: {str(e)}")
            return []

    def find_credit_spreads(self, symbol: str) -> list:
        """Find bull put credit spreads based on real bid/ask prices."""
        try:
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key
            }
            url = f"{self.options_url}{symbol.upper()}"
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            snapshots = res.json().get("snapshots", {})

            quotes = []
            for contract, data in snapshots.items():
                quote = data.get("latestQuote")
                if quote:
                    quotes.append({
                        "symbol": contract,
                        "bp": quote.get("bp"),
                        "ap": quote.get("ap")
                    })

            spreads = []
            quotes = sorted(quotes, key=lambda x: x["symbol"])[:20]  # simplify for now
            for i in range(len(quotes) - 1):
                short = quotes[i]
                long = quotes[i + 1]
                if short["bp"] and long["ap"]:
                    credit = short["bp"] - long["ap"]
                    if credit > 0:
                        spreads.append({
                            "type": "bull_put_spread",
                            "short_leg": short["symbol"],
                            "long_leg": long["symbol"],
                            "credit": round(credit, 2)
                        })
            return spreads
        except Exception as e:
            logging.error(f"Error finding credit spreads: {str(e)}")
            return []

    def scan_volume_spikes(self, symbol: str) -> list:
        """Scan for volume spikes against a moving average."""
        try:
            request = StockBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=TimeFrame.Day,
                start=datetime.now() - timedelta(days=10),
                end=datetime.now()
            )
            bars = self.client.get_stock_bars(request)
            df = bars.df
            if symbol not in df.index.get_level_values(0):
                return []

            symbol_df = df.loc[symbol]
            avg_volume = symbol_df["volume"].mean()
            spikes = symbol_df[symbol_df["volume"] > avg_volume * 1.5]
            return spikes[["volume"]].reset_index().to_dict("records")

        except Exception as e:
            logging.error(f"Error scanning volume spikes: {str(e)}")
            return []
