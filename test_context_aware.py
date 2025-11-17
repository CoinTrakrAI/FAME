#!/usr/bin/env python3
"""Test Context-Aware Routing"""

import asyncio
from fame_unified import get_fame
from core.context_aware_router import get_context_router

async def test():
    print("Testing Context-Aware Routing...")
    print("=" * 60)
    
    # Setup context
    router = get_context_router()
    router.add_to_context(
        'Would you like me to help you create a build script?',
        'Yes, I can help you create a build script...',
        'build_request'
    )
    
    print("\n1. Testing affirmative follow-up detection...")
    is_aff, conf, exp_type = router.is_affirmative_followup('yes')
    print(f"   Is affirmative: {is_aff}")
    print(f"   Confidence: {conf:.2f}")
    print(f"   Expected type: {exp_type}")
    
    print("\n2. Testing with FAME Unified...")
    fame = get_fame()
    
    # First, set up context by asking about build
    print("\n   Setting up context...")
    response1 = await fame.process_query({
        'text': 'Would you like me to help you create a build script?'
    })
    print(f"   Response 1 type: {response1.get('type', 'unknown')}")
    
    # Now test "yes" response
    print("\n   Testing 'yes' response...")
    response2 = await fame.process_query({'text': 'yes'})
    print(f"   Response 2 type: {response2.get('type', 'unknown')}")
    print(f"   Response 2 preview: {response2.get('response', '')[:200]}...")
    print(f"   Confidence: {response2.get('confidence', 0):.2f}")
    
    if response2.get('type') == 'build_instructions':
        print("\n   SUCCESS: Context-aware routing working!")
    else:
        print(f"\n   WARNING: Expected 'build_instructions', got '{response2.get('type')}'")

if __name__ == "__main__":
    asyncio.run(test())

