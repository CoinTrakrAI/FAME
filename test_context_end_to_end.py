#!/usr/bin/env python3
"""End-to-End Test: Context-Aware Routing for Yes/No Confusion"""

import asyncio
from fame_unified import get_fame

async def test():
    print("=" * 60)
    print("End-to-End Test: Context-Aware Routing")
    print("=" * 60)
    
    fame = get_fame()
    
    print("\n1. Setting up context...")
    response1 = await fame.process_query({
        'text': 'Would you like me to help you create a build script?'
    })
    print(f"   Response 1 type: {response1.get('type', 'unknown')}")
    
    print("\n2. Testing 'yes' response (should be build_instructions, not web search)...")
    response2 = await fame.process_query({'text': 'yes'})
    print(f"   Response 2 type: {response2.get('type', 'unknown')}")
    print(f"   Confidence: {response2.get('confidence', 0):.2f}")
    print(f"   Source: {response2.get('source', 'unknown')}")
    print(f"   Preview: {response2.get('response', '')[:200]}...")
    
    if response2.get('type') == 'build_instructions':
        print("\n   [SUCCESS] Context-aware routing working!")
        print("   'yes' correctly interpreted as affirmative, not web search")
    elif response2.get('source') == 'web_scraper' or 'Yes' in response2.get('response', ''):
        print("\n   [FAILED] Still searching web for band 'Yes'")
    else:
        print(f"\n   [WARNING] Unexpected response type: {response2.get('type')}")
    
    print("\n3. Testing 'no' response...")
    response3 = await fame.process_query({'text': 'no'})
    print(f"   Response 3 type: {response3.get('type', 'unknown')}")
    if response3.get('type') == 'negative_followup':
        print("   [SUCCESS] 'no' correctly handled as negative follow-up")

if __name__ == "__main__":
    asyncio.run(test())

