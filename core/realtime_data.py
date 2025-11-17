#!/usr/bin/env python3
"""
FAME Real-Time Data Integration
Provides current information from reliable APIs
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

CACHE_FILE = CACHE_DIR / "realtime_data_cache.json"
CACHE_DURATION = timedelta(hours=1)  # Cache for 1 hour


def load_cache() -> Dict[str, Any]:
    """Load cached data"""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading cache: {e}")
    return {}


def save_cache(data: Dict[str, Any]):
    """Save data to cache"""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving cache: {e}")


def is_cache_valid(timestamp: str) -> bool:
    """Check if cached data is still valid"""
    try:
        cache_time = datetime.fromisoformat(timestamp)
        return datetime.now() - cache_time < CACHE_DURATION
    except:
        return False


def get_current_us_president() -> Dict[str, Any]:
    """
    Get current US President information
    
    Uses web search as fallback if API unavailable
    """
    cache = load_cache()
    cache_key = "us_president"
    
    # Check cache
    if cache_key in cache:
        cached_data = cache[cache_key]
        if is_cache_valid(cached_data.get("timestamp", "")):
            logger.info("Returning cached president data")
            return cached_data.get("data", {})
    
    # Try to get from reliable sources
    result = {
        "name": "Unknown",
        "year": 2025,
        "source": "fallback",
        "timestamp": datetime.now().isoformat()
    }
    
    # Strategy 1: Try web search (SERPAPI or similar)
    try:
        from core.web_scraper import WebScraper
        scraper = WebScraper()
        
        # Try multiple search methods
        search_queries = [
            "current US president 2025",
            "who is president of United States 2025",
            "US president 2025"
        ]
        
        for query in search_queries:
            try:
                # Try different search methods
                search_result = None
                
                # Method 1: Try SERPAPI search directly (most reliable)
                if hasattr(scraper, 'search_serpapi'):
                    search_result = scraper.search_serpapi(query, max_results=5)
                
                # Method 2: Try search_bug_fixing_techniques (generic search)
                if not search_result or not search_result.get('success'):
                    if hasattr(scraper, 'search_bug_fixing_techniques'):
                        search_result = scraper.search_bug_fixing_techniques(query)
                
                # Method 3: Try generic search method
                if not search_result or not search_result.get('success'):
                    if hasattr(scraper, 'search'):
                        search_result = scraper.search(query)
                
                # Method 4: Try web_search method
                if not search_result or not search_result.get('success'):
                    if hasattr(scraper, 'web_search'):
                        search_result = scraper.web_search(query)
                
                if search_result and (search_result.get('success') or search_result.get('results')):
                    results = search_result.get('results', [])
                    if not results and isinstance(search_result, list):
                        results = search_result
                    
                    # Parse results to find president
                    for item in results[:5]:
                        if isinstance(item, dict):
                            snippet = item.get('snippet', '').lower() or item.get('description', '').lower()
                            title = item.get('title', '').lower() or item.get('heading', '').lower()
                        else:
                            snippet = str(item).lower()
                            title = ""
                        
                        # Look for president mentions
                        combined_text = f"{snippet} {title}".lower()
                        if 'president' in combined_text:
                            # Try to extract name - prioritize recent mentions
                            if 'trump' in combined_text and ('2025' in combined_text or '2024' in combined_text):
                                result["name"] = "Donald Trump"
                                result["source"] = "web_search"
                                break
                            elif 'biden' in combined_text and ('2025' in combined_text or '2024' in combined_text):
                                result["name"] = "Joe Biden"
                                result["source"] = "web_search"
                                break
                            # Fallback: if no year, use first mention
                            elif 'trump' in combined_text and result["name"] == "Unknown":
                                result["name"] = "Donald Trump"
                                result["source"] = "web_search"
                            elif 'biden' in combined_text and result["name"] == "Unknown":
                                result["name"] = "Joe Biden"
                                result["source"] = "web_search"
                    
                    if result["name"] != "Unknown":
                        break
            except Exception as e:
                logger.debug(f"Search query '{query}' failed: {e}")
                continue
    except Exception as e:
        logger.debug(f"Web search failed: {e}")
    
    # Update cache
    cache[cache_key] = {
        "data": result,
        "timestamp": datetime.now().isoformat()
    }
    save_cache(cache)
    
    return result


def get_current_date_time() -> Dict[str, Any]:
    """Get current date and time"""
    now = datetime.now()
    return {
        "date": now.strftime("%A, %B %d, %Y"),
        "time": now.strftime("%I:%M %p"),
        "iso": now.isoformat(),
        "timestamp": now.timestamp()
    }


def verify_current_information(query: str, claimed_answer: str) -> Dict[str, Any]:
    """
    Verify if claimed information is current and accurate
    
    Args:
        query: The question asked
        claimed_answer: The answer provided
    
    Returns:
        Verification result with confidence and source
    """
    query_lower = query.lower()
    
    # Check for time-sensitive queries
    if "president" in query_lower and "current" in query_lower:
        president_info = get_current_us_president()
        claimed_lower = claimed_answer.lower()
        
        if president_info["name"].lower() in claimed_lower:
            return {
                "verified": True,
                "confidence": 0.9,
                "source": president_info["source"],
                "correct_answer": president_info["name"]
            }
        else:
            return {
                "verified": False,
                "confidence": 0.8,
                "source": president_info["source"],
                "correct_answer": president_info["name"],
                "claimed_answer": claimed_answer
            }
    
    # For other queries, return neutral
    return {
        "verified": None,
        "confidence": 0.5,
        "source": "unknown"
    }


def update_knowledge_base_with_current_data():
    """Update knowledge base with current information"""
    try:
        # Get current president
        president_info = get_current_us_president()
        
        # Store in knowledge base
        from core.knowledge_base import KNOWLEDGE_BASE_DIR
        current_data_file = KNOWLEDGE_BASE_DIR / "current_events.json"
        
        current_data = {
            "us_president": president_info,
            "last_updated": datetime.now().isoformat()
        }
        
        with open(current_data_file, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, indent=2)
        
        logger.info("Updated knowledge base with current data")
        return True
    except Exception as e:
        logger.error(f"Error updating knowledge base: {e}")
        return False


if __name__ == "__main__":
    # Test real-time data
    print("Current US President:")
    print(get_current_us_president())
    print("\nCurrent Date/Time:")
    print(get_current_date_time())

