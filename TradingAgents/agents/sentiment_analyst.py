"""Sentiment Analyst using local FinBERT model."""
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from typing import List, Dict, Optional
import config
from database.db_manager import DatabaseManager


class SentimentAnalyst:
    """Analyzes news sentiment using FinBERT."""
    
    def __init__(self, model=None, tokenizer=None):
        """Initialize FinBERT model from local directory, or accept a shared instance."""
        if model is not None and tokenizer is not None:
            # Reuse shared model instance (avoids double-loading with NewsEngine)
            self.model = model
            self.tokenizer = tokenizer
        else:
            model_path = str(config.FINBERT_PATH)
            self.tokenizer = BertTokenizer.from_pretrained(model_path, local_files_only=True)
            self.model = BertForSequenceClassification.from_pretrained(model_path, local_files_only=True)
            self.model.eval()
            self.model.to(torch.device("cpu"))

        self.device = torch.device("cpu")
        self.db = DatabaseManager()
        self.labels = ['negative', 'neutral', 'positive']
    
    def from_news_engine(self, ticker: str, news_result: Dict) -> Dict:
        """
        Build sentiment_data from Sentinel News Engine results.
        Avoids re-running FinBERT when the engine already scored the headlines.
        """
        score = news_result.get('score', 0.0)
        direction = news_result.get('direction', 'neutral')
        count = news_result.get('articles_count', 0)

        if score > 0.2:
            avg_sentiment = 'positive'
        elif score < -0.2:
            avg_sentiment = 'negative'
        else:
            avg_sentiment = 'neutral'

        # Approximate ratios from the signed score
        positive_ratio = max(0.0, score)
        negative_ratio = max(0.0, -score)
        neutral_ratio = max(0.0, 1.0 - abs(score))

        return {
            'ticker': ticker,
            'avg_sentiment': avg_sentiment,
            'avg_score': round(score, 4),
            'positive_ratio': round(positive_ratio, 4),
            'negative_ratio': round(negative_ratio, 4),
            'neutral_ratio': round(neutral_ratio, 4),
            'total_headlines': count,
            'source': 'news_engine',
        }

    def analyze_headline(self, headline: str) -> Dict[str, float]:
        """Analyze a single headline and return sentiment scores."""
        inputs = self.tokenizer(headline, return_tensors="pt", truncation=True, 
                               max_length=512, padding=True)
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
    
    def analyze_news(self, ticker: str, headlines: List[str]) -> Dict:
        """Analyze multiple headlines and return aggregated sentiment."""
        if not headlines:
            return {
                'ticker': ticker,
                'avg_sentiment': 'neutral',
                'avg_score': 0.0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'neutral_ratio': 0.0,
                'total_headlines': 0
            }
        
        results = []
        for headline in headlines:
            result = self.analyze_headline(headline)
            results.append(result)
            
            # Store in database
            self.db.insert_sentiment_score(
                ticker=ticker,
                headline=headline,
                sentiment=result['sentiment'],
                score=result['confidence']
            )
        
        # Aggregate results
        positive_count = sum(1 for r in results if r['sentiment'] == 'positive')
        negative_count = sum(1 for r in results if r['sentiment'] == 'negative')
        neutral_count = sum(1 for r in results if r['sentiment'] == 'neutral')
        total = len(results)
        
        # Calculate weighted sentiment score (-1 to 1)
        sentiment_score = (positive_count - negative_count) / total
        
        # Determine overall sentiment
        if sentiment_score > 0.2:
            avg_sentiment = 'positive'
        elif sentiment_score < -0.2:
            avg_sentiment = 'negative'
        else:
            avg_sentiment = 'neutral'
        
        return {
            'ticker': ticker,
            'avg_sentiment': avg_sentiment,
            'avg_score': sentiment_score,
            'positive_ratio': positive_count / total,
            'negative_ratio': negative_count / total,
            'neutral_ratio': neutral_count / total,
            'total_headlines': total,
            'detailed_results': results
        }
