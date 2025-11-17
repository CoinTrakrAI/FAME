#!/usr/bin/env python3
"""Quick test to verify knowledge base is working"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from core.knowledge_base import get_knowledge_summary, search_knowledge_base
    from core.knowledge_integration import get_relevant_knowledge, get_python_code_examples
    
    print("[OK] Knowledge base modules loaded successfully")
    
    # Test summary
    summary = get_knowledge_summary()
    print(f"\n{summary}")
    
    # Test search
    test_query = "python"
    results = search_knowledge_base(test_query, max_results=3)
    print(f"\n[SEARCH] Search for '{test_query}': Found {len(results)} results")
    for result in results:
        print(f"   - {result['title']} (concept: {result['concept']})")
    
    print("\n[OK] Knowledge base is working!")
    
except Exception as e:
    print(f"[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()

