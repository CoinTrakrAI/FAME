#!/usr/bin/env python3
"""Direct HTTP test - no SSH, just test the API endpoint"""
import requests

API = "http://3.17.56.74:8080/query"

questions = [
    "What's today's date?",
    "What's the current price of XRP?",
    "What is artificial intelligence?",
    "What's the price of Apple stock?",
    "Explain quantum computing in simple terms",
    "What's the current price of Bitcoin?",
    "Who won the 2024 US presidential election?",
    "What are the key features of Python programming language?",
    "Compare Tesla and Apple stock prices",
    "What is machine learning and how does it differ from AI?"
]

print("="*70)
print("FAME TEST - 10 QUESTIONS")
print("="*70)
print(f"\nTesting: {API}\n")

for i, q in enumerate(questions, 1):
    try:
        print(f"[{i}/10] YOU: {q}")
        r = requests.post(API, json={'text': q, 'session_id': 'test', 'source': 'test'}, timeout=10)
        
        if r.status_code == 200:
            d = r.json()
            ans = d.get('response', 'No response')
            conf = d.get('confidence', 0)
            print(f"FAME: {ans[:200]}...")
            print(f"      [Confidence: {conf:.1%}]\n")
        else:
            print(f"[ERROR] HTTP {r.status_code}: {r.text[:100]}\n")
            break
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Connection refused - FAME is not accessible\n")
        if i == 1:
            print("Container may not be running or port 8080 is blocked.")
            break
    except Exception as e:
        print(f"[ERROR] {e}\n")
        break

