"""yfinance client for news and historical data."""
import os
import yfinance as yf
import pandas as pd
from typing import List, Dict

# Clear PostgreSQL SSL cert env vars that break curl/requests
os.environ.pop('REQUESTS_CA_BUNDLE', None)
os.environ.pop('CURL_CA_BUNDLE', None)
os.environ.pop('SSL_CERT_FILE', None)


class YFinanceClient:
    """Client for yfinance to fetch news and historical price data."""
    
    def get_news(self, ticker: str, limit: int = 10) -> List[str]:
        """Fetch recent news headlines for a ticker."""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            
            if not news:
                return []
            
            # Extract headlines
            headlines = [item.get('title', '') for item in news[:limit] if item.get('title')]
            return headlines
            
        except Exception as e:
            print(f"Error fetching news for {ticker}: {e}")
            return []
    
    def get_price_history(self, ticker: str, period: str = "1mo") -> pd.DataFrame:
        """Fetch historical price data for technical analysis."""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            
            if hist.empty:
                return pd.DataFrame()
            
            # Rename columns to lowercase for consistency
            hist.columns = [col.lower() for col in hist.columns]
            return hist
            
        except Exception as e:
            print(f"Error fetching price history for {ticker}: {e}")
            return pd.DataFrame()
    
    def get_batch_news(self, tickers: List[str], limit: int = 10) -> Dict[str, List[str]]:
        """Fetch news for multiple tickers."""
        results = {}
        for ticker in tickers:
            headlines = self.get_news(ticker, limit)
            if headlines:
                results[ticker] = headlines
        return results
