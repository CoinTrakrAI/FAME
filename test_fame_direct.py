#!/usr/bin/env python3
"""
Test FAME directly with the new IP and better error handling
"""

import requests
import sys
import time

FAME_API = "http://3.135.222.143:8080/query"
FAME_HEALTH = "http://3.135.222.143:8080/healthz"

def test_health():
    """Test health endpoint"""
    try:
        print(f"Testing health endpoint: {FAME_HEALTH}")
        r = requests.get(FAME_HEALTH, timeout=10)
        print(f"Status Code: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Health Status: {data.get('overall_status', 'unknown')}")
            return True
        else:
            print(f"Health check returned: {r.text[:200]}")
            return False
    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: {e}")
        print("\nThis means:")
        print("1. Service is not running")
        print("2. Port 8080 is blocked (even if Security Group allows it)")
        print("3. Container is not binding to 0.0.0.0")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def ask_fame(question):
    """Ask FAME a question"""
    try:
        print(f"\nQuestion: {question}")
        r = requests.post(
            FAME_API,
            json={'text': question, 'session_id': 'test', 'source': 'test'},
            timeout=30
        )
        
        if r.status_code == 200:
            data = r.json()
            response = data.get('response', 'No response')
            confidence = data.get('confidence', 0)
            intent = data.get('intent', 'unknown')
            sources = data.get('sources', [])
            
            print(f"FAME: {response}")
            print(f"\n[Intent: {intent} | Confidence: {confidence:.1%} | Sources: {', '.join(sources)}]")
            return True
        else:
            print(f"Error: HTTP {r.status_code}")
            print(f"Response: {r.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print("Connection Error: Cannot reach FAME")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("="*70)
    print("FAME Connection Test")
    print("="*70)
    
    # Test health first
    if test_health():
        print("\n✅ Health check passed! Testing questions...\n")
        print("="*70)
        
        questions = [
            "What's today's date?",
            "What's the current price of XRP?",
            "What is artificial intelligence?"
        ]
        
        for question in questions:
            ask_fame(question)
            time.sleep(1)
            print("\n" + "-"*70)
    else:
            print("\n[FAILED] Health check failed. Cannot proceed with questions.")
            print("The deployment may still be building. Wait a few minutes and try again.")
            sys.exit(1)

