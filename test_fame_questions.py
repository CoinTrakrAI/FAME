#!/usr/bin/env python3
"""
Test FAME with questions using the new IP
"""

import requests
import time

FAME_API = "http://3.135.222.143:8080/query"

questions = [
    "What's today's date?",
    "What's the current price of XRP?",
    "What is artificial intelligence?",
    "What's the price of Apple stock?"
]

print("Testing FAME with questions...")
print(f"API: {FAME_API}\n")

for i, question in enumerate(questions, 1):
    try:
        print(f"[{i}] YOU: {question}")
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
            
            print(f"     FAME: {response[:200]}...")
            print(f"     [Intent: {intent}, Confidence: {confidence:.1%}]\n")
        else:
            print(f"     [ERROR] HTTP {r.status_code}\n")
    except requests.exceptions.ConnectionError:
        print(f"     [ERROR] Cannot connect - Service may not be running or Security Group needs port 8080 open\n")
    except Exception as e:
        print(f"     [ERROR] {str(e)}\n")
    
    time.sleep(1)
