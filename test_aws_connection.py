#!/usr/bin/env python3
"""Test AWS connection for updated chat_with_fame.py"""

import requests
import json

FAME_API_URL = "http://18.220.108.23:8080/query"

print("Testing updated chat_with_fame.py AWS connection...")
print(f"API URL: {FAME_API_URL}")
print()

# Test the same format as updated chat_with_fame.py
payload = {
    "text": "Hello FAME, testing AWS connection",
    "session_id": "test_session",
    "source": "python_chat_client"
}

try:
    response = requests.post(FAME_API_URL, json=payload, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ SUCCESS: Updated chat_with_fame.py will connect to AWS!")
        print(f"Status: {response.status_code}")
        print(f"Response: {data.get('response', 'N/A')[:200]}")
        print(f"Source: {data.get('source', 'N/A')}")
        if 'confidence' in data:
            print(f"Confidence: {data.get('confidence')}")
    else:
        print(f"❌ FAILED: Server returned {response.status_code}")
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {str(e)}")

