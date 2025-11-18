#!/usr/bin/env python3
"""
Test FAME with various questions to verify AGI functionality
"""

import requests
import json
import time

FAME_API = "http://3.135.222.143:8080/query"

def ask_fame(question, session_id="test_session"):
    """Ask FAME a question"""
    try:
        print(f"\n{'='*80}")
        print(f"YOU: {question}")
        print(f"{'='*80}")
        
        response = requests.post(
            FAME_API,
            json={
                'text': question,
                'session_id': session_id,
                'source': 'test'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('response', 'No response')
            intent = data.get('intent', 'unknown')
            confidence = data.get('confidence', 0.0)
            sources = data.get('sources', [])
            processing_time = data.get('processing_time', 0)
            
            print(f"\nFAME: {answer}")
            print(f"\n[Intent: {intent} | Confidence: {confidence:.1%} | Time: {processing_time:.2f}s]")
            if sources:
                print(f"[Sources: {', '.join(sources)}]")
            
            return {
                'success': True,
                'response': answer,
                'intent': intent,
                'confidence': confidence
            }
        else:
        print(f"[ERROR] HTTP {response.status_code}")
        print(f"Response: {response.text[:200]}")
        return {'success': False, 'error': f"HTTP {response.status_code}"}
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to FAME API. Is the service running?")
        print("[INFO] Check EC2 Security Group allows inbound traffic on port 8080")
        return {'success': False, 'error': 'Connection failed'}
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return {'success': False, 'error': str(e)}

def main():
    print("\n" + "="*80)
    print("FAME AGI TEST SUITE")
    print("="*80)
    print(f"Testing against: {FAME_API}\n")
    
    # Test questions covering different capabilities
    questions = [
        # Basic knowledge
        "What's today's date?",
        "What time is it?",
        
        # Current price queries (should use current price handler, not prediction)
        "What's the current price of XRP?",
        "What's Bitcoin's price right now?",
        
        # General knowledge
        "What is artificial intelligence?",
        "Explain quantum computing in simple terms",
        
        # Financial analysis
        "What's the price of Apple stock?",
        "Analyze the current cryptocurrency market",
        
        # Complex queries (should trigger Planner)
        "Compare Bitcoin and Ethereum and explain which might be better for long-term investment",
    ]
    
    results = []
    session_id = f"test_{int(time.time())}"
    
    for i, question in enumerate(questions, 1):
        print(f"\n[Question {i}/{len(questions)}]")
        result = ask_fame(question, session_id)
        results.append(result)
        
        if result['success']:
            # Check if response is generic or actually answers the question
            response_text = result['response'].lower()
            is_generic = any(generic in response_text for generic in [
                'i don\'t know',
                'i cannot',
                'i\'m not able',
                'unable to',
                'cannot answer',
                'i don\'t have'
            ])
            
            if is_generic:
                print("[WARNING] Response appears generic")
            else:
                print("[SUCCESS] Response appears to answer the question")
        
        # Small delay between questions
        if i < len(questions):
            time.sleep(2)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    successful = sum(1 for r in results if r.get('success'))
    failed = len(results) - successful
    avg_confidence = sum(r.get('confidence', 0) for r in results if r.get('success')) / max(successful, 1)
    
    print(f"Total Questions: {len(results)}")
    print(f"✅ Successful: {successful}")
    print(f"[FAILED] {failed}")
    print(f"Average Confidence: {avg_confidence:.1%}")
    print(f"Success Rate: {(successful/len(results)*100):.1f}%")
    
    if successful == len(results):
        print("\n[SUCCESS] All tests passed! FAME is working correctly.")
    elif successful > 0:
        print(f"\n[PARTIAL] Partial success: {successful}/{len(results)} questions answered")
    else:
        print("\n[FAILED] All tests failed. FAME may not be accessible or functioning correctly.")

if __name__ == "__main__":
    main()

