#!/usr/bin/env python3
"""Test technical query routing"""

from fame_unified import get_fame

fame = get_fame()

test_queries = [
    'can you build an .exe file from your code?',
    'can you compile your code into a program?',
    'what information does your core logic tell me about penetration?',
    'can you write code?',  # Should still be self-referential
]

print("=" * 80)
print("Testing Technical Query Routing")
print("=" * 80)
print()

for query in test_queries:
    print(f"Q: {query}")
    response = fame.process_text(query)
    answer = response.get('response', 'No response')
    print(f"A: {answer[:300]}...")
    print(f"Intent: {response.get('intent', 'N/A')}")
    print(f"Confidence: {response.get('confidence', 'N/A')}")
    print()
    print("-" * 80)
    print()

