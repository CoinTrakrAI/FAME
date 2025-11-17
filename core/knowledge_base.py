#!/usr/bin/env python3
"""
FAME Knowledge Base - Stores and retrieves knowledge from books and documents
"""

import json
import os
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

KNOWLEDGE_BASE_DIR = Path(__file__).parent.parent / "knowledge_base"
KNOWLEDGE_BASE_DIR.mkdir(exist_ok=True)

BOOKS_INDEX_FILE = KNOWLEDGE_BASE_DIR / "books_index.json"
KNOWLEDGE_INDEX_FILE = KNOWLEDGE_BASE_DIR / "knowledge_index.json"


def get_book_hash(file_path: str) -> str:
    """Generate hash for a book file to track if it's been processed"""
    file_stat = os.stat(file_path)
    # Use file path, size, and modification time as hash
    hash_input = f"{file_path}:{file_stat.st_size}:{file_stat.st_mtime}"
    return hashlib.md5(hash_input.encode()).hexdigest()


def load_index(filename: Path) -> Dict[str, Any]:
    """Load index file"""
    if filename.exists():
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_index(filename: Path, data: Dict[str, Any]):
    """Save index file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def store_book_knowledge(book_path: str, title: str, content: str, 
                         key_concepts: List[str] = None, 
                         code_examples: List[str] = None,
                         file_type: str = "pdf") -> str:
    """
    Store knowledge from a book
    
    Returns:
        book_id: Unique identifier for this book
    """
    book_hash = get_book_hash(book_path)
    book_id = f"book_{book_hash[:12]}"
    
    # Load existing index
    books_index = load_index(BOOKS_INDEX_FILE)
    
    # Check if already processed
    if book_id in books_index:
        return book_id
    
    # Store book metadata
    books_index[book_id] = {
        "title": title,
        "path": book_path,
        "file_type": file_type,
        "processed_date": datetime.now().isoformat(),
        "content_length": len(content),
        "key_concepts": key_concepts or [],
        "code_examples_count": len(code_examples) if code_examples else 0
    }
    
    # Store full content (chunked for large files)
    book_content_file = KNOWLEDGE_BASE_DIR / f"{book_id}_content.txt"
    with open(book_content_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Store code examples separately
    if code_examples:
        code_file = KNOWLEDGE_BASE_DIR / f"{book_id}_code.json"
        with open(code_file, 'w', encoding='utf-8') as f:
            json.dump({"examples": code_examples}, f, indent=2)
    
    # Update knowledge index with key concepts
    knowledge_index = load_index(KNOWLEDGE_INDEX_FILE)
    for concept in (key_concepts or []):
        if concept not in knowledge_index:
            knowledge_index[concept] = []
        knowledge_index[concept].append({
            "book_id": book_id,
            "title": title,
            "relevance": "high"
        })
    
    # Save indices
    save_index(BOOKS_INDEX_FILE, books_index)
    save_index(KNOWLEDGE_INDEX_FILE, knowledge_index)
    
    return book_id


def extract_key_concepts(content: str, max_concepts: int = 20) -> List[str]:
    """
    Extract key technical concepts from content with improved algorithm
    
    Uses multiple strategies:
    1. Keyword frequency analysis
    2. Context-aware extraction
    3. Technical term detection
    4. Minimum threshold to ensure quality
    """
    if not content or len(content.strip()) < 100:
        return []
    
    # Expanded keyword list with categories
    tech_keywords = [
        # Programming languages
        'python', 'javascript', 'java', 'c++', 'c#', 'go', 'rust', 'ruby', 'php', 'swift',
        # Security & hacking
        'hacking', 'security', 'penetration', 'kali', 'metasploit', 'wireshark',
        'encryption', 'authentication', 'firewall', 'vulnerability', 'exploit', 'payload',
        'sql injection', 'xss', 'csrf', 'buffer overflow', 'privilege escalation',
        # Networking & infrastructure
        'network', 'tcp/ip', 'dns', 'http', 'https', 'ssl', 'tls', 'vpn', 'proxy',
        'aws', 'azure', 'gcp', 'cloud', 'docker', 'kubernetes', 'container',
        # Operating systems
        'linux', 'windows', 'unix', 'macos', 'android', 'ios',
        # Databases
        'database', 'sql', 'mysql', 'postgresql', 'mongodb', 'redis',
        # Web technologies
        'api', 'rest', 'graphql', 'web', 'html', 'css', 'react', 'vue', 'angular',
        'node.js', 'express', 'django', 'flask', 'framework',
        # General technical
        'algorithm', 'data structure', 'machine learning', 'ai', 'artificial intelligence',
        'blockchain', 'cryptocurrency', 'devops', 'ci/cd', 'testing', 'debugging'
    ]
    
    content_lower = content.lower()
    found_concepts = []
    
    # Strategy 1: Direct keyword matching with frequency
    for keyword in tech_keywords:
        count = content_lower.count(keyword)
        if count > 0:
            # Weight by frequency (log scale to prevent single terms from dominating)
            import math
            weight = math.log(count + 1) * count
            found_concepts.append((keyword, weight, count))
    
    # Strategy 2: Look for technical patterns (capitalized terms, acronyms)
    import re
    # Find capitalized technical terms (likely important concepts)
    capitalized_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
    # Find acronyms (2-5 uppercase letters)
    acronyms = re.findall(r'\b[A-Z]{2,5}\b', content)
    
    # Common acronyms to filter
    common_words = {'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW', 'MAN', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WAY', 'WHO', 'ITS', 'LET', 'PUT', 'SAY', 'SHE', 'TOO', 'USE', 'WHAT', 'WHEN', 'WHY', 'WITH'}
    
    for term in capitalized_terms:
        term_lower = term.lower()
        if term_lower not in [c[0] for c in found_concepts] and len(term) > 3:
            count = content_lower.count(term_lower)
            if count >= 2:  # Must appear at least twice
                found_concepts.append((term_lower, count * 2, count))  # Higher weight for proper nouns
    
    for acronym in acronyms:
        if acronym not in common_words and len(acronym) >= 2:
            count = content_lower.count(acronym.lower())
            if count >= 2:
                found_concepts.append((acronym.lower(), count * 3, count))  # Even higher weight for acronyms
    
    # Strategy 3: Remove duplicates and sort by weight
    concept_dict = {}
    for concept, weight, count in found_concepts:
        if concept not in concept_dict or concept_dict[concept][1] < weight:
            concept_dict[concept] = (concept, weight, count)
    
    # Sort by weight and return top concepts
    sorted_concepts = sorted(concept_dict.values(), key=lambda x: x[1], reverse=True)
    
    # Apply minimum threshold (concept must appear at least 2 times or have high weight)
    filtered_concepts = [
        concept for concept, weight, count in sorted_concepts
        if count >= 2 or weight >= 5.0
    ]
    
    # Ensure we return at least some concepts if content is substantial
    if len(filtered_concepts) == 0 and len(content) > 1000:
        # Fallback: return top concepts even if below threshold
        filtered_concepts = [concept for concept, _, _ in sorted_concepts[:max_concepts]]
    
    return filtered_concepts[:max_concepts]


def extract_code_examples(content: str) -> List[str]:
    """Extract code examples from content"""
    import re
    
    # Look for code blocks (Python, JavaScript, etc.)
    code_patterns = [
        r'```python\s*\n(.*?)```',
        r'```python3\s*\n(.*?)```',
        r'```py\s*\n(.*?)```',
        r'```javascript\s*\n(.*?)```',
        r'```js\s*\n(.*?)```',
        r'```bash\s*\n(.*?)```',
        r'```sh\s*\n(.*?)```',
    ]
    
    code_examples = []
    for pattern in code_patterns:
        matches = re.findall(pattern, content, re.DOTALL)
        code_examples.extend(matches)
    
    # Also look for indented code blocks (common in PDFs)
    lines = content.split('\n')
    current_block = []
    for line in lines:
        if line.strip().startswith(('def ', 'class ', 'import ', 'from ', '$', 'sudo', 'pip', 'npm')):
            current_block.append(line)
        elif current_block and (line.strip() == '' or line.startswith('    ') or line.startswith('\t')):
            current_block.append(line)
        else:
            if len(current_block) > 3:  # Only save meaningful code blocks
                code_examples.append('\n'.join(current_block))
            current_block = []
    
    return code_examples[:50]  # Limit to 50 examples per book


def search_knowledge_base(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Search knowledge base for relevant information"""
    query_lower = query.lower()
    
    # Load indices
    books_index = load_index(BOOKS_INDEX_FILE)
    knowledge_index = load_index(KNOWLEDGE_INDEX_FILE)
    
    results = []
    
    # Search by concept
    for concept, book_refs in knowledge_index.items():
        if concept in query_lower:
            for book_ref in book_refs:
                book_id = book_ref["book_id"]
                if book_id in books_index:
                    results.append({
                        "book_id": book_id,
                        "title": book_ref["title"],
                        "concept": concept,
                        "relevance": "high"
                    })
    
    # Search by book title
    for book_id, book_info in books_index.items():
        title_lower = book_info["title"].lower()
        if any(word in title_lower for word in query_lower.split() if len(word) > 3):
            results.append({
                "book_id": book_id,
                "title": book_info["title"],
                "concept": "title match",
                "relevance": "medium"
            })
    
    # Remove duplicates
    seen = set()
    unique_results = []
    for result in results:
        key = (result["book_id"], result["concept"])
        if key not in seen:
            seen.add(key)
            unique_results.append(result)
    
    return unique_results[:max_results]


