"""
Alpha Vantage Data Provider with News Sentiment Analysis
Provides alternative data source with real-time news sentiment for trading signals
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import time

class AlphaVantageProvider:
    """Alpha Vantage API integration for stock data and news sentiment"""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self):
        self.api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
        if not self.api_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY not found in environment variables")
    
    def _make_request(self, params: Dict) -> Optional[Dict]:
        """Make API request with error handling"""
        params['apikey'] = self.api_key
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'Error Message' in data:
                print(f"API Error: {data['Error Message']}")
                return None
            
            if 'Note' in data:
                print(f"API Rate Limit: {data['Note']}")
                return None
            
            return data
        except Exception as e:
            print(f"Request failed: {e}")
            return None
    
    def get_intraday_data(self, symbol: str, interval: str = '5min', outputsize: str = 'compact') -> Optional[pd.DataFrame]:
        """
        Get intraday stock data
        interval: 1min, 5min, 15min, 30min, 60min
        outputsize: compact (latest 100 data points) or full
        """
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': interval,
            'outputsize': outputsize
        }
        
        data = self._make_request(params)
        if not data:
            return None
        
        time_series_key = f'Time Series ({interval})'
        if time_series_key not in data:
            return None
        
        df = pd.DataFrame.from_dict(data[time_series_key], orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        df.columns = ['open', 'high', 'low', 'close', 'volume']
        for col in ['open', 'high', 'low', 'close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce').astype(int)
        
        return df
    
    def get_daily_data(self, symbol: str, outputsize: str = 'compact') -> Optional[pd.DataFrame]:
        """
        Get daily stock data
        outputsize: compact (latest 100 days) or full (20+ years)
        """
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'outputsize': outputsize
        }
        
        data = self._make_request(params)
        if not data:
            return None
        
        if 'Time Series (Daily)' not in data:
            return None
        
        df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        df.columns = ['open', 'high', 'low', 'close', 'volume']
        for col in ['open', 'high', 'low', 'close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce').astype(int)
        
        return df
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """Get real-time quote"""
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        if not data or 'Global Quote' not in data:
            return None
        
        quote = data['Global Quote']
        return {
            'symbol': quote.get('01. symbol', symbol),
            'price': float(quote.get('05. price', 0)),
            'change': float(quote.get('09. change', 0)),
            'change_percent': quote.get('10. change percent', '0%'),
            'volume': int(quote.get('06. volume', 0)),
            'latest_trading_day': quote.get('07. latest trading day', '')
        }
    
    def get_news_sentiment(self, tickers: str = None, topics: str = None, 
                          time_from: str = None, time_to: str = None,
                          limit: int = 50) -> Optional[Dict]:
        """
        Get news sentiment data
        
        Args:
            tickers: Comma-separated stock symbols (e.g., "AAPL,TSLA")
            topics: Topics like "technology", "finance", "earnings", etc.
            time_from: Format YYYYMMDDTHHMM (e.g., 20231201T0000)
            time_to: Format YYYYMMDDTHHMM
            limit: Max 1000, default 50
        """
        params = {
            'function': 'NEWS_SENTIMENT',
            'limit': limit
        }
        
        if tickers:
            params['tickers'] = tickers
        if topics:
            params['topics'] = topics
        if time_from:
            params['time_from'] = time_from
        if time_to:
            params['time_to'] = time_to
        
        data = self._make_request(params)
        return data
    
    def analyze_news_sentiment(self, symbol: str, hours_back: int = 24) -> Dict:
        """
        Analyze recent news sentiment for a stock
        
        Returns:
            Dict with sentiment scores and signal recommendation
        """
        time_to = datetime.now()
        time_from = time_to - timedelta(hours=hours_back)
        
        time_from_str = time_from.strftime('%Y%m%dT%H%M')
        time_to_str = time_to.strftime('%Y%m%dT%H%M')
        
        news_data = self.get_news_sentiment(
            tickers=symbol,
            time_from=time_from_str,
            time_to=time_to_str,
            limit=50
        )
        
        if not news_data or 'feed' not in news_data:
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'Neutral',
                'relevance_score': 0.0,
                'article_count': 0,
                'signal': 'NEUTRAL',
                'confidence': 0.0,
                'articles': []
            }
        
        articles = news_data.get('feed', [])
        
        if not articles:
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'Neutral',
                'relevance_score': 0.0,
                'article_count': 0,
                'signal': 'NEUTRAL',
                'confidence': 0.0,
                'articles': []
            }
        
        sentiments = []
        relevance_scores = []
        processed_articles = []
        
        for article in articles:
            ticker_sentiments = article.get('ticker_sentiment', [])
            
            for ticker_data in ticker_sentiments:
                if ticker_data.get('ticker') == symbol:
                    sentiment_score = float(ticker_data.get('ticker_sentiment_score', 0))
                    sentiment_label = ticker_data.get('ticker_sentiment_label', 'Neutral')
                    relevance = float(ticker_data.get('relevance_score', 0))
                    
                    sentiments.append(sentiment_score)
                    relevance_scores.append(relevance)
                    
                    processed_articles.append({
                        'title': article.get('title', 'N/A'),
                        'source': article.get('source', 'N/A'),
                        'time_published': article.get('time_published', ''),
                        'sentiment_score': sentiment_score,
                        'sentiment_label': sentiment_label,
                        'relevance': relevance,
                        'url': article.get('url', '')
                    })
        
        if not sentiments:
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'Neutral',
                'relevance_score': 0.0,
                'article_count': 0,
                'signal': 'NEUTRAL',
                'confidence': 0.0,
                'articles': []
            }
        
        avg_sentiment = sum(sentiments) / len(sentiments)
        avg_relevance = sum(relevance_scores) / len(relevance_scores)
        
        if avg_sentiment > 0.15:
            sentiment_label = 'Bullish'
            signal = 'LONG'
        elif avg_sentiment < -0.15:
            sentiment_label = 'Bearish'
            signal = 'SHORT'
        else:
            sentiment_label = 'Neutral'
            signal = 'NEUTRAL'
        
        confidence = min(abs(avg_sentiment) * avg_relevance * 10, 1.0)
        
        processed_articles.sort(key=lambda x: x['relevance'], reverse=True)
        
        return {
            'sentiment_score': avg_sentiment,
            'sentiment_label': sentiment_label,
            'relevance_score': avg_relevance,
            'article_count': len(sentiments),
            'signal': signal,
            'confidence': confidence,
            'articles': processed_articles[:10]
        }
    
    def get_combined_signal(self, symbol: str) -> Dict:
        """
        Get combined trading signal from price and news sentiment
        
        Returns:
            Dict with price data, news sentiment, and combined recommendation
        """
        quote = self.get_quote(symbol)
        sentiment = self.analyze_news_sentiment(symbol, hours_back=24)
        
        if not quote:
            return {
                'error': 'Failed to fetch quote data',
                'signal': 'NO_DATA'
            }
        
        price_change_pct = float(quote['change_percent'].replace('%', ''))
        
        if price_change_pct > 2.0:
            price_signal = 'LONG'
        elif price_change_pct < -2.0:
            price_signal = 'SHORT'
        else:
            price_signal = 'NEUTRAL'
        
        news_signal = sentiment['signal']
        
        if price_signal == 'LONG' and news_signal == 'LONG':
            combined_signal = 'STRONG_LONG'
            confidence = min(sentiment['confidence'] + 0.3, 1.0)
        elif price_signal == 'SHORT' and news_signal == 'SHORT':
            combined_signal = 'STRONG_SHORT'
            confidence = min(sentiment['confidence'] + 0.3, 1.0)
        elif price_signal == 'LONG' or news_signal == 'LONG':
            combined_signal = 'LONG'
            confidence = sentiment['confidence'] * 0.7
        elif price_signal == 'SHORT' or news_signal == 'SHORT':
            combined_signal = 'SHORT'
            confidence = sentiment['confidence'] * 0.7
        else:
            combined_signal = 'NEUTRAL'
            confidence = 0.0
        
        return {
            'symbol': symbol,
            'price': quote['price'],
            'price_change': quote['change'],
            'price_change_pct': price_change_pct,
            'price_signal': price_signal,
            'news_sentiment_score': sentiment['sentiment_score'],
            'news_sentiment_label': sentiment['sentiment_label'],
            'news_signal': news_signal,
            'news_confidence': sentiment['confidence'],
            'article_count': sentiment['article_count'],
            'combined_signal': combined_signal,
            'confidence': confidence,
            'top_articles': sentiment['articles'][:5],
            'timestamp': datetime.now().isoformat()
        }


def fetch_alpha_vantage_data(symbol: str, interval: str = '1d', period: str = '3mo') -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Fetch stock data from Alpha Vantage (compatible with existing fetch_stock_data interface)
    
    Args:
        symbol: Stock ticker symbol
        interval: Time interval (1m, 5m, 15m, 30m, 45m, 1h, 1d, 1wk)
        period: Not used for Alpha Vantage (uses outputsize instead)
    
    Returns:
        Tuple of (DataFrame, error_message)
    """
    try:
        provider = AlphaVantageProvider()
        
        # Map UI intervals to Alpha Vantage supported intervals
        interval_mapping = {
            '1m': '1min',
            '5m': '5min',
            '15m': '15min',
            '30m': '30min',
            '45m': '60min',  # Alpha Vantage doesn't support 45min, use 60min
            '1h': '60min',
            '1d': 'daily',
            '1wk': 'daily'  # Alpha Vantage doesn't support weekly, use daily
        }
        
        av_interval = interval_mapping.get(interval, '1d')
        
        if av_interval == 'daily':
            df = provider.get_daily_data(symbol, outputsize='full')
        else:
            df = provider.get_intraday_data(symbol, interval=av_interval, outputsize='full')
        
        if df is None:
            return None, "Failed to fetch data from Alpha Vantage. Check symbol or API limits (25 requests/day)."
        
        if len(df) == 0:
            return None, "No data returned from Alpha Vantage"
        
        return df, None
        
    except Exception as e:
        return None, f"Alpha Vantage error: {str(e)}"
