#!/usr/bin/env python3
"""
FAME Assistant - Interactive Chat Interface (AWS Server)
Chat with FAME on AWS EC2 through the API
"""

import requests
import json
import sys
from datetime import datetime

# FAME API endpoint on AWS EC2
FAME_API_URL = "http://18.220.108.23:8080/query"

def send_to_aws(text, session_id=None):
    """Send query to FAME on AWS EC2"""
    try:
        payload = {
            "text": text,
            "session_id": session_id or f"session_{int(datetime.now().timestamp())}",
            "source": "python_chat_client"
        }
        
        response = requests.post(FAME_API_URL, json=payload, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Server returned status {response.status_code}",
                "response": response.text[:200],
                "reply": f"Error: Server returned {response.status_code}"
            }
    except requests.exceptions.ConnectionError:
        return {
            "error": "Cannot connect to FAME on AWS",
            "reply": "❌ Cannot connect to FAME on AWS. Please check:\n  1. FAME is running on AWS EC2\n  2. Server is accessible at http://18.220.108.23:8080\n  3. Your network allows connections to port 8080"
        }
    except requests.exceptions.Timeout:
        return {
            "error": "Request timeout",
            "reply": "⏱️ Request timeout - FAME may be processing a complex query. Please try again."
        }
    except Exception as e:
        return {
            "error": str(e),
            "reply": f"❌ Error: {type(e).__name__}: {str(e)[:200]}"
        }

print("=" * 70)
print("FAME ASSISTANT - INTERACTIVE CHAT (AWS Server)")
print("=" * 70)
print(f"\nConnecting to FAME on AWS: {FAME_API_URL}")
print("\nWelcome! I'm FAME Assistant. I can help you with:")
print("  • Stock prices (e.g., 'what is the price of AAPL?')")
print("  • Cryptocurrency information")
print("  • Market trends and analysis")
print("  • Date and time queries")
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
        
        result = send_to_aws(user_input, session_id)
        
        # Display FAME's response
        if "error" in result and result.get("error") not in ["", None]:
            print(f"⚠️  Error: {result.get('error')}")
            reply = result.get('reply', result.get('response', 'I did not understand that.'))
        else:
            reply = result.get('response', result.get('reply', 'I did not understand that.'))
        
        print(reply)
        
        # Show debug info (source and confidence) for first few turns
        if turn_count <= 3 and "error" not in result:
            source = result.get('source', 'unknown')
            confidence = result.get('confidence', 0.0)
            if confidence:
                conf_pct = f"{confidence * 100:.1f}%" if isinstance(confidence, (int, float)) else str(confidence)
                print(f"      [Source: {source}, Confidence: {conf_pct}]")
        
        print()  # Blank line for readability
        
    except KeyboardInterrupt:
        print("\n\nFAME: Goodbye! Have a great day!")
        break
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please try again or type 'exit' to quit.\n")

