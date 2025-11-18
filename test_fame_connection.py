#!/usr/bin/env python3
"""
Simple FAME connection test
"""

import requests
import sys

FAME_API = "http://3.135.222.143:8080/query"
FAME_HEALTH = "http://3.135.222.143:8080/healthz"

def test_connection():
    """Test if FAME is accessible"""
    print("Testing FAME connection...")
    print(f"Health endpoint: {FAME_HEALTH}")
    print(f"Query endpoint: {FAME_API}\n")
    
    # Test health endpoint
    try:
        print("[1] Testing health endpoint...")
        r = requests.get(FAME_HEALTH, timeout=5)
        if r.status_code == 200:
            print("[SUCCESS] Health check passed!")
            health = r.json()
            print(f"   Status: {health.get('overall_status', 'unknown')}")
            return True
        else:
            print(f"[FAILED] Health check returned {r.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[FAILED] Connection refused - Port 8080 not accessible")
        print("\nPossible issues:")
        print("1. EC2 Security Group doesn't allow inbound on port 8080")
        print("2. Firewall blocking the connection")
        print("3. Container not exposing port 8080 correctly")
        print("\nSolution:")
        print("Go to AWS Console -> EC2 -> Security Groups")
        print("Add inbound rule: Type=Custom TCP, Port=8080, Source=0.0.0.0/0")
        return False
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return False

def ask_question(question):
    """Ask FAME a question"""
    try:
        print(f"\n[2] Asking FAME: '{question}'")
        r = requests.post(
            FAME_API,
            json={
                'text': question,
                'session_id': 'test',
                'source': 'test'
            },
            timeout=30
        )
        
        if r.status_code == 200:
            data = r.json()
            response = data.get('response', 'No response')
            confidence = data.get('confidence', 0)
            intent = data.get('intent', 'unknown')
            
            print(f"[SUCCESS] FAME responded!")
            print(f"\nFAME: {response}")
            print(f"\nIntent: {intent} | Confidence: {confidence:.1%}")
            return True
        else:
            print(f"[FAILED] Server returned {r.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return False

if __name__ == "__main__":
    # Test connection
    if not test_connection():
        sys.exit(1)
    
    # If health check passed, ask a question
    print("\n" + "="*70)
    if ask_question("What's today's date?"):
        print("\n[SUCCESS] FAME is working and can answer questions!")
        print("\nTest complete. FAME is operational.")
    else:
        print("\n[FAILED] Could not get response from FAME")

