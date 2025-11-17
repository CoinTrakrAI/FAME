#!/usr/bin/env python3
"""
FAME Parallel Search Executor
Executes all available search APIs simultaneously for maximum coverage
"""

import asyncio
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    try:
        import requests
        REQUESTS_AVAILABLE = True
    except ImportError:
        REQUESTS_AVAILABLE = False

try:
    from fame_config import (
        SERPAPI_KEY as CONFIG_KEY, 
        SERPAPI_KEY_BACKUP as CONFIG_BACKUP,
    )
    if not os.getenv('SERPAPI_KEY'):
        os.environ['SERPAPI_KEY'] = CONFIG_KEY
    if not os.getenv('SERPAPI_KEY_BACKUP'):
        os.environ['SERPAPI_KEY_BACKUP'] = CONFIG_BACKUP
except ImportError:
    pass


class ParallelSearchExecutor:
    """Executes all search APIs in parallel"""
    
    def __init__(self):
        # Load API keys from environment
        self.google_api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
        self.google_cx = os.getenv('GOOGLE_SEARCH_CX')
        self.serpapi_key = os.getenv('SERPAPI_KEY')
        self.serpapi_backup = os.getenv('SERPAPI_KEY_BACKUP')
        self.bing_key = os.getenv('BING_SEARCH_API_KEY')
        self.newsapi_key = os.getenv('NEWSAPI_KEY')
        
        # Check which APIs are available
        self.available_apis = []
        if self.serpapi_key or self.serpapi_backup:
            self.available_apis.append('serpapi')
        if self.google_api_key and self.google_cx:
            self.available_apis.append('google')
        if self.bing_key:
            self.available_apis.append('bing')
        if self.newsapi_key:
            self.available_apis.append('newsapi')
    
    async def search_serpapi_async(self, session: Any, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Async SerpAPI search"""
        api_keys = []
        if self.serpapi_key:
            api_keys.append(self.serpapi_key)
        if self.serpapi_backup:
            api_keys.append(self.serpapi_backup)
        
        if not api_keys:
            return []
        
        for api_key in api_keys:
            try:
                url = "https://serpapi.com/search"
                params = {
                    'api_key': api_key,
                    'q': query,
                    'engine': 'google',
                    'num': num_results
                }
                
                if AIOHTTP_AVAILABLE:
                    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                        if response.status == 200:
                            data = await response.json()
                            results = []
                            for item in data.get('organic_results', [])[:num_results]:
                                results.append({
                                    'title': item.get('title', ''),
                                    'snippet': item.get('snippet', ''),
                                    'link': item.get('link', ''),
                                    'source': 'SerpAPI'
                                })
                            return results
                        elif response.status == 401:
                            continue  # Try next key
                else:
                    # Fallback to requests in thread
                    import requests
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
            except Exception:
                continue
        
        return []
    
    async def search_google_async(self, session: Any, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Async Google Custom Search"""
        if not self.google_api_key or not self.google_cx:
            return []
        
        try:
            url = "https://customsearch.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_api_key,
                'cx': self.google_cx,
                'q': query,
                'num': num_results
            }
            
            if AIOHTTP_AVAILABLE:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        for item in data.get('items', [])[:num_results]:
                            results.append({
                                'title': item.get('title', ''),
                                'snippet': item.get('snippet', ''),
                                'link': item.get('link', ''),
                                'source': 'Google Custom Search'
                            })
                        return results
            else:
                import requests
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
        except Exception:
            pass
        
        return []
    
    async def search_bing_async(self, session: Any, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Async Bing search"""
        if not self.bing_key:
            return []
        
        try:
            url = "https://api.bing.microsoft.com/v7.0/search"
            headers = {'Ocp-Apim-Subscription-Key': self.bing_key}
            params = {'q': query, 'count': num_results}
            
            if AIOHTTP_AVAILABLE:
                async with session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        for item in data.get('webPages', {}).get('value', [])[:num_results]:
                            results.append({
                                'title': item.get('name', ''),
                                'snippet': item.get('snippet', ''),
                                'link': item.get('url', ''),
                                'source': 'Bing'
                            })
                        return results
            else:
                import requests
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
        except Exception:
            pass
        
        return []
    
    async def search_newsapi_async(self, session: Any, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Async NewsAPI search"""
        if not self.newsapi_key:
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
            
            if AIOHTTP_AVAILABLE:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        for article in data.get('articles', [])[:num_results]:
                            results.append({
                                'title': article.get('title', ''),
                                'snippet': article.get('description', ''),
                                'link': article.get('url', ''),
                                'publishedAt': article.get('publishedAt', ''),
                                'source': article.get('source', {}).get('name', ''),
                                'type': 'news'
                            })
                        return results
            else:
                import requests
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    for article in data.get('articles', [])[:num_results]:
                        results.append({
                            'title': article.get('title', ''),
                            'snippet': article.get('description', ''),
                            'link': article.get('url', ''),
                            'publishedAt': article.get('publishedAt', ''),
                            'source': article.get('source', {}).get('name', ''),
                            'type': 'news'
                        })
                    return results
        except Exception:
            pass
        
        return []
    
    async def search_all_parallel(self, query: str, num_results: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        Execute all available search APIs in parallel
        
        Returns:
            Dictionary mapping API names to their results
        """
        all_results = {}
        
        if AIOHTTP_AVAILABLE:
            async with aiohttp.ClientSession() as session:
                tasks = []
                
                if 'serpapi' in self.available_apis:
                    tasks.append(('serpapi', self.search_serpapi_async(session, query, num_results)))
                if 'google' in self.available_apis:
                    tasks.append(('google', self.search_google_async(session, query, num_results)))
                if 'bing' in self.available_apis:
                    tasks.append(('bing', self.search_bing_async(session, query, num_results)))
                if 'newsapi' in self.available_apis:
                    tasks.append(('newsapi', self.search_newsapi_async(session, query, num_results)))
                
                if tasks:
                    results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
                    for (api_name, _), result in zip(tasks, results):
                        if isinstance(result, Exception):
                            all_results[api_name] = []
                        else:
                            all_results[api_name] = result
        else:
            # Fallback to sequential execution if aiohttp not available
            import requests
            if 'serpapi' in self.available_apis:
                all_results['serpapi'] = await asyncio.to_thread(
                    self._search_serpapi_sync, query, num_results
                )
            if 'google' in self.available_apis:
                all_results['google'] = await asyncio.to_thread(
                    self._search_google_sync, query, num_results
                )
            if 'bing' in self.available_apis:
                all_results['bing'] = await asyncio.to_thread(
                    self._search_bing_sync, query, num_results
                )
            if 'newsapi' in self.available_apis:
                all_results['newsapi'] = await asyncio.to_thread(
                    self._search_newsapi_sync, query, num_results
                )
        
        return all_results
    
    def _search_serpapi_sync(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Synchronous SerpAPI search for fallback"""
        import requests
        api_keys = [k for k in [self.serpapi_key, self.serpapi_backup] if k]
        for api_key in api_keys:
            try:
                url = "https://serpapi.com/search"
                params = {'api_key': api_key, 'q': query, 'engine': 'google', 'num': num_results}
                response = requests.get(url, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    return [{
                        'title': item.get('title', ''),
                        'snippet': item.get('snippet', ''),
                        'link': item.get('link', ''),
                        'source': 'SerpAPI'
                    } for item in data.get('organic_results', [])[:num_results]]
            except:
                continue
        return []
    
    def _search_google_sync(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Synchronous Google search for fallback"""
        import requests
        try:
            url = "https://customsearch.googleapis.com/customsearch/v1"
            params = {'key': self.google_api_key, 'cx': self.google_cx, 'q': query, 'num': num_results}
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [{
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'link': item.get('link', ''),
                    'source': 'Google Custom Search'
                } for item in data.get('items', [])[:num_results]]
        except:
            pass
        return []
    
    def _search_bing_sync(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Synchronous Bing search for fallback"""
        import requests
        try:
            url = "https://api.bing.microsoft.com/v7.0/search"
            headers = {'Ocp-Apim-Subscription-Key': self.bing_key}
            params = {'q': query, 'count': num_results}
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [{
                    'title': item.get('name', ''),
                    'snippet': item.get('snippet', ''),
                    'link': item.get('url', ''),
                    'source': 'Bing'
                } for item in data.get('webPages', {}).get('value', [])[:num_results]]
        except:
            pass
        return []
    
    def _search_newsapi_sync(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Synchronous NewsAPI search for fallback"""
        import requests
        try:
            url = "https://newsapi.org/v2/everything"
            params = {'apiKey': self.newsapi_key, 'q': query, 'sortBy': 'publishedAt', 'language': 'en', 'pageSize': num_results}
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [{
                    'title': article.get('title', ''),
                    'snippet': article.get('description', ''),
                    'link': article.get('url', ''),
                    'source': article.get('source', {}).get('name', ''),
                    'type': 'news'
                } for article in data.get('articles', [])[:num_results]]
        except:
            pass
        return []
    
    def aggregate_results(self, all_results: Dict[str, List[Dict[str, Any]]], max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Aggregate results from all APIs, removing duplicates and prioritizing
        
        Args:
            all_results: Dictionary mapping API names to results
            max_results: Maximum number of results to return
        
        Returns:
            Aggregated list of unique results
        """
        seen_links = set()
        aggregated = []
        
        # Priority order: SerpAPI, Google, Bing, NewsAPI
        priority_order = ['serpapi', 'google', 'bing', 'newsapi']
        
        for api_name in priority_order:
            if api_name in all_results:
                for result in all_results[api_name]:
                    link = result.get('link', result.get('url', ''))
                    if link and link not in seen_links:
                        seen_links.add(link)
                        aggregated.append(result)
                        if len(aggregated) >= max_results:
                            break
                if len(aggregated) >= max_results:
                    break
        
        # Add any remaining results from other APIs
        for api_name, results in all_results.items():
            if api_name not in priority_order:
                for result in results:
                    link = result.get('link', result.get('url', ''))
                    if link and link not in seen_links:
                        seen_links.add(link)
                        aggregated.append(result)
                        if len(aggregated) >= max_results:
                            break
                    if len(aggregated) >= max_results:
                        break
        
        return aggregated