def get_book_content(book_id: str) -> Optional[str]:
    """Retrieve full content of a book"""
    book_content_file = KNOWLEDGE_BASE_DIR / f"{book_id}_content.txt"
    if book_content_file.exists():
        with open(book_content_file, 'r', encoding='utf-8') as f:
            return f.read()
    return None


def get_knowledge_summary() -> str:
    """Get summary of all stored knowledge"""
    books_index = load_index(BOOKS_INDEX_FILE)
    knowledge_index = load_index(KNOWLEDGE_INDEX_FILE)
    
    summary_parts = [
        f"**KNOWLEDGE BASE SUMMARY**\n\n",
        f"**Books Processed**: {len(books_index)}\n\n"
    ]
    
    if books_index:
        summary_parts.append("**Books in Knowledge Base:**\n\n")
        for book_id, book_info in list(books_index.items())[:10]:
            summary_parts.append(f"- **{book_info['title']}**\n")
            summary_parts.append(f"  - Concepts: {len(book_info.get('key_concepts', []))}\n")
            summary_parts.append(f"  - Code Examples: {book_info.get('code_examples_count', 0)}\n\n")
        
        if len(books_index) > 10:
            summary_parts.append(f"... and {len(books_index) - 10} more books\n\n")
    
    summary_parts.append(f"**Total Concepts Indexed**: {len(knowledge_index)}\n")
    
    return "".join(summary_parts)


if __name__ == "__main__":
    # Test the knowledge base
    print("Knowledge Base Directory:", KNOWLEDGE_BASE_DIR)
    print("Books Index:", BOOKS_INDEX_FILE.exists())
    print("Knowledge Index:", KNOWLEDGE_INDEX_FILE.exists())

