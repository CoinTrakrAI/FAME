#!/usr/bin/env python3
"""
FAME Knowledge Integration - Integrates book knowledge into responses
"""

from typing import Dict, Any, Optional, List
import re

try:
    from core.knowledge_base import search_knowledge_base, get_book_content, extract_code_examples
    KNOWLEDGE_BASE_AVAILABLE = True
except ImportError:
    KNOWLEDGE_BASE_AVAILABLE = False


def get_relevant_knowledge(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """Get relevant knowledge from books for a query"""
    if not KNOWLEDGE_BASE_AVAILABLE:
        return []
    
    try:
        kb_results = search_knowledge_base(query, max_results=max_results)
        knowledge_list = []
        
        for result in kb_results:
            book_content = get_book_content(result["book_id"])
            if book_content:
                # Find relevant snippet containing query terms
                query_terms = query.lower().split()
                content_lower = book_content.lower()
                
                # Find position of first query term
                best_pos = -1
                for term in query_terms:
                    pos = content_lower.find(term)
                    if pos != -1 and (best_pos == -1 or pos < best_pos):
                        best_pos = pos
                
                if best_pos != -1:
                    # Extract 1000 chars around the match
                    start = max(0, best_pos - 500)
                    end = min(len(book_content), best_pos + 500)
                    snippet = book_content[start:end]
                else:
                    snippet = book_content[:1000]
                
                knowledge_list.append({
                    "book_title": result["title"],
                    "concept": result["concept"],
                    "snippet": snippet,
                    "full_content_available": len(book_content) > 1000
                })
        
        return knowledge_list
    except Exception as e:
        return []


def get_python_code_examples(topic: str, max_examples: int = 3) -> List[str]:
    """Get Python code examples from books related to a topic"""
    if not KNOWLEDGE_BASE_AVAILABLE:
        return []
    
    try:
        kb_results = search_knowledge_base(topic, max_results=5)
        code_examples = []
        
        for result in kb_results:
            book_content = get_book_content(result["book_id"])
            if book_content:
                examples = extract_code_examples(book_content)
                # Filter for Python examples
                python_examples = [
                    ex for ex in examples 
                    if any(keyword in ex.lower() for keyword in ['import ', 'def ', 'class ', 'print(', 'if __name__'])
                ]
                code_examples.extend(python_examples[:max_examples])
        
        return code_examples[:max_examples]
    except Exception as e:
        return []


def enhance_response_with_knowledge(response: str, query: str) -> str:
    """Enhance a response with relevant knowledge from books"""
    if not KNOWLEDGE_BASE_AVAILABLE:
        return response
    
    knowledge = get_relevant_knowledge(query, max_results=2)
    
    if not knowledge:
        return response
    
    enhancement = "\n\n**📚 RELEVANT KNOWLEDGE FROM BOOKS:**\n\n"
    for i, kb_item in enumerate(knowledge, 1):
        enhancement += f"**From: {kb_item['book_title']}**\n"
        enhancement += f"{kb_item['snippet'][:500]}...\n\n"
    
    return response + enhancement


def get_knowledge_for_code_generation(task_description: str) -> Dict[str, Any]:
    """
    Get relevant knowledge and code examples for code generation tasks
    
    Returns:
        Dict with 'code_examples', 'concepts', 'book_references'
    """
    if not KNOWLEDGE_BASE_AVAILABLE:
        return {"code_examples": [], "concepts": [], "book_references": []}
    
    # Extract key terms from task description
    python_keywords = ['python', 'function', 'class', 'script', 'program', 'code']
    security_keywords = ['hack', 'security', 'penetration', 'exploit', 'vulnerability']
    network_keywords = ['network', 'socket', 'tcp', 'udp', 'http', 'api']
    
    topic = task_description.lower()
    
    # Determine primary topic
    if any(kw in topic for kw in python_keywords):
        code_examples = get_python_code_examples(topic, max_examples=5)
    elif any(kw in topic for kw in security_keywords):
        code_examples = get_python_code_examples("python security hacking", max_examples=5)
    elif any(kw in topic for kw in network_keywords):
        code_examples = get_python_code_examples("python network", max_examples=5)
    else:
        code_examples = get_python_code_examples("python", max_examples=3)
    
    # Get relevant knowledge
    knowledge = get_relevant_knowledge(task_description, max_results=3)
    
    return {
        "code_examples": code_examples,
        "concepts": [k["concept"] for k in knowledge],
        "book_references": [k["book_title"] for k in knowledge]
    }


if __name__ == "__main__":
    # Test
    if KNOWLEDGE_BASE_AVAILABLE:
        print("Knowledge base available")
        test_query = "python hacking"
        results = get_relevant_knowledge(test_query)
        print(f"Found {len(results)} relevant knowledge items")
    else:
        print("Knowledge base not available")

