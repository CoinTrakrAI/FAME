#!/usr/bin/env python3
"""
Simple FAME test - asks questions when available
"""

import requests
import time

FAME_API = "http://3.135.222.143:8080/query"

questions = [
    "What's today's date?",
    "What's the current price of XRP?",
    "What is artificial intelligence?",
]

print("Testing FAME...")
print(f"API: {FAME_API}\n")

for question in questions:
    try:
        print(f"YOU: {question}")
        r = requests.post(
            FAME_API,
            json={'text': question, 'session_id': 'test', 'source': 'test'},
            timeout=30
        )
        
        if r.status_code == 200:
            data = r.json()
            response = data.get('response', 'No response')
            print(f"FAME: {response}\n")
        else:
            print(f"Error: HTTP {r.status_code}\n")
            break
    except requests.exceptions.ConnectionError:
        print("Cannot connect - FAME is still deploying or not running.\n")
        print("The deployment takes 3-5 minutes. Please wait and try again.")
        break
    except Exception as e:
        print(f"Error: {e}\n")
        break
    
    time.sleep(1)

