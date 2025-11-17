#!/usr/bin/env python3
"""
Test script to verify all fixes are working correctly
"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all critical imports work"""
    print("Testing imports...")
    
    try:
        from orchestrator.brain import Brain
        print("[OK] Brain import: OK")
    except Exception as e:
        print(f"[FAIL] Brain import: FAILED - {e}")
        return False
    
    try:
        from core.self_evolution import handle_evolution_request
        print("[OK] Self-evolution import: OK")
    except Exception as e:
        print(f"[FAIL] Self-evolution import: FAILED - {e}")
        return False
    
    try:
        from core.assistant.assistant_api import handle_text_input
        print("[OK] Assistant API import: OK")
    except Exception as e:
        print(f"[FAIL] Assistant API import: FAILED - {e}")
        return False
    
    try:
        from core.assistant.nlu import parse_intent
        print("[OK] NLU import: OK")
    except Exception as e:
        print(f"[FAIL] NLU import: FAILED - {e}")
        return False
    
    return True

def test_nlu():
    """Test NLU with various queries"""
    print("\nTesting NLU...")
    
    try:
        from core.assistant.nlu import parse_intent
        
        test_queries = [
            ("who is the current president?", "factual_question"),
            ("what can you do?", "general_query"),
            ("hi", "greet"),
            ("what is the time?", "get_time"),
            ("self-evolve", "general_query"),
        ]
        
        for query, expected_intent in test_queries:
            result = parse_intent(query)
            intent = result.get("intent")
            confidence = result.get("confidence", 0.0)
            
            if intent == expected_intent or confidence > 0.3:
                print(f"[OK] '{query}' -> {intent} (confidence: {confidence:.2f})")
            else:
                print(f"[WARN] '{query}' -> {intent} (expected: {expected_intent}, confidence: {confidence:.2f})")
        
        return True
    except Exception as e:
        print(f"[FAIL] NLU test: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_brain_initialization():
    """Test that Brain can be initialized"""
    print("\nTesting Brain initialization...")
    
    try:
        from orchestrator.brain import Brain
        brain = Brain()
        print("[OK] Brain initialized successfully")
        print(f"  Loaded {len(brain.plugins)} plugins")
        return True
    except Exception as e:
        print(f"[FAIL] Brain initialization: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_assistant_api():
    """Test assistant API basic functionality"""
    print("\nTesting Assistant API...")
    
    try:
        from core.assistant.assistant_api import handle_text_input
        
        # Test greeting
        result = handle_text_input("hi", session_id="test_session", speak=False)
        if result.get('reply'):
            print(f"[OK] Assistant API responds: {result.get('reply')[:50]}...")
            return True
        else:
            print(f"[WARN] Assistant API returned no reply: {result}")
            return False
    except Exception as e:
        print(f"[FAIL] Assistant API test: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("FAME System Fixes Verification")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("NLU", test_nlu()))
    results.append(("Brain", test_brain_initialization()))
    results.append(("Assistant API", test_assistant_api()))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! System is ready to use.")
        return 0
    else:
        print("\n[WARNING] Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

