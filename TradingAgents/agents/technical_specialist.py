"""Technical Specialist using Llama 3.2 via Ollama."""
import pandas as pd
import requests
from typing import Dict
import config
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TechnicalSpecialist:
    """Computes technical indicators and provides analysis using Llama 3.2."""
    
    def __init__(self):
        """Initialize Ollama client."""
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.SPECIALIST_MODEL
    
    def compute_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Compute RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    
    def compute_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """Compute MACD indicator."""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': float(macd_line.iloc[-1]),
            'signal': float(signal_line.iloc[-1]),
            'histogram': float(histogram.iloc[-1])
        }
    
    def analyze_with_llama(self, ticker: str, market_data: Dict, indicators: Dict) -> str:
        """Use Llama 3.2 to analyze technical indicators."""
        prompt = f"""You are a technical analysis specialist. Analyze the following market data and technical indicators for {ticker}:

Market Data:
- Current Price: ${market_data['current_price']:.2f}
- Change: ${market_data['change']:.2f} ({market_data['percent_change']:.2f}%)
- High: ${market_data['high']:.2f}
- Low: ${market_data['low']:.2f}
- Previous Close: ${market_data['previous_close']:.2f}

Technical Indicators:
- RSI (14): {indicators['rsi']:.2f}
- MACD: {indicators['macd']['macd']:.4f}
- MACD Signal: {indicators['macd']['signal']:.4f}
- MACD Histogram: {indicators['macd']['histogram']:.4f}

Provide a concise technical analysis (2-3 sentences) focusing on:
1. RSI interpretation (overbought >70, oversold <30)
2. MACD trend and momentum
3. Overall technical signal (bullish/bearish/neutral)"""

        try:
            print(f"\n[Llama 3.2] Analyzing technical indicators for {ticker}...")
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60,
                verify=False
            )
            response.raise_for_status()
            
            # Parse response properly
            result = response.json()
            analysis = result.get('response', '')
            
            print(f"[Llama 3.2] Analysis: {analysis[:200]}...")
            return analysis
            
        except Exception as e:
            error_msg = f"Technical analysis unavailable: {str(e)}"
            print(f"[Llama 3.2] Error: {error_msg}")
            return error_msg
    
    def analyze(self, ticker: str, market_data: Dict, price_history: pd.DataFrame) -> Dict:
        """Perform complete technical analysis."""
        # Compute indicators
        rsi = self.compute_rsi(price_history['close'])
        macd = self.compute_macd(price_history['close'])
        
        indicators = {
            'rsi': rsi,
            'macd': macd
        }
        
        # Get LLM analysis
        analysis = self.analyze_with_llama(ticker, market_data, indicators)
        
        return {
            'ticker': ticker,
            'indicators': indicators,
            'analysis': analysis
        }
