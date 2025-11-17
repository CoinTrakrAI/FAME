# FAME Knowledge Base - Usage Guide

## What It Does

FAME can now learn from books and use that knowledge to:
1. **Answer questions** - FAME searches the knowledge base when answering technical questions
2. **Generate code** - FAME uses Python code examples and concepts from books when coding
3. **Provide expertise** - FAME draws on cybersecurity, networking, AWS, and other technical knowledge

## Current Status

✅ **16 books processed** and stored in knowledge base
✅ **29 technical concepts** indexed
✅ **70+ code examples** extracted (Python, security, networking)

## Books Already Processed

- CISSP Study Guide
- Android Hackers Handbook
- Network Protocol Attacks
- AWS SysOps Guide
- Ethical Hacking with Python
- Black Hat Python
- Red Team Field Manual
- CCNA Routing & Switching
- And more...

## How to Process More Books

Run this command to process one book at a time (incremental):
```bash
python process_books_simple.py
```

Each run processes one new book. Run it multiple times to process all 48 books.

## How FAME Uses the Knowledge

1. **When you ask a question**: FAME automatically searches the knowledge base
2. **When generating code**: FAME uses Python examples from books
3. **Technical questions**: FAME references relevant book content

## Example Usage

Just ask FAME questions normally - the knowledge base is integrated automatically!

- "How do I write a Python script to scan ports?"
- "Explain SQL injection attacks"
- "What are best practices for network security?"

FAME will search the knowledge base and use relevant book content in responses.

## Knowledge Base Location

- Storage: `knowledge_base/` folder
- Books index: `knowledge_base/books_index.json`
- Knowledge index: `knowledge_base/knowledge_index.json`
- Book content: `knowledge_base/book_*.txt`
- Code examples: `knowledge_base/book_*_code.json`

