#!/usr/bin/env python3
"""Verify Question 9 is routed correctly"""

import asyncio
from core.universal_developer import UniversalDeveloper

async def test():
    dev = UniversalDeveloper()
    req = {'requests_per_second': 10000, 'use_case': 'dynamic_routing_api_gateway'}
    result = await dev.compare_reverse_proxy_architectures(req)
    
    print("\n=== QUESTION 9 VERIFICATION ===")
    rec = result.get('recommendation', {})
    print(f"Recommended Proxy: {rec.get('recommended_proxy')}")
    print(f"Winner Score: {rec.get('winner_score')}")
    print(f"\nReasoning: {rec.get('reasoning', '')[:300]}...")
    print(f"\nKey Insight: {rec.get('key_insight', '')[:400]}...")
    
    if 'ENVOY' in rec.get('recommended_proxy', ''):
        print("\nCORRECT: Reverse proxy comparison answered!")
    else:
        print("\nERROR: Wrong answer type")

if __name__ == "__main__":
    asyncio.run(test())

