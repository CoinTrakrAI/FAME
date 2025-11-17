#!/usr/bin/env python3
"""Test confidence and sources display"""

from fame_unified import get_fame

fame = get_fame()

test_queries = [
    'what is Python?',
    'whats the difference between https and smtp?',
    'hello'
]

print("=" * 80)
print("Testing Confidence and Sources Display")
print("=" * 80)
print()

for query in test_queries:
    print(f"Q: {query}")
    response = fame.process_text(query)
    
    # Response
    answer = response.get('response', 'No response')
    print(f"A: {answer[:200]}...")
    
    # Metadata
    print("\nMETADATA:")
    print(f"  Confidence: {response.get('confidence', 'N/A')}")
    if 'confidence' in response:
        conf = response['confidence']
        print(f"  Confidence: {conf*100:.1f}%")
    
    print(f"  Sources: {response.get('sources', [])}")
    print(f"  Intent: {response.get('intent', 'N/A')}")
    print(f"  Processing Time: {response.get('processing_time', 'N/A')}s")
    
    print()
    print("-" * 80)
    print()

