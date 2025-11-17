#!/usr/bin/env python3
"""Test FAME Identity System"""

import asyncio
from fame_unified import get_fame

async def test_identity():
    fame = get_fame()
    
    test_queries = [
        "who are you?",
        "what can you do?",
        "can you upgrade yourself?",
        "what makes you special?"
    ]
    
    print("=" * 60)
    print("Testing FAME Identity System")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nQ: {query}")
        response = await fame.process_query({"text": query})
        print(f"A: {response.get('response', '')[:300]}")
        print(f"Source: {response.get('source', 'unknown')}")
        print(f"Confidence: {response.get('confidence', 'unknown')}")
        print(f"Intent: {response.get('intent', 'unknown')}")
        print("-" * 60)

if __name__ == "__main__":
    asyncio.run(test_identity())

