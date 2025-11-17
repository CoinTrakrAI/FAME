#!/usr/bin/env python3
"""
FAME Assistant - Interactive Demo
Shows how to start and use FAME Assistant
"""

from core.assistant.assistant_api import handle_text_input
import time

print("=" * 70)
print("HOW TO START FAME ASSISTANT")
print("=" * 70)
print("\nTo start FAME Assistant, run:")
print("  python chat_with_fame.py")
print("\nOr use it programmatically:")
print("  from core.assistant.assistant_api import handle_text_input")
print("  result = handle_text_input('your question here')")
print("\n" + "=" * 70)
print("\nDEMONSTRATING LIVE CONVERSATION:")
print("=" * 70)
print()

# Simulate a conversation
session_id = None

# Question 1
print("YOU: hi")
time.sleep(0.5)
result1 = handle_text_input("hi")
session_id = result1.get('session')
print(f"FAME: {result1.get('reply')}")
print(f"      [Intent: {result1.get('intent')}, Confidence: {result1.get('confidence', 0):.2f}]")
print()

# Question 2
print("YOU: my name is Karl")
time.sleep(0.5)
result2 = handle_text_input("my name is Karl", session_id=session_id)
print(f"FAME: {result2.get('reply')}")
print(f"      [Intent: {result2.get('intent')}, Confidence: {result2.get('confidence', 0):.2f}]")
print()

# Question 3
print("YOU: what is the price of AAPL?")
time.sleep(1)
result3 = handle_text_input("what is the price of AAPL?", session_id=session_id)
print(f"FAME: {result3.get('reply')}")
print(f"      [Intent: {result3.get('intent')}, Confidence: {result3.get('confidence', 0):.2f}]")
if result3.get('data'):
    print(f"      [Data: {result3.get('data')}]")
print()

# Question 4
print("YOU: whats todays date?")
time.sleep(0.5)
result4 = handle_text_input("whats todays date?", session_id=session_id)
print(f"FAME: {result4.get('reply')}")
print(f"      [Intent: {result4.get('intent')}, Confidence: {result4.get('confidence', 0):.2f}]")
print()

# Question 5
print("YOU: hello again")
time.sleep(0.5)
result5 = handle_text_input("hello again", session_id=session_id)
print(f"FAME: {result5.get('reply')}")
print(f"      [Intent: {result5.get('intent')}, Confidence: {result5.get('confidence', 0):.2f}]")
print(f"      (Notice: FAME remembers your name!)")
print()

print("=" * 70)
print("CONVERSATION COMPLETE!")
print("=" * 70)
print("\nTo start your own interactive session:")
print("  python chat_with_fame.py")
print("\nOr integrate it into your code:")
print("  from core.assistant.assistant_api import handle_text_input")
print("  result = handle_text_input('your question')")
print("=" * 70)

