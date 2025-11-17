#!/usr/bin/env python3
"""
Test FAME Core Integration
Quick test to verify all systems are working
"""

import asyncio
from core.brain_orchestrator import BrainOrchestrator

async def test_integration():
    """Test the complete integration"""
    print("=" * 70)
    print("FAME Core Integration Test")
    print("=" * 70)
    
    # Initialize orchestrator
    print("\n[1/5] Initializing Brain Orchestrator...")
    orchestrator = BrainOrchestrator()
    
    # Check health
    print("\n[2/5] Checking system health...")
    health = orchestrator.get_health_status()
    print(f"✅ Plugins loaded: {health['plugins_loaded']}")
    print(f"✅ Plugin names: {', '.join(health['plugin_names'][:5])}...")
    print(f"✅ Safety enabled: {health['safety_enabled']}")
    
    # Test query routing
    print("\n[3/5] Testing query routing...")
    test_queries = [
        {'text': 'hello', 'source': 'test'},
        {'text': 'who is the current US president', 'source': 'test'},
        {'text': 'how to build a reverse proxy', 'source': 'test'},
    ]
    
    for query in test_queries:
        print(f"\n  Testing: {query['text']}")
        result = await orchestrator.handle_query(query)
        response = result.get('response', str(result))
        print(f"  Response: {str(response)[:100]}...")
    
    # Test safety
    print("\n[4/5] Testing safety controller...")
    allowed, reason = orchestrator.safety.check_permission(
        capability='universal_hacker',
        operation='test',
        context={}
    )
    print(f"  Dangerous capability check: {'✅ Blocked' if not allowed else '⚠️ Allowed'}")
    print(f"  Reason: {reason}")
    
    # Test sandbox (if Docker available)
    print("\n[5/5] Testing sandbox execution...")
    test_code = "print('Hello from sandbox!')"
    sandbox_result = orchestrator.run_in_sandbox(test_code, timeout=10)
    if sandbox_result.get('success'):
        print(f"  ✅ Sandbox test passed")
    else:
        print(f"  ⚠️ Sandbox test: {sandbox_result.get('error', 'Not available')}")
    
    print("\n" + "=" * 70)
    print("Integration test complete!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_integration())

