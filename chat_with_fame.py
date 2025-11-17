#!/usr/bin/env python3
"""
FAME Assistant - Interactive Chat Interface
Chat with FAME like Siri/Alexa
"""

from core.assistant.assistant_api import handle_text_input
import sys

print("=" * 70)
print("FAME ASSISTANT - INTERACTIVE CHAT")
print("=" * 70)
print("\nWelcome! I'm FAME Assistant. I can help you with:")
print("  • Stock prices (e.g., 'what is the price of AAPL?')")
print("  • Date and time queries")
print("  • General questions")
print("\nType 'exit' or 'quit' to end the conversation")
print("=" * 70)
print()

# Create a session for this conversation
session_id = None
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
        
        # Process the input
        turn_count += 1
        result = handle_text_input(user_input, session_id=session_id)
        
        # Get session ID from first response
        if not session_id:
            session_id = result.get('session')
        
        # Display FAME's response
        reply = result.get('reply', 'I did not understand that.')
        intent = result.get('intent', 'unknown')
        confidence = result.get('confidence', 0.0)
        
        print(f"\nFAME: {reply}")
        
        # Show debug info (intent and confidence) for first few turns
        if turn_count <= 3:
            print(f"      [Intent: {intent}, Confidence: {confidence:.2f}]")
        
        print()  # Blank line for readability
        
    except KeyboardInterrupt:
        print("\n\nFAME: Goodbye! Have a great day!")
        break
    except Exception as e:
        print(f"\nFAME: I encountered an error: {e}")
        print("Please try again or type 'exit' to quit.\n")

