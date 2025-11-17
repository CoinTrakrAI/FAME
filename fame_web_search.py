#!/usr/bin/env python3
"""
FAME Web Search Integration
Provides real-time information access through multiple search methods
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

# Try to load keys from config if available
try:
    from fame_config import (
        SERPAPI_KEY as CONFIG_KEY, 
        SERPAPI_KEY_BACKUP as CONFIG_BACKUP,
        ALPHA_VANTAGE_API_KEY as CONFIG_AV_KEY,
        COINGECKO_API_KEY as CONFIG_CG_KEY,
        FINNHUB_API_KEY as CONFIG_FH_KEY
    )
    if not os.getenv('SERPAPI_KEY'):
        os.environ['SERPAPI_KEY'] = CONFIG_KEY
    if not os.getenv('SERPAPI_KEY_BACKUP'):
        os.environ['SERPAPI_KEY_BACKUP'] = CONFIG_BACKUP
    if not os.getenv('ALPHA_VANTAGE_API_KEY'):
        os.environ['ALPHA_VANTAGE_API_KEY'] = CONFIG_AV_KEY
    if not os.getenv('COINGECKO_API_KEY'):
        os.environ['COINGECKO_API_KEY'] = CONFIG_CG_KEY
    if not os.getenv('FINNHUB_API_KEY'):
        os.environ['FINNHUB_API_KEY'] = CONFIG_FH_KEY
except ImportError:
    pass  # Config not available, use environment variables only

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False


class FAMEWebSearcher:
    """Web search capabilities for FAME"""
    
    def __init__(self):
        # API keys from environment (will be auto-loaded from config)
        self.google_api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
        self.google_cx = os.getenv('GOOGLE_SEARCH_CX')
        self.serpapi_key = os.getenv('SERPAPI_KEY')
        self.serpapi_backup = os.getenv('SERPAPI_KEY_BACKUP')
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.coingecko_key = os.getenv('COINGECKO_API_KEY')
        self.finnhub_key = os.getenv('FINNHUB_API_KEY')
        self.newsapi_key = os.getenv('NEWSAPI_KEY')
        
        # Financial data sources
        self.financial_sources = {
            'yahoo_finance': 'https://finance.yahoo.com',
            'bloomberg': 'https://www.bloomberg.com',
            'reuters': 'https://www.reuters.com',
            'cnbc': 'https://www.cnbc.com'
        }
    
    def search_google_custom(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search using Google Custom Search JSON API"""
        if not self.google_api_key or not self.google_cx:
            return []
        
        if not REQUESTS_AVAILABLE:
            return []
        
        try:
            url = "https://customsearch.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_api_key,
                'cx': self.google_cx,
                'q': query,
                'num': num_results
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get('items', [])[:num_results]:
                    results.append({
                        'title': item.get('title', ''),
                        'snippet': item.get('snippet', ''),
                        'link': item.get('link', ''),
                        'source': 'Google Custom Search'
                    })
                return results
        except Exception as e:
            print(f"Google search error: {e}")
        
        return []
    
    def search_serpapi(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search using SerpAPI (handles CAPTCHAs and proxies)"""
        # Try primary key first, then backup
        api_keys = []
        if self.serpapi_key:
            api_keys.append(self.serpapi_key)
        if self.serpapi_backup:
            api_keys.append(self.serpapi_backup)
        
        if not api_keys:
            return []
        
        if not REQUESTS_AVAILABLE:
            return []
        
        # Try each key until one works
        for api_key in api_keys:
            try:
                url = "https://serpapi.com/search"
                params = {
                    'api_key': api_key,
                    'q': query,
                    'engine': 'google',
                    'num': num_results
                }
                
                response = requests.get(url, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    for item in data.get('organic_results', [])[:num_results]:
                        results.append({
                            'title': item.get('title', ''),
                            'snippet': item.get('snippet', ''),
                            'link': item.get('link', ''),
                            'source': 'SerpAPI'
                        })
                    return results
                elif response.status_code == 401:
                    # Invalid API key, try next one
                    continue
            except Exception as e:
                # Try backup key if error
                if api_key == api_keys[-1]:  # Last key, give up
                    print(f"SerpAPI search error: {e}")
                continue
        
        return []
    
    def search_bing(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search using Bing Web Search API"""
        bing_key = os.getenv('BING_SEARCH_API_KEY')
        if not bing_key:
            return []
        
        if not REQUESTS_AVAILABLE:
            return []
        
        try:
            url = "https://api.bing.microsoft.com/v7.0/search"
            headers = {'Ocp-Apim-Subscription-Key': bing_key}
            params = {'q': query, 'count': num_results}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get('webPages', {}).get('value', [])[:num_results]:
                    results.append({
                        'title': item.get('name', ''),
                        'snippet': item.get('snippet', ''),
                        'link': item.get('url', ''),
                        'source': 'Bing'
                    })
                return results
        except Exception as e:
            print(f"Bing search error: {e}")
        
        return []
    
    def get_financial_news(self, query: str = "financial news", num_results: int = 5) -> List[Dict[str, Any]]:
        """Get financial news from NewsAPI"""
        if not self.newsapi_key:
            return []
        
        if not REQUESTS_AVAILABLE:
            return []
        
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'apiKey': self.newsapi_key,
                'q': query,
                'sortBy': 'publishedAt',
                'language': 'en',
                'pageSize': num_results
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = []
                for article in data.get('articles', [])[:num_results]:
                    results.append({
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': article.get('url', ''),
                        'publishedAt': article.get('publishedAt', ''),
                        'source': article.get('source', {}).get('name', ''),
                        'type': 'financial_news'
                    })
                return results
        except Exception as e:
            print(f"NewsAPI error: {e}")
        
        return []
    
    def search(self, query: str, search_type: str = 'general', num_results: int = 5) -> List[Dict[str, Any]]:
        """Unified search interface"""
        results = []
        
        # Try different search methods in order of preference
        if search_type == 'financial_news':
            results = self.get_financial_news(query, num_results)
            if results:
                return results
        
        # Try SerpAPI first (most reliable)
        if self.serpapi_key:
            results = self.search_serpapi(query, num_results)
            if results:
                return results
        
        # Try Google Custom Search
        if self.google_api_key and self.google_cx:
            results = self.search_google_custom(query, num_results)
            if results:
                return results
        
        # Try Bing as fallback
        if os.getenv('BING_SEARCH_API_KEY'):
            results = self.search_bing(query, num_results)
            if results:
                return results
        
        return results
    
    def format_search_results(self, results: List[Dict[str, Any]], max_chars: int = 500) -> str:
        """Format search results for display"""
        if not results:
            # Check if keys are configured
            has_keys = bool(self.serpapi_key or self.serpapi_backup or self.google_api_key or os.getenv('BING_SEARCH_API_KEY'))
            if has_keys:
                return "No search results found for this query. The search may have failed or returned no results."
            else:
                return "No search results found. Check API keys configuration."
        
        formatted = f"Found {len(results)} result(s):\n\n"
        
        for i, result in enumerate(results[:3], 1):  # Show top 3
            title = result.get('title', 'No title')
            snippet = result.get('snippet', result.get('description', 'No description'))
            link = result.get('link', result.get('url', ''))
            source = result.get('source', 'Unknown')
            
            # Truncate if too long
            if len(snippet) > max_chars:
                snippet = snippet[:max_chars] + "..."
            
            formatted += f"{i}. {title}\n"
            formatted += f"   {snippet}\n"
            if link:
                formatted += f"   Source: {source} | {link}\n"
            formatted += "\n"
        
        return formatted


def get_current_info(query: str) -> str:
    """Get current information using web search"""
    searcher = FAMEWebSearcher()
    
    # Determine search type
    query_lower = query.lower()
    search_type = 'financial_news' if any(word in query_lower for word in ['stock', 'market', 'finance', 'crypto', 'bitcoin']) else 'general'
    
    # Perform search
    results = searcher.search(query, search_type=search_type, num_results=3)
    
    if results:
        return searcher.format_search_results(results)
    else:
        return "Unable to fetch current information. API keys may not be configured. Check environment variables for search API keys."


# For testing
if __name__ == "__main__":
    searcher = FAMEWebSearcher()
    
    print("FAME Web Search Test")
    print("=" * 60)
    
    # Test query
    query = "current US President 2025"
    print(f"\nSearching: {query}\n")
    
    results = searcher.search(query, num_results=3)
    if results:
        print(searcher.format_search_results(results))
    else:
        print("No results. Configure API keys:")
        print("  - GOOGLE_SEARCH_API_KEY + GOOGLE_SEARCH_CX")
        print("  - SERPAPI_KEY (recommended)")
        print("  - BING_SEARCH_API_KEY")
        print("  - NEWSAPI_KEY (for financial news)")

