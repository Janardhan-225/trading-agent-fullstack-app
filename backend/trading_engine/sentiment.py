import torch
from transformers import BertTokenizer, BertForSequenceClassification
import yfinance as yf
from typing import List, Dict
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

# We try to use the pre-downloaded local instance from TradingAgents to save bandwidth
LOCAL_TARGET = "d:/Minor Project/project-2/TradingAgents/model/finbert"
MODEL_NAME = LOCAL_TARGET if os.path.exists(LOCAL_TARGET) else "ProsusAI/finbert"

class SentimentAnalyst:
    """Analyzes news sentiment using FinBERT mapped directly to CPU pipeline."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        print(f"[SentimentAnalyst] Booting PyTorch with model: {MODEL_NAME}")
        self.tokenizer = BertTokenizer.from_pretrained(MODEL_NAME, local_files_only=os.path.exists(LOCAL_TARGET))
        self.model = BertForSequenceClassification.from_pretrained(MODEL_NAME, local_files_only=os.path.exists(LOCAL_TARGET))
        self.model.eval()
        self.device = torch.device("cpu")
        self.model.to(self.device)
        self.labels = ['positive', 'negative', 'neutral'] # FinBert standard output logic
        
    def analyze_headline(self, headline: str) -> Dict[str, float]:
        inputs = self.tokenizer(headline, return_tensors="pt", truncation=True, max_length=512, padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
        scores = {label: float(prob) for label, prob in zip(self.labels, probs[0])}
        sentiment = max(scores, key=scores.get)
        
        return {
            'sentiment': sentiment,
            'scores': scores,
            'confidence': scores[sentiment]
        }
        
    async def analyze_news_async(self, ticker: str, limit: int = 15) -> Dict:
        """Fetch multiple sources physically concurrently and score"""
        def fetch_and_score():
            import feedparser
            import requests
            from datetime import datetime, timedelta
            import re
            
            headlines = []
            
            # 1. Google News RSS
            try:
                feed = feedparser.parse(f"https://news.google.com/rss/search?q={ticker}+stock+news&hl=en-US")
                for entry in feed.entries[:10]:
                    title = entry.get('title', '')
                    title = re.sub(r'\s[-|]\s.*$', '', title.strip())
                    if len(title) > 5: headlines.append(title)
            except Exception: pass

            # 2. Finnhub 3-Day Institutional Corporate News
            try:
                finnhub_key = os.getenv("FINNHUB_API_KEY", "")
                if finnhub_key:
                    end = datetime.now().strftime("%Y-%m-%d")
                    start = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
                    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={start}&to={end}&token={finnhub_key}"
                    res = requests.get(url, timeout=5)
                    if res.status_code == 200:
                        for item in res.json()[:10]:
                            hl = item.get("headline", "")
                            summary = item.get("summary", "")
                            text = f"{hl}. {summary}".strip()
                            if len(text) > 10: headlines.append(text)
            except Exception: pass

            # Deduplicate by removing exact string duplicates
            unique_headlines = list(set(headlines))[:limit]

            if not unique_headlines:
                return {
                    'ticker': ticker, 'avg_sentiment': 'neutral', 'avg_score': 0.0,
                    'positive_ratio': 0.0, 'negative_ratio': 0.0, 'neutral_ratio': 0.0,
                    'total_headlines': 0
                }
            
            results = [self.analyze_headline(h) for h in unique_headlines]
            
            p_count = sum(1 for r in results if r['sentiment'] == 'positive')
            n_count = sum(1 for r in results if r['sentiment'] == 'negative')
            neu_count = sum(1 for r in results if r['sentiment'] == 'neutral')
            t = len(results)
            
            score = (p_count - n_count) / t
            
            if score > 0.2: avg_s = 'positive'
            elif score < -0.2: avg_s = 'negative'
            else: avg_s = 'neutral'
            
            return {
                'ticker': ticker,
                'avg_sentiment': avg_s,
                'avg_score': score,
                'positive_ratio': p_count / t,
                'negative_ratio': n_count / t,
                'neutral_ratio': neu_count / t,
                'total_headlines': t
            }
            
        return await asyncio.to_thread(fetch_and_score)
