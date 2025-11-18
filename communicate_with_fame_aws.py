#!/usr/bin/env python3
"""
Quick FAME AWS Communication Script
Simple way to talk to FAME on AWS EC2
"""

import requests
import json
import sys

FAME_API = "http://3.135.222.143:8080/query"

def chat_with_fame(message, session_id="default_session"):
    """Send a message to FAME on AWS and get response"""
    try:
        response = requests.post(
            FAME_API,
            json={
                "text": message,
                "session_id": session_id,
                "source": "python_client"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("response", "No response")
        else:
            return f"Error: Server returned {response.status_code}"
            
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to FAME on AWS. Is it running?"
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line mode
        message = " ".join(sys.argv[1:])
        print(f"YOU: {message}")
        print(f"FAME: {chat_with_fame(message)}")
    else:
        # Interactive mode
        print("FAME AWS Communication")
        print("=" * 50)
        print(f"Connected to: {FAME_API}\n")
        
        session_id = f"session_{int(__import__('time').time())}"
        
        while True:
            try:
                user_input = input("YOU: ").strip()
                if not user_input or user_input.lower() in ['exit', 'quit']:
                    break
                    
                print(f"FAME: {chat_with_fame(user_input, session_id)}")
                print()
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break

