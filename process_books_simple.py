#!/usr/bin/env python3
"""
Simple script to process books one at a time and store in knowledge base
Run this multiple times to process all books incrementally
"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from core.book_reader import find_books_in_directory, read_book
from core.knowledge_base import (
    store_book_knowledge, extract_key_concepts, extract_code_examples,
    get_book_hash, load_index, BOOKS_INDEX_FILE, get_knowledge_summary
)

def process_one_book():
    """Process one unprocessed book"""
    e_books_dir = r"C:\Users\cavek\Downloads\E_Books"
    
    if not Path(e_books_dir).exists():
        print(f"ERROR: Directory not found: {e_books_dir}")
        return
    
    # Find all books
    books = find_books_in_directory(e_books_dir)
    print(f"Found {len(books)} total books")
    
    # Check which are already processed (improved duplicate detection)
    books_index = load_index(BOOKS_INDEX_FILE)
    processed_hashes = set()
    processed_paths = {}  # Track by path for duplicate detection
    
    for book_id, book_info in books_index.items():
        if "path" in book_info:
            path = book_info["path"]
            book_hash = get_book_hash(path)
            processed_hashes.add(book_hash)
            # Also track by filename for duplicate detection
            filename = Path(path).name.lower()
            if filename not in processed_paths:
                processed_paths[filename] = []
            processed_paths[filename].append({
                "book_id": book_id,
                "path": path,
                "title": book_info.get("title", ""),
                "hash": book_hash
            })
    
    # Find first unprocessed book
    for book_info in books:
        book_path = book_info["path"]
        book_hash = get_book_hash(book_path)
        filename = Path(book_path).name.lower()
        
        # Check if already processed by hash
        if book_hash in processed_hashes:
            print(f"   [SKIP] Already processed (hash match): {book_info['name']}")
            continue
        
        # Check for potential duplicates by filename
        if filename in processed_paths:
            similar_books = processed_paths[filename]
            print(f"   [WARNING] Found {len(similar_books)} book(s) with similar filename:")
            for similar in similar_books:
                print(f"     - {similar['title']} ({similar['book_id']})")
            # Ask user or auto-skip (for now, skip)
            print(f"   [SKIP] Skipping potential duplicate: {book_info['name']}")
            continue
        
        # Process new book
        if True:
            print(f"\n[PROCESSING] {book_info['name']}")
            print(f"   Size: {book_info['size']:,} bytes")
            
            # Read book
            book_data = read_book(book_info["path"])
            
            if book_data['success']:
                content = book_data['content']
                print(f"   [OK] Read {len(content):,} characters")
                
                # Extract knowledge
                key_concepts = extract_key_concepts(content)
                code_examples = extract_code_examples(content)
                
                print(f"   [INFO] Extracted {len(key_concepts)} concepts, {len(code_examples)} code examples")
                
                # Store in knowledge base
                book_id = store_book_knowledge(
                    book_info["path"],
                    book_data['title'],
                    content,
                    key_concepts=key_concepts,
                    code_examples=code_examples,
                    file_type=book_data['file_type']
                )
                
                print(f"   [STORED] Knowledge base ID: {book_id}")
                print(f"\n[SUCCESS] Processed: {book_data['title']}")
                return True
            else:
                print(f"   [ERROR] {book_data.get('error', 'Unknown')}")
                return False
    
    print("\n[COMPLETE] All books have been processed!")
    print(f"\n{get_knowledge_summary()}")
    return False

if __name__ == "__main__":
    print("=" * 60)
    print("FAME Book Processor - Incremental Mode")
    print("=" * 60)
    process_one_book()

