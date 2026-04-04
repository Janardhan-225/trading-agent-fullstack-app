from fastapi import APIRouter, Depends
import feedparser
import random
from sqlalchemy.orm import Session
from database import get_db
import models
import urllib.parse
import time

router = APIRouter()

# Simple global cache to avoid rate limits and repeat loads
NEWS_CACHE = {"timestamp": 0, "data": []}

@router.get("/")
def get_live_news(db: Session = Depends(get_db)):
    global NEWS_CACHE
    # Refresh cache every 20 mins
    if time.time() - NEWS_CACHE["timestamp"] < 1200 and NEWS_CACHE["data"]:
        return {"news": NEWS_CACHE["data"]}

    tracked = db.query(models.TrackedStock).filter(models.TrackedStock.is_active == True).all()
    symbols = [t.symbol for t in tracked] if tracked else ["AAPL", "MSFT"]
    
    results = []
    
    for symbol in symbols:
        # Fetch multiple articles for each stock
        query = urllib.parse.quote(f"{symbol} stock market update finance")
        url = f"https://news.google.com/rss/search?q={query}+when:1d"
        feed = feedparser.parse(url)
        
        # Take top 3 articles per stock to diversify
        for entry in feed.entries[:3]:
            title = entry.title
            lower_title = title.lower()
            if any(word in lower_title for word in ['surge', 'jump', 'up', 'beat', 'gain', 'growth', 'bull']):
                sentiment = 'positive'
            elif any(word in lower_title for word in ['drop', 'fall', 'down', 'miss', 'loss', 'bear', 'crash', 'warn', 'bearish']):
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
                
            results.append({
                "id": entry.id if hasattr(entry, 'id') else str(random.random()),
                "title": title,
                "source": entry.source.title if hasattr(entry, 'source') and hasattr(entry.source, 'title') else "Google News RSS",
                "time": getattr(entry, 'published', 'Recently'),
                "sentiment": sentiment,
                "link": entry.link
            })
    
    # Shuffle results to mix up the feed visually instead of grouping by stock
    random.shuffle(results)
    
    NEWS_CACHE["timestamp"] = time.time()
    NEWS_CACHE["data"] = results
    
    return {"news": results}
