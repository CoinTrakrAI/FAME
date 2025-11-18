#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test FAME with 10 random questions to see how he answers
"""

import requests
import time
import json
import sys

FAME_API = "http://3.17.56.74:8080/query"
FAME_HEALTH = "http://3.17.56.74:8080/healthz"

def check_health():
    """Check if FAME is available"""
    try:
        r = requests.get(FAME_HEALTH, timeout=5)
        if r.status_code == 200:
            return True, r.json()
        return False, None
    except:
        return False, None

def ask_fame(question, session_id="test_session"):
    """Ask FAME a question and get response"""
    try:
        r = requests.post(
            FAME_API,
            json={
                'text': question,
                'session_id': session_id,
                'source': 'test'
            },
            timeout=30
        )
        
        if r.status_code == 200:
            return r.json()
        else:
            return {'error': f'HTTP {r.status_code}', 'response': r.text[:200]}
    except requests.exceptions.ConnectionError:
        return {'error': 'Connection refused', 'response': 'FAME is not accessible'}
    except Exception as e:
        return {'error': str(e), 'response': 'Error occurred'}

# 10 diverse questions
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

print("="*80)
print("FAME AGI TEST - 10 Random Questions")
print("="*80)
print(f"\nTesting against: {FAME_API}\n")

# Check health first
print("[Checking health...]")
is_healthy, health_data = check_health()

if is_healthy:
    print("[SUCCESS] FAME is healthy and ready!\n")
    if health_data:
        status = health_data.get('overall_status', 'unknown')
        print(f"System Status: {status}\n")
else:
    print("[WARNING] Health check failed, but will try to ask questions anyway...\n")
    print("If all questions fail, FAME may still be deploying. Wait 2-3 minutes.\n")

print("="*80)
print("ASKING QUESTIONS")
print("="*80)

session_id = f"test_{int(time.time())}"
results = []

for i, question in enumerate(questions, 1):
    print(f"\n[Question {i}/10]")
    print(f"YOU: {question}")
    print("-" * 80)
    
    response = ask_fame(question, session_id)
    
    if 'error' in response:
        print(f"FAME: [ERROR] {response.get('error')}")
        print(f"       {response.get('response', '')}")
        results.append({'question': question, 'success': False, 'error': response.get('error')})
    else:
        answer = response.get('response', 'No response')
        intent = response.get('intent', 'unknown')
        confidence = response.get('confidence', 0)
        sources = response.get('sources', [])
        processing_time = response.get('processing_time', 0)
        
        print(f"FAME: {answer}")
        print(f"\n[Intent: {intent} | Confidence: {confidence:.1%} | Time: {processing_time:.2f}s]")
        if sources:
            print(f"[Sources: {', '.join(sources[:3])}]")  # Show first 3 sources
        
        # Check if response is meaningful (not just an error message)
        is_meaningful = len(answer) > 20 and 'error' not in answer.lower() and 'cannot' not in answer.lower()
        results.append({
            'question': question,
            'success': True,
            'meaningful': is_meaningful,
            'confidence': confidence,
            'intent': intent
        })
    
    time.sleep(1)  # Small delay between questions

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

successful = sum(1 for r in results if r.get('success'))
meaningful = sum(1 for r in results if r.get('meaningful'))
failed = len(results) - successful
avg_confidence = sum(r.get('confidence', 0) for r in results if r.get('success')) / max(successful, 1)

print(f"\nTotal Questions: {len(questions)}")
print(f"Successful Responses: {successful}")
print(f"Meaningful Responses: {meaningful}")
print(f"Failed: {failed}")
print(f"Average Confidence: {avg_confidence:.1%}")
print(f"Success Rate: {(successful/len(questions)*100):.1f}%")
print(f"Meaningful Rate: {(meaningful/len(questions)*100):.1f}%")

if successful == len(questions):
    print("\n[SUCCESS] All questions answered! FAME is working correctly.")
elif successful > 5:
    print(f"\n[GOOD] Most questions answered ({successful}/{len(questions)}). FAME is operational.")
elif successful > 0:
    print(f"\n[PARTIAL] Some questions answered ({successful}/{len(questions)}). FAME may still be initializing.")
else:
    print("\n[FAILED] No questions answered. FAME may not be running or accessible.")

print("\n" + "="*80)

