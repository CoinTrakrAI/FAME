#!/usr/bin/env python3
"""
FAME Assistant - AWS Server Communication
Chat with FAME on AWS EC2 through the API
"""

import requests
import json
import sys
from datetime import datetime

# FAME API endpoint on AWS EC2
FAME_API_URL = "http://3.135.222.143:8080/query"
FAME_HEALTH_URL = "http://3.135.222.143:8080/healthz"

def check_connection():
    """Check if FAME is available on AWS"""
    try:
        r = requests.get(FAME_HEALTH_URL, timeout=5)
        if r.status_code == 200:
            health = r.json()
            status = health.get('overall_status', 'unknown')
            return status == 'healthy', health
        return False, None
    except requests.exceptions.RequestException as e:
        return False, None

def send_query(text, session_id=None):
    """Send query to FAME on AWS"""
    try:
        payload = {
            "text": text,
            "session_id": session_id or f"session_{int(datetime.now().timestamp())}",
            "source": "aws_chat_client"
        }
        
        r = requests.post(FAME_API_URL, json=payload, timeout=30)
        
        if r.status_code == 200:
            return r.json()
        else:
            return {
                "error": f"Server returned status {r.status_code}",
                "response": r.text[:200]
            }
    except requests.exceptions.Timeout:
        return {
            "error": "Request timeout - FAME may be processing a complex query",
            "response": "Please try again with a simpler question."
        }
    except requests.exceptions.ConnectionError:
        return {
            "error": "Cannot connect to FAME on AWS",
            "response": "Please check that FAME is running on AWS EC2 and accessible."
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {type(e).__name__}",
            "response": str(e)[:200]
        }

def main():
    print("=" * 70)
    print("FAME ASSISTANT - AWS SERVER CONNECTION")
    print("=" * 70)
    print(f"\nConnecting to FAME on AWS: {FAME_API_URL}")
    
    # Check connection
    is_healthy, health_data = check_connection()
    if not is_healthy:
        print("\n⚠️  WARNING: Cannot connect to FAME on AWS")
        print("   Please verify:")
        print(f"   1. FAME is running on AWS EC2 at {FAME_API_URL}")
        print("   2. The EC2 instance is accessible")
        print("   3. Security groups allow port 8080")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    else:
        print("✅ FAME is healthy and ready!")
        if health_data:
            system = health_data.get('system', {})
            print(f"   Memory: {system.get('memory_percent', 'N/A')}%")
            print(f"   CPU: {system.get('cpu_percent', 'N/A')}%")
    
    print("\nFAME can help you with:")
    print("  • Stock prices and analysis")
    print("  • Cryptocurrency information")
    print("  • Market trends and insights")
    print("  • Business intelligence")
    print("  • General questions")
    print("\nType 'exit' or 'quit' to end the conversation")
    print("=" * 70)
    print()
    
    # Create a session for this conversation
    session_id = f"user_{int(datetime.now().timestamp())}"
    turn_count = 0
    
    while True:
        try:
            # Get user input
            user_input = input("YOU: ").strip()
            
            if not user_input:
                continue
            
            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                print("\nFAME: Goodbye! Have a great day!")
                break
            
            # Send to FAME on AWS
            turn_count += 1
            print(f"\nFAME: ", end="", flush=True)
            
            result = send_query(user_input, session_id)
            
            # Display FAME's response
            if "error" in result:
                print(f"⚠️  Error: {result.get('error')}")
                print(f"   {result.get('response', '')}")
            else:
                reply = result.get('response', 'I did not understand that.')
                confidence = result.get('confidence', 0.0)
                source = result.get('source', 'unknown')
                
                print(reply)
                
                # Show debug info (confidence and source) for first few turns
                if turn_count <= 3:
                    conf_pct = f"{confidence * 100:.1f}%" if isinstance(confidence, (int, float)) else str(confidence)
                    print(f"      [Source: {source}, Confidence: {conf_pct}]")
            
            print()  # Blank line for readability
            
        except KeyboardInterrupt:
            print("\n\nFAME: Goodbye! Have a great day!")
            break
        except Exception as e:
            print(f"\n⚠️  Unexpected error: {e}")
            print("Please try again or type 'exit' to quit.\n")

if __name__ == "__main__":
    main()

