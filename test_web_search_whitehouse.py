#!/usr/bin/env python3
"""
Test FAME Web Search for whitehouse.gov content
"""

from fame_web_search import FAMEWebSearcher

print("=" * 70)
print("TESTING FAME WEB SEARCH FOR WHITEHOUSE.GOV")
print("=" * 70)

# Create searcher
searcher = FAMEWebSearcher()

# Search for whitehouse.gov content
print("\nSearching: 'whitehouse.gov current president'")
print("-" * 70)

results = searcher.search("whitehouse.gov current president")

# Display results
print(f"\nResults Type: {type(results)}")

if isinstance(results, dict):
    print(f"\nResults Dictionary Keys: {list(results.keys())}")
    
    if 'results' in results:
        print(f"\nFound {len(results['results'])} results:")
        print("-" * 70)
        for i, item in enumerate(results['results'], 1):
            print(f"\nResult {i}:")
            print(f"  Title: {item.get('title', 'No title')}")
            print(f"  Snippet: {item.get('snippet', 'No snippet')[:150]}...")
            print(f"  Link: {item.get('link', 'No link')}")
            if 'whitehouse.gov' in item.get('link', '').lower():
                print(f"  [FOUND] whitehouse.gov link!")
            print(f"  Source: {item.get('source', 'Unknown')}")
    
    if 'summary' in results:
        print(f"\nSummary: {results['summary']}")
    
    print(f"\nFull Results Structure:")
    print(f"  {results}")

elif isinstance(results, list):
    print(f"\nFound {len(results)} results:")
    print("-" * 70)
    for i, item in enumerate(results, 1):
        print(f"\nResult {i}:")
        if isinstance(item, dict):
            print(f"  Title: {item.get('title', 'No title')}")
            print(f"  Snippet: {item.get('snippet', 'No snippet')[:150]}...")
            print(f"  Link: {item.get('link', 'No link')}")
            if 'whitehouse.gov' in str(item.get('link', '')).lower():
                print(f"  [FOUND] whitehouse.gov link!")
        else:
            print(f"  {item}")
else:
    print(f"\nResults: {results}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)

