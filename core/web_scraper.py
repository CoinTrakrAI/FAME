#!/usr/bin/env python3
"""
F.A.M.E. Web Scraper - Dynamic web content extraction with SERPAPI integration
"""

import requests
import re
import os
import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# SERPAPI Keys
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "90f8748cb8ab624df5d503e1765e929491c57ef0b4d681fbe046f1febe045dbc")
SERPAPI_BACKUP_KEY = os.getenv("SERPAPI_BACKUP_KEY", "912dc3fe069c587aa89dc662a492998ded20a25dfc49f9961ff5e5c99168eeb1")

class WebScraper:
    """Dynamic web scraping for current information with SERPAPI support"""
    
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.serpapi_key = SERPAPI_KEY
        self.serpapi_backup_key = SERPAPI_BACKUP_KEY
        self.use_serpapi = bool(self.serpapi_key)
    
    def search_serpapi(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Search using SERPAPI (Google Search API)"""
        if not self.use_serpapi:
            return {'success': False, 'error': 'SERPAPI key not available'}
        
        # Try primary key first
        for api_key in [self.serpapi_key, self.serpapi_backup_key]:
            if not api_key:
                continue
            
            try:
                url = "https://serpapi.com/search"
                params = {
                    'q': query,
                    'api_key': api_key,
                    'num': max_results,
                    'engine': 'google'
                }
                
                response = self.session.get(url, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    
                    results = []
                    # Extract organic results
                    if 'organic_results' in data:
                        for item in data['organic_results'][:max_results]:
                            results.append({
                                'title': item.get('title', ''),
                                'snippet': item.get('snippet', ''),
                                'link': item.get('link', ''),
                                'source': 'serpapi'
                            })
                    
                    # Extract answer box if available
                    answer_box = data.get('answer_box', {})
                    if answer_box:
                        answer = answer_box.get('answer') or answer_box.get('snippet', '')
                        if answer:
                            results.insert(0, {
                                'title': 'Direct Answer',
                                'snippet': answer,
                                'link': answer_box.get('link', ''),
                                'source': 'serpapi_answer_box'
                            })
                    
                    if results:
                        return {
                            'success': True,
                            'results': results,
                            'method': 'serpapi',
                            'query': query
                        }
                elif response.status_code == 401:
                    # Invalid API key, try backup
                    continue
            except Exception as e:
                logger.warning(f"SERPAPI search failed with key: {e}")
                continue
        
        return {'success': False, 'error': 'SERPAPI search failed'}
    
    def search_evolution_techniques(self, query: str = "how to self-evolve AI systems") -> Dict[str, Any]:
        """Search for self-evolution techniques and strategies"""
        search_queries = [
            query,
            "AI self-evolution techniques",
            "automated bug fixing Python",
            "code improvement strategies",
            "self-improving AI systems"
        ]
        
        all_results = []
        for q in search_queries[:3]:  # Limit to 3 queries
            result = self.search_serpapi(q, max_results=5)
            if result.get('success') and result.get('results'):
                all_results.extend(result['results'])
        
        return {
            'success': len(all_results) > 0,
            'results': all_results[:10],  # Top 10 results
            'method': 'serpapi_evolution_search'
        }
    
    def search(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Generic search method - uses SERPAPI for general queries
        """
        return self.search_serpapi(query, max_results)
    
    def search_bug_fixing_techniques(self, bug_type: str = None) -> Dict[str, Any]:
        """Search for bug fixing techniques"""
        queries = [
            "Python bug fixing techniques",
            "automated code debugging",
            "static analysis bug detection",
            "code quality improvement"
        ]
        
        if bug_type:
            queries.insert(0, f"how to fix {bug_type} in Python")
        
        all_results = []
        for q in queries[:3]:
            result = self.search_serpapi(q, max_results=5)
            if result.get('success') and result.get('results'):
                all_results.extend(result['results'])
        
        return {
            'success': len(all_results) > 0,
            'results': all_results[:10],
            'method': 'serpapi_bug_fixing_search'
        }
    
    def search_news(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Search for news articles dynamically"""
        try:
            # Try Google News search
            news_url = "https://www.google.com/search"
            params = {
                'q': query,
                'tbm': 'nws',  # News search
                'num': max_results
            }
            
            response = self.session.get(news_url, params=params, timeout=10)
            if response.status_code == 200:
                # Parse HTML for news results
                html_content = response.text
                results = self._parse_google_news(html_content)
                
                if results:
                    return {
                        'success': True,
                        'results': results,
                        'method': 'google_news_search'
                    }
        except Exception as e:
            pass
        
        return {'success': False, 'error': 'No news found'}
    
    def _parse_google_news(self, html: str) -> List[Dict[str, Any]]:
        """Parse Google News HTML results"""
        results = []
        
        # Google News structure may vary, try multiple patterns
        # Look for article titles and links
        # Pattern 1: Standard news results
        pattern1 = r'<h3[^>]*><a[^>]*href="([^"]*)"[^>]*>(.*?)</a></h3>'
        matches1 = re.findall(pattern1, html)
        
        for url, title in matches1[:5]:
            if url.startswith('/url?'):
                # Extract actual URL
                url_match = re.search(r'url\?q=([^&]+)', url)
                if url_match:
                    actual_url = url_match.group(1)
                else:
                    continue
            else:
                actual_url = url
            
            results.append({
                'title': re.sub(r'<[^>]+>', '', title),
                'url': actual_url
            })
        
        return results
    
    def get_page_content(self, url: str) -> Dict[str, Any]:
        """Get content from a specific URL"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                # Extract text content from HTML
                text = self._extract_text(response.text)
                
                return {
                    'success': True,
                    'content': text[:1000],  # First 1000 chars
                    'url': url
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        return {'success': False}
    
    def _extract_text(self, html: str) -> str:
        """Extract readable text from HTML"""
        # Remove script and style tags
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Extract text from paragraphs and divs
        text_parts = []
        patterns = [
            r'<p[^>]*>(.*?)</p>',
            r'<div[^>]*class="[^"]*article[^"]*"[^>]*>(.*?)</div>',
            r'<article[^>]*>(.*?)</article>'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            for match in matches[:10]:  # First 10 matches
                clean_text = re.sub(r'<[^>]+>', '', match)
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                if clean_text and len(clean_text) > 20:
                    text_parts.append(clean_text)
        
        return ' '.join(text_parts)

