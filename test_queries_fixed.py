#!/usr/bin/env python3
"""Test queries to verify FAME is working correctly"""

from fame_unified import get_fame

fame = get_fame()

test_queries = [
    'whats todays date?',
    'what is Python?',
    'what is the capital of France?',
    'whats my name?',
    'hello',
    'what is machine learning?'
]

print("=" * 60)
print("Testing FAME Query Handling")
print("=" * 60)
print()

for query in test_queries:
    print(f"Q: {query}")
    response = fame.process_text(query)
    answer = response.get('response', 'No response')
    print(f"A: {answer[:200]}...")
    print(f"   Source: {response.get('source', 'unknown')}")
    print(f"   Confidence: {response.get('confidence', 'N/A')}")
    print()

print("=" * 60)
print("All tests complete!")
print("=" * 60)

