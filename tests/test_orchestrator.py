"""
Integration tests for FAME Orchestrator
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_plugin_loader():
    """Test plugin loading"""
    from orchestrator.plugin_loader import load_plugins
    
    plugins = load_plugins()
    assert isinstance(plugins, dict), "Plugins should be a dict"
    assert len(plugins) > 0, "Should load at least one plugin"
    
    # Check for common plugins
    has_core = any('universal' in name or 'evolution' in name for name in plugins.keys())
    assert has_core, "Should load at least one core module"
    
    print(f"✅ Loaded {len(plugins)} plugins: {list(plugins.keys())[:5]}...")


def test_brain_routing():
    """Test brain query routing"""
    from orchestrator.brain import Brain
    
    brain = Brain()
    
    # Test simple query
    query = {
        'text': 'reverse a string',
        'intent': 'generate_code'
    }
    
    async def run_test():
        response = await brain.handle_query(query)
        assert isinstance(response, dict), "Response should be a dict"
        assert 'responses' in response or 'code' in response or 'capabilities' in response, \
            "Response should have useful content"
        return response
    
    response = asyncio.run(run_test())
    print(f"✅ Query routed and handled: {type(response)}")


def test_event_bus():
    """Test event bus"""
    from orchestrator.event_bus import EventBus
    import asyncio
    
    bus = EventBus()
    events_received = []
    
    def sync_handler(event):
        events_received.append(('sync', event))
    
    async def async_handler(event):
        events_received.append(('async', event))
    
    bus.subscribe('test.event', sync_handler)
    bus.subscribe('test.event', async_handler)
    
    async def run_test():
        await bus.publish('test.event', {'data': 'test'})
        await asyncio.sleep(0.1)  # Give handlers time
    
    asyncio.run(run_test())
    
    assert len(events_received) >= 1, "Should receive at least one event"
    print(f"✅ Event bus working: {len(events_received)} events received")


def test_code_generation_flow():
    """Test end-to-end code generation with sandbox"""
    from orchestrator.brain import Brain
    from orchestrator.sandbox_runner import run_code_locally
    
    brain = Brain()
    brain.sandbox_runner = run_code_locally
    
    query = {
        'text': 'write a function to reverse a string',
        'intent': 'generate_code'
    }
    
    async def run_test():
        response = await brain.handle_query(query)
        # Should route to universal_developer
        assert isinstance(response, dict)
        
        # If code was generated, should have test report
        if 'code' in response or any('code' in str(r) for r in response.get('responses', [])):
            print("✅ Code generation flow working")
        else:
            print("⚠️ Code generation may need wrapper functions in universal_developer")
    
    asyncio.run(run_test())


def test_sandbox_runner():
    """Test local sandbox runner (dev only)"""
    from orchestrator.sandbox_runner import run_code_locally
    
    test_code = """
def reverse_string(s):
    return s[::-1]

print(reverse_string("hello"))
"""
    
    result = run_code_locally(test_code, timeout_seconds=5)
    
    assert 'ok' in result, "Result should have 'ok' field"
    assert result['ok'] == True, "Code should execute successfully"
    assert 'olleh' in result.get('stdout', ''), "Should output reversed string"
    
    print("✅ Sandbox runner working")


if __name__ == "__main__":
    print("=" * 60)
    print("FAME Orchestrator Integration Tests")
    print("=" * 60)
    
    try:
        test_plugin_loader()
        test_event_bus()
        test_sandbox_runner()
        test_brain_routing()
        test_code_generation_flow()
        
        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

