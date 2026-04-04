"""Sentinel News Engine - Dual-source news ingestion, deduplication, and FinBERT scoring."""
import re
import time
import warnings
import urllib3
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple

import feedparser
import torch
import yfinance as yf
from transformers import BertTokenizer, BertForSequenceClassification

import config
from database.db_manager import DatabaseManager

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Clear PostgreSQL SSL cert env vars that break requests/curl
import os
os.environ.pop('REQUESTS_CA_BUNDLE', None)
os.environ.pop('CURL_CA_BUNDLE', None)
os.environ.pop('SSL_CERT_FILE', None)

BATCH_SIZE = 8  # Optimized for i7-12th gen
ALERT_THRESHOLD = 0.7
RECENT_WEIGHT_MINUTES = 15  # Headlines within this window get 2x weight
GOOGLE_NEWS_URL = "https://news.google.com/rss/search?q={symbol}+stock+news&hl=en-US"


class SentinelNewsEngine:
    """Aggregates, deduplicates, and scores financial news headlines."""

    def __init__(self):
        self.db = DatabaseManager()
        self._load_finbert()

    def _load_finbert(self):
        """Load FinBERT from local model directory."""
        model_path = str(config.FINBERT_PATH)
        self.tokenizer = BertTokenizer.from_pretrained(model_path, local_files_only=True)
        self.model = BertForSequenceClassification.from_pretrained(model_path, local_files_only=True)
        self.model.eval()
        self.device = torch.device("cpu")
        self.model.to(self.device)
        self.labels = ['negative', 'neutral', 'positive']

    # ── Text Cleaning ──────────────────────────────────────────────────────────

    def _clean_headline(self, text: str) -> str:
        """Strip HTML tags and publisher suffixes like '- Reuters'."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove publisher suffixes: " - Reuters", " | Bloomberg", etc.
        text = re.sub(r'\s[-|]\s+[A-Z][A-Za-z\s]+$', '', text.strip())
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    # ── Source 1: Google News RSS ──────────────────────────────────────────────

    def _fetch_google_news(self, symbol: str) -> List[Dict]:
        """Fetch top 10 headlines from Google News RSS."""
        url = GOOGLE_NEWS_URL.format(symbol=symbol)
        try:
            feed = feedparser.parse(url)
            articles = []
            for entry in feed.entries[:10]:
                published_at = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                articles.append({
                    'headline': self._clean_headline(entry.get('title', '')),
                    'url': entry.get('link', ''),
                    'published_at': published_at,
                    'source': 'google_news',
                })
            return articles
        except Exception as e:
            print(f"  [NewsEngine] Google News fetch failed for {symbol}: {e}")
            return []

    # ── Source 2: yfinance ─────────────────────────────────────────────────────

    def _fetch_yfinance_news(self, symbol: str) -> Tuple[List[Dict], bool]:
        """Fetch headlines from yfinance. Returns (articles, hit_403)."""
        try:
            raw = yf.Ticker(symbol).news or []
            articles = []
            for item in raw[:10]:
                published_at = None
                ts = item.get('providerPublishTime') or item.get('publishedAt')
                if ts:
                    published_at = datetime.fromtimestamp(int(ts), tz=timezone.utc)
                url = item.get('link') or item.get('url', '')
                headline = self._clean_headline(item.get('title', ''))
                if headline and url:
                    articles.append({
                        'headline': headline,
                        'url': url,
                        'published_at': published_at,
                        'source': 'yfinance',
                    })
            return articles, False
        except Exception as e:
            err = str(e)
            if '403' in err:
                print(f"  [NewsEngine] yfinance 403 for {symbol}, falling back to Google News")
                return [], True
            print(f"  [NewsEngine] yfinance error for {symbol}: {e}")
            return [], False

    # ── FinBERT Batch Scoring ──────────────────────────────────────────────────

    def _score_batch(self, headlines: List[str]) -> List[float]:
        """Score a batch of headlines. Returns list of signed scores (-1 to 1)."""
        scores = []
        for i in range(0, len(headlines), BATCH_SIZE):
            batch = headlines[i:i + BATCH_SIZE]
            inputs = self.tokenizer(
                batch, return_tensors="pt", truncation=True,
                max_length=512, padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with torch.no_grad():
                logits = self.model(**inputs).logits
                probs = torch.nn.functional.softmax(logits, dim=-1).cpu().numpy()
            for p in probs:
                # negative=p[0], neutral=p[1], positive=p[2]
                signed = float(p[2] - p[0])  # range: -1 to 1
                scores.append(signed)
        return scores

    # ── Weighted Aggregate Score ───────────────────────────────────────────────

    def _weighted_score(self, articles: List[Dict]) -> float:
        """Compute time-decayed weighted sentiment score for the last hour."""
        now = datetime.now(tz=timezone.utc)
        cutoff = now - timedelta(hours=1)
        recent_cutoff = now - timedelta(minutes=RECENT_WEIGHT_MINUTES)

        total_weight = 0.0
        weighted_sum = 0.0

        for art in articles:
            score = art.get('sentiment_score')
            pub = art.get('published_at')
            if score is None or pub is None:
                continue
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            if pub < cutoff:
                continue
            weight = 2.0 if pub >= recent_cutoff else 1.0
            weighted_sum += score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    # ── Main Run ───────────────────────────────────────────────────────────────

    def run(self, tickers: List[str] = None) -> Dict[str, Dict]:
        """
        Run the full pipeline for all tickers.
        Returns dict of {ticker: {score, alert, articles_count}}.
        """
        if tickers is None:
            tickers = config.STOCKS

        results = {}

        for symbol in tickers:
            print(f"  [NewsEngine] Processing {symbol}...")

            # Fetch from yfinance, fallback to Google News on 403
            articles, hit_403 = self._fetch_yfinance_news(symbol)
            if hit_403 or not articles:
                articles = self._fetch_google_news(symbol)

            if not articles:
                print(f"  [NewsEngine] No articles found for {symbol}")
                results[symbol] = {'score': 0.0, 'alert': False, 'articles_count': 0}
                continue

            # Deduplicate via DB upsert, collect new articles for scoring
            new_articles = []
            for art in articles:
                if not art['url']:
                    continue
                inserted = self.db.upsert_news_article(
                    ticker=symbol,
                    source=art['source'],
                    headline=art['headline'],
                    url=art['url'],
                    published_at=art['published_at'],
                )
                if inserted:
                    new_articles.append(art)

            # Score only new articles in batches
            if new_articles:
                headlines = [a['headline'] for a in new_articles]
                scores = self._score_batch(headlines)
                for art, score in zip(new_articles, scores):
                    art['sentiment_score'] = score
                    self.db.update_news_sentiment(art['url'], score)
                print(f"  [NewsEngine] Scored {len(new_articles)} new articles for {symbol}")

            # Pull last-hour articles from DB for weighted score
            db_articles = self.db.get_recent_news(symbol, hours=1)
            # Convert RealDictRow to plain dict; use created_at for time-decay (published_at can be stale)
            scored_articles = []
            for row in db_articles:
                pub = row.get('created_at') or row.get('published_at')
                if pub and pub.tzinfo is None:
                    pub = pub.replace(tzinfo=timezone.utc)
                scored_articles.append({'sentiment_score': row['sentiment_score'], 'published_at': pub})

            agg_score = self._weighted_score(scored_articles)
            alert = abs(agg_score) >= ALERT_THRESHOLD

            results[symbol] = {
                'score': round(agg_score, 4),
                'alert': alert,
                'articles_count': len(db_articles),
                'direction': 'positive' if agg_score > 0 else ('negative' if agg_score < 0 else 'neutral'),
            }

            if alert:
                direction = 'BULLISH' if agg_score > 0 else 'BEARISH'
                print(f"  [NewsEngine] *** ALERT: {symbol} {direction} score={agg_score:.3f} ***")

        return results
