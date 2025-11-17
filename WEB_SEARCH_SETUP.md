# FAME Web Search Setup Guide

## Overview

FAME now supports real-time web search capabilities through multiple APIs. This allows FAME to access current information, financial data, and news.

## Supported Search Methods

### 1. SerpAPI (Recommended)
- **Pros:** Handles CAPTCHAs, proxies, very reliable
- **Cons:** Paid service (free tier available)
- **Setup:**
  ```bash
  set SERPAPI_KEY=your_key_here
  ```
- **Get API Key:** https://serpapi.com/

### 2. Google Custom Search API
- **Pros:** Reliable, Google results
- **Cons:** Requires both API key and Custom Search Engine ID
- **Setup:**
  ```bash
  set GOOGLE_SEARCH_API_KEY=your_key_here
  set GOOGLE_SEARCH_CX=your_search_engine_id
  ```
- **Get API Key:** https://developers.google.com/custom-search/v1/overview
- **Create Search Engine:** https://programmablesearchengine.google.com/

### 3. Bing Web Search API
- **Pros:** Microsoft-backed, reliable
- **Cons:** Requires Azure subscription
- **Setup:**
  ```bash
  set BING_SEARCH_API_KEY=your_key_here
  ```
- **Get API Key:** https://www.microsoft.com/en-us/bing/apis/bing-web-search-api

### 4. NewsAPI (For Financial News)
- **Pros:** Great for financial/market news
- **Cons:** Limited free tier
- **Setup:**
  ```bash
  set NEWSAPI_KEY=your_key_here
  ```
- **Get API Key:** https://newsapi.org/

### 5. Alpha Vantage (For Financial Data)
- **Pros:** Free tier, excellent for stock data
- **Cons:** Rate limited on free tier
- **Setup:**
  ```bash
  set ALPHA_VANTAGE_API_KEY=your_key_here
  ```
- **Get API Key:** https://www.alphavantage.co/support/#api-key

## Quick Setup

### Minimum Setup (One API)
```bash
# Option 1: SerpAPI (easiest)
set SERPAPI_KEY=your_serpapi_key

# Option 2: Google Custom Search
set GOOGLE_SEARCH_API_KEY=your_google_key
set GOOGLE_SEARCH_CX=your_search_engine_id

# Option 3: Bing
set BING_SEARCH_API_KEY=your_bing_key
```

### Recommended Setup (Multiple APIs)
```bash
# Primary search (SerpAPI or Google)
set SERPAPI_KEY=your_serpapi_key
# OR
set GOOGLE_SEARCH_API_KEY=your_google_key
set GOOGLE_SEARCH_CX=your_cx

# Financial news
set NEWSAPI_KEY=your_newsapi_key

# Stock data (optional, for enhanced financial queries)
set ALPHA_VANTAGE_API_KEY=your_alphavantage_key
```

## How It Works

1. **User asks a question** that needs current information
2. **FAME detects** if real-time data is needed
3. **FAME searches** using available APIs (tries SerpAPI first, then Google, then Bing)
4. **Results are formatted** and returned to user

## Usage Examples

```
You: What's the current US President?
FAME: [Searches web and returns current information]

You: What's happening in the stock market today?
FAME: [Searches financial news and returns results]

You: Latest news on AI stocks
FAME: [Searches financial news specifically]
```

## Without API Keys

If no API keys are configured, FAME will:
- Use cached knowledge for known facts
- Still respond intelligently but without real-time data
- Inform you that web search requires API keys

## Testing

Run the test script:
```bash
python fame_web_search.py
```

This will test your API key configuration and show sample results.

## Cost Considerations

- **SerpAPI:** Free tier: 100 searches/month, then paid
- **Google Custom Search:** Free tier: 100 queries/day, then $5 per 1000 queries
- **Bing:** Free tier: 1000 queries/month, then pay-as-you-go
- **NewsAPI:** Free tier: 100 requests/day
- **Alpha Vantage:** Free tier: 5 API calls/min, 500 calls/day

**For most users:** Start with SerpAPI free tier or Google Custom Search free tier.

## Troubleshooting

**"No search results found"**
- Check API keys are set correctly
- Verify API key is valid
- Check API quota hasn't been exceeded

**"Search error"**
- Check internet connection
- Verify API keys in environment variables
- Try a different search API

## Integration

The web search is automatically integrated into `fame_simple.py`. Just set your API keys and FAME will use them automatically for queries that need current information.

