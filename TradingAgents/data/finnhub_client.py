"""Finnhub API client for real-time market data."""
import requests
from typing import Dict, Optional
import config
from database.db_manager import DatabaseManager
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class FinnhubClient:
    """Client for Finnhub API to fetch real-time quotes."""
    
    def __init__(self):
        """Initialize Finnhub client."""
        self.api_key = config.FINNHUB_API_KEY
        self.base_url = "https://finnhub.io/api/v1"
        self.db = DatabaseManager()
    
    def get_quote(self, ticker: str) -> Optional[Dict]:
        """Fetch real-time quote for a ticker."""
        try:
            response = requests.get(
                f"{self.base_url}/quote",
                params={
                    "symbol": ticker,
                    "token": self.api_key
                },
                timeout=10,
                verify=False  # Bypass SSL verification
            )
            response.raise_for_status()
            data = response.json()
            
            # Finnhub returns: c (current), d (change), dp (percent change), 
            # h (high), l (low), o (open), pc (previous close)
            if data.get('c') == 0:
                return None
            
            quote_data = {
                'ticker': ticker,
                'current_price': data['c'],
                'change': data['d'],
                'percent_change': data['dp'],
                'high': data['h'],
                'low': data['l'],
                'open': data['o'],
                'previous_close': data['pc']
            }
            
            # Store in database
            self.db.insert_market_quote(ticker, data)
            
            return quote_data
            
        except Exception as e:
            print(f"Error fetching quote for {ticker}: {e}")
            return None
    
    def get_quotes_batch(self, tickers: list) -> Dict[str, Dict]:
        """Fetch quotes for multiple tickers."""
        results = {}
        for ticker in tickers:
            quote = self.get_quote(ticker)
            if quote:
                results[ticker] = quote
        return results
