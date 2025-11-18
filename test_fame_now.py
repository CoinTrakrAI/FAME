# -*- coding: utf-8 -*-
"""
Direct FAME test - no delays, just ask questions NOW
"""
import requests
import json
import sys

API = "http://3.135.222.143:8080/query"

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

print("\n" + "="*70)
print("TESTING FAME - 10 QUESTIONS")
print("="*70)
print(f"API: {API}\n")

results = []
for i, question in enumerate(questions, 1):
    try:
        print(f"[{i}/10] YOU: {question}")
        r = requests.post(API, json={'text': question, 'session_id': 'test', 'source': 'test'}, timeout=15)
        
        if r.status_code == 200:
            data = r.json()
            answer = data.get('response', 'No response')
            conf = data.get('confidence', 0)
            intent = data.get('intent', 'unknown')
            
            # Show first 300 chars of answer
            answer_preview = answer[:300] + ('...' if len(answer) > 300 else '')
            print(f"FAME: {answer_preview}")
            print(f"     [Intent: {intent} | Confidence: {conf:.1%}]\n")
            
            results.append({'success': True, 'confidence': conf})
        else:
            print(f"[ERROR] HTTP {r.status_code}: {r.text[:100]}\n")
            results.append({'success': False})
            
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Cannot connect to FAME\n")
        results.append({'success': False})
        if i == 1:
            print("FAME is not accessible. Container may not be running.")
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {str(e)}\n")
        results.append({'success': False})
    
    time.sleep(0.5)

# Summary
successful = sum(1 for r in results if r.get('success'))
print("="*70)
print(f"RESULTS: {successful}/10 successful")
if successful > 0:
    avg_conf = sum(r.get('confidence', 0) for r in results if r.get('success')) / successful
    print(f"Average Confidence: {avg_conf:.1%}")
print("="*70)

