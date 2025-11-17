#!/usr/bin/env python3
"""Test self-awareness functionality"""

from fame_unified import get_fame

fame = get_fame()

test_queries = [
    'can you write in code FAME?',
    'can you write code?',
    'do you code?',
    'can FAME write code?'
]

print("=" * 80)
print("Testing Self-Awareness")
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

