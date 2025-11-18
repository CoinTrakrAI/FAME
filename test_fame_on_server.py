#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test FAME on Deployed Server (Internet Access)
Tests FAME's knowledge and internet connectivity from the deployed EC2 instance
"""

import requests
import time
import os
from typing import Dict, Any, Optional
import sys

# Default server URL - UPDATE THIS WITH YOUR EC2 IP
# Get your EC2 IP from: AWS Console → EC2 → Instances → Public IPv4 address
FAME_SERVER = os.getenv("FAME_SERVER_URL", "http://3.17.56.74:8080")
FAME_API = f"{FAME_SERVER}/query"
FAME_HEALTH = f"{FAME_SERVER}/healthz"
FAME_DOCS = f"{FAME_SERVER}/docs"


def check_health() -> tuple[bool, Optional[Dict[str, Any]]]:
    """Check if FAME server is accessible and healthy"""
    try:
        print(f"[CHECKING] Testing connection to: {FAME_SERVER}")
        r = requests.get(FAME_HEALTH, timeout=10)
        if r.status_code == 200:
            data = r.json()
            print(f"[SUCCESS] FAME is healthy and accessible!")
            print(f"  Status: {data.get('overall_status', 'unknown')}")
            return True, data
        else:
            print(f"[WARNING] Health check returned status {r.status_code}")
            return False, None
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Cannot connect to {FAME_SERVER}")
        print(f"  → Check that EC2 instance is running")
        print(f"  → Verify security group allows port 8080")
        print(f"  → Confirm the IP address is correct")
        return False, None
    except requests.exceptions.Timeout:
        print(f"[ERROR] Connection timeout - server may be slow to respond")
        return False, None
    except Exception as e:
        print(f"[ERROR] Health check failed: {e}")
        return False, None


def test_internet_access() -> bool:
    """Test if FAME can access the internet"""
    print("\n[TESTING] Internet Access Test")
    print("=" * 80)
    
    # Questions that require internet access
    internet_tests = [
        "What is the current price of Bitcoin?",
        "What's the latest news about Apple stock?",
        "What is today's date and time?",
        "Who won the 2024 US Presidential election?",
    ]
    
    results = []
    for question in internet_tests:
        print(f"\n[QUESTION] {question}")
        try:
            start = time.time()
            response = requests.post(
                FAME_API,
                json={'text': question, 'session_id': 'internet_test'},
                timeout=90
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                print(f"[RESPONSE] ({elapsed:.2f}s)")
                print(f"  {data.get('response', '')[:200]}...")
                print(f"  Confidence: {data.get('confidence', 0):.2f}")
                print(f"  Source: {data.get('source', 'unknown')}")
                results.append(True)
            else:
                print(f"[ERROR] HTTP {response.status_code}: {response.text[:200]}")
                results.append(False)
        except Exception as e:
            print(f"[ERROR] {e}")
            results.append(False)
        
        time.sleep(1)  # Rate limiting
    
    success_rate = sum(results) / len(results) if results else 0
    print(f"\n[RESULT] Internet Access Test: {success_rate*100:.0f}% success rate")
    return success_rate > 0.5


def test_knowledge_base() -> bool:
    """Test FAME's knowledge base"""
    print("\n[TESTING] Knowledge Base Test")
    print("=" * 80)
    
    knowledge_tests = [
        "Explain what options trading is",
        "What is the Kelly Criterion?",
        "Explain implied volatility skew",
        "What are the differences between growth and value stocks?",
        "What is dollar cost averaging?",
    ]
    
    results = []
    for question in knowledge_tests:
        print(f"\n[QUESTION] {question}")
        try:
            start = time.time()
            response = requests.post(
                FAME_API,
                json={'text': question, 'session_id': 'knowledge_test'},
                timeout=90
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                print(f"[RESPONSE] ({elapsed:.2f}s)")
                print(f"  {data.get('response', '')[:200]}...")
                print(f"  Confidence: {data.get('confidence', 0):.2f}")
                print(f"  Source: {data.get('source', 'unknown')}")
                results.append(True)
            else:
                print(f"[ERROR] HTTP {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"[ERROR] {e}")
            results.append(False)
        
        time.sleep(1)
    
    success_rate = sum(results) / len(results) if results else 0
    print(f"\n[RESULT] Knowledge Base Test: {success_rate*100:.0f}% success rate")
    return success_rate > 0.5


def test_investment_analysis() -> bool:
    """Test FAME's investment analysis capabilities"""
    print("\n[TESTING] Investment Analysis Test")
    print("=" * 80)
    
    investment_tests = [
        "Should I invest in Apple stock right now?",
        "Analyze Tesla stock comprehensively",
        "What are the best dividend stocks for 2024?",
        "What are the current market risks?",
        "What's the IV skew for SPY options?",
    ]
    
    results = []
    for question in investment_tests:
        print(f"\n[QUESTION] {question}")
        try:
            start = time.time()
            response = requests.post(
                FAME_API,
                json={'text': question, 'session_id': 'investment_test'},
                timeout=90
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                print(f"[RESPONSE] ({elapsed:.2f}s)")
                print(f"  {data.get('response', '')[:200]}...")
                print(f"  Confidence: {data.get('confidence', 0):.2f}")
                print(f"  Source: {data.get('source', 'unknown')}")
                results.append(True)
            else:
                print(f"[ERROR] HTTP {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"[ERROR] {e}")
            results.append(False)
        
        time.sleep(1)
    
    success_rate = sum(results) / len(results) if results else 0
    print(f"\n[RESULT] Investment Analysis Test: {success_rate*100:.0f}% success rate")
    return success_rate > 0.5


def interactive_test():
    """Interactive mode - ask FAME questions"""
    print("\n" + "=" * 80)
    print("INTERACTIVE MODE - Test FAME directly")
    print("=" * 80)
    print(f"Server: {FAME_SERVER}")
    print("Type 'exit' or 'quit' to stop")
    print("Type 'health' to check server status")
    print("-" * 80)
    
    session_id = f"interactive_{int(time.time())}"
    
    while True:
        try:
            question = input("\n[YOU] ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['exit', 'quit', 'q']:
                print("\n[EXITING] Goodbye!")
                break
            
            if question.lower() == 'health':
                healthy, _ = check_health()
                continue
            
            print("[FAME] Thinking...")
            start = time.time()
            
            response = requests.post(
                FAME_API,
                json={'text': question, 'session_id': session_id},
                timeout=90
            )
            
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n[FAME] ({elapsed:.2f}s, confidence: {data.get('confidence', 0):.2f})")
                print(f"{data.get('response', 'No response')}")
                if 'error' in data:
                    print(f"[WARNING] Error: {data['error']}")
            else:
                print(f"\n[ERROR] HTTP {response.status_code}: {response.text[:200]}")
        
        except KeyboardInterrupt:
            print("\n\n[EXITING] Goodbye!")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")


def main():
    """Main test function"""
    # Get server URL from environment or use default
    server_url = os.getenv("FAME_SERVER_URL")
    if server_url:
        global FAME_SERVER, FAME_API, FAME_HEALTH, FAME_DOCS
        FAME_SERVER = server_url
        FAME_API = f"{FAME_SERVER}/query"
        FAME_HEALTH = f"{FAME_SERVER}/healthz"
        FAME_DOCS = f"{FAME_SERVER}/docs"
    
    print("=" * 80)
    print("FAME SERVER TEST SUITE")
    print("Testing FAME on Deployed EC2 Instance")
    print("=" * 80)
    print(f"Server URL: {FAME_SERVER}")
    print(f"API Endpoint: {FAME_API}")
    print(f"Health Check: {FAME_HEALTH}")
    print(f"Interactive Docs: {FAME_DOCS}")
    print("=" * 80)
    
    # Check health first
    healthy, health_data = check_health()
    if not healthy:
        print("\n[FAILED] Cannot connect to FAME server. Please check:")
        print("  1. EC2 instance is running")
        print("  2. Security group allows port 8080")
        print("  3. IP address is correct (check AWS Console)")
        print("  4. FAME container is running")
        print(f"\nUpdate FAME_SERVER_URL or edit this script if using different IP")
        sys.exit(1)
    
    print("\n[INFO] Running comprehensive tests...")
    print("This will test:")
    print("  • Internet connectivity (FAME's access to web)")
    print("  • Knowledge base (FAME's training/knowledge)")
    print("  • Investment analysis (FAME's financial expertise)")
    
    # Run tests
    internet_ok = test_internet_access()
    knowledge_ok = test_knowledge_base()
    investment_ok = test_investment_analysis()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Internet Access:     {'✅ PASS' if internet_ok else '❌ FAIL'}")
    print(f"Knowledge Base:      {'✅ PASS' if knowledge_ok else '❌ FAIL'}")
    print(f"Investment Analysis: {'✅ PASS' if investment_ok else '❌ FAIL'}")
    print("=" * 80)
    
    if internet_ok and knowledge_ok and investment_ok:
        print("\n[SUCCESS] All tests passed! FAME is ready for training.")
    else:
        print("\n[WARNING] Some tests failed. Review output above.")
    
    # Ask if user wants interactive mode
    print("\n" + "-" * 80)
    response = input("Enter interactive mode? (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        interactive_test()


if __name__ == "__main__":
    main()

