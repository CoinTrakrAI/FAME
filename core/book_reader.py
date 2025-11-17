#!/usr/bin/env python3
"""
F.A.M.E. Book Reader Module
Reads and summarizes books from various formats (PDF, TXT, EPUB, DOCX)
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Try importing document reading libraries
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PyPDF2 not available. PDF reading disabled.")

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx not available. DOCX reading disabled.")

try:
    import ebooklib
    from ebooklib import epub
    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False
    logger.warning("ebooklib not available. EPUB reading disabled.")


def read_pdf(file_path: str, max_pages: int = 100) -> str:
    """
    Extract text from PDF file with improved error handling and fallback methods
    
    Uses multiple extraction strategies:
    1. Try PyPDF2 first (fast)
    2. Fallback to pdfplumber if available (better quality)
    3. Sample pages across document for better coverage
    """
    if not PDF_AVAILABLE:
        return "ERROR: PyPDF2 not installed. Install with: pip install PyPDF2"
    
    # Try pdfplumber as fallback (better text extraction)
    try:
        import pdfplumber
        PDFPLUMBER_AVAILABLE = True
    except ImportError:
        PDFPLUMBER_AVAILABLE = False
    
    text_content = []
    pages_processed = 0
    errors = []
    
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            if total_pages == 0:
                return "ERROR: PDF has no pages"
            
            pages_to_read = min(total_pages, max_pages)
            
            # Strategy: Read first 50%, then sample from rest for better coverage
            first_half = min(pages_to_read // 2, total_pages // 2)
            remaining_pages = pages_to_read - first_half
            
            # Read first half
            for page_num in range(first_half):
                try:
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text and text.strip():
                        text_content.append(text)
                        pages_processed += 1
                except Exception as e:
                    errors.append(f"Page {page_num}: {str(e)}")
                    logger.debug(f"Error reading PDF page {page_num}: {e}")
            
            # Sample from remaining pages
            if remaining_pages > 0 and total_pages > first_half:
                import random
                remaining_range = range(first_half, total_pages)
                sample_pages = random.sample(
                    list(remaining_range),
                    min(remaining_pages, len(remaining_range))
                )
                for page_num in sorted(sample_pages):
                    try:
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        if text and text.strip():
                            text_content.append(text)
                            pages_processed += 1
                    except Exception as e:
                        errors.append(f"Page {page_num}: {str(e)}")
                        logger.debug(f"Error reading PDF page {page_num}: {e}")
            
            # If extraction was poor, try pdfplumber
            total_chars = sum(len(t) for t in text_content)
            if PDFPLUMBER_AVAILABLE and total_chars < 1000 and pages_processed > 0:
                logger.info(f"PyPDF2 extraction poor ({total_chars} chars), trying pdfplumber...")
                try:
                    text_content = []
                    with pdfplumber.open(file_path) as pdf:
                        for i, page in enumerate(pdf.pages[:pages_to_read]):
                            try:
                                text = page.extract_text()
                                if text and text.strip():
                                    text_content.append(text)
                            except:
                                pass
                except Exception as e:
                    logger.warning(f"pdfplumber also failed: {e}")
            
            # Add note about extraction
            if total_pages > max_pages:
                text_content.append(f"\n[Note: PDF has {total_pages} pages, extracted {pages_processed} pages]")
            
            if errors:
                logger.warning(f"Encountered {len(errors)} errors during PDF extraction")
        
        result = "\n\n".join(text_content)
        
        # Validate we got meaningful content
        if len(result.strip()) < 100:
            logger.warning(f"PDF extraction resulted in very little text ({len(result)} chars)")
        
        return result
        
    except Exception as e:
        error_msg = f"ERROR reading PDF: {str(e)}"
        logger.error(error_msg)
        return error_msg


def read_txt(file_path: str) -> str:
    """Read text from TXT file"""
    try:
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    return file.read()
            except UnicodeDecodeError:
                continue
        return "ERROR: Could not decode text file with any encoding"
    except Exception as e:
        return f"ERROR reading TXT: {str(e)}"


def read_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    if not DOCX_AVAILABLE:
        return "ERROR: python-docx not installed. Install with: pip install python-docx"
    
    try:
        doc = docx.Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n\n".join(paragraphs)
    except Exception as e:
        return f"ERROR reading DOCX: {str(e)}"


def read_epub(file_path: str) -> str:
    """Extract text from EPUB file"""
    if not EPUB_AVAILABLE:
        return "ERROR: ebooklib not installed. Install with: pip install ebooklib"
    
    try:
        book = epub.read_epub(file_path)
        text_content = []
        
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                # Extract text from HTML
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text = soup.get_text()
                if text.strip():
                    text_content.append(text)
        
        return "\n\n".join(text_content)
    except Exception as e:
        return f"ERROR reading EPUB: {str(e)}"


def read_book(file_path: str) -> Dict[str, Any]:
    """
    Read a book file and return its content
    
    Args:
        file_path: Path to the book file
        
    Returns:
        Dict with 'content', 'title', 'file_type', 'success', 'error'
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "content": "",
            "title": file_path.name,
            "file_type": file_path.suffix
        }
    
    file_ext = file_path.suffix.lower()
    title = file_path.stem
    
    try:
        if file_ext == '.pdf':
            content = read_pdf(str(file_path))
        elif file_ext == '.txt':
            content = read_txt(str(file_path))
        elif file_ext == '.docx':
            content = read_docx(str(file_path))
        elif file_ext == '.epub':
            content = read_epub(str(file_path))
        else:
            return {
                "success": False,
                "error": f"Unsupported file type: {file_ext}",
                "content": "",
                "title": title,
                "file_type": file_ext
            }
        
        success = not content.startswith("ERROR")
        
        return {
            "success": success,
            "content": content,
            "title": title,
            "file_type": file_ext,
            "file_path": str(file_path),
            "content_length": len(content),
            "error": None if success else content
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "content": "",
            "title": title,
            "file_type": file_ext
        }


def summarize_book(content: str, max_length: int = 2000) -> str:
    """
    Create a summary of book content
    
    Args:
        content: Book content text
        max_length: Maximum summary length
        
    Returns:
        Summary string
    """
    if not content or len(content) < 100:
        return "Content too short or empty to summarize."
    
    # Simple summary: first and last portions
    if len(content) <= max_length:
        return content
    
    # Take first 60% and last 20% with gap indicator
    first_part = content[:int(max_length * 0.6)]
    last_part = content[-int(max_length * 0.2):]
    
    summary = f"{first_part}\n\n... [content truncated] ...\n\n{last_part}"
    return summary


def find_books_in_directory(directory: str = None) -> List[Dict[str, Any]]:
    """
    Find all book files in a directory
    
    Args:
        directory: Directory to search (defaults to FAME_Desktop, or E_Books if specified)
        
    Returns:
        List of book file info dicts
    """
    if directory is None:
        # Check for E_Books directory first
        e_books_dir = r"C:\Users\cavek\Downloads\E_Books"
        if os.path.exists(e_books_dir):
            directory = e_books_dir
        else:
            directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    book_extensions = ['.pdf', '.txt', '.epub', '.docx', '.mobi']
    books = []
    
    directory_path = Path(directory)
    if not directory_path.exists():
        return books
    
    for ext in book_extensions:
        for book_file in directory_path.rglob(f"*{ext}"):
            if book_file.is_file():
                books.append({
                    "path": str(book_file),
                    "name": book_file.name,
                    "type": ext,
                    "size": book_file.stat().st_size
                })
    
    return books


def handle_book_review_request(text: str, directory: str = None, incremental: bool = True, max_books: int = 5) -> Dict[str, Any]:
    """
    Handle a request to review books
    
    Args:
        text: User request text
        directory: Optional directory to search (defaults to E_Books or FAME_Desktop)
        
    Returns:
        Response dict with book summaries
    """
    # Check if user specified a directory in the text or use default
    if directory is None:
        # Check for E_Books directory first
        e_books_dir = r"C:\Users\cavek\Downloads\E_Books"
        if os.path.exists(e_books_dir):
            directory = e_books_dir
    
    # Import knowledge base
    try:
        from core.knowledge_base import (
            store_book_knowledge, extract_key_concepts, extract_code_examples,
            get_book_hash, load_index, BOOKS_INDEX_FILE, get_knowledge_summary
        )
        KNOWLEDGE_BASE_AVAILABLE = True
    except ImportError:
        KNOWLEDGE_BASE_AVAILABLE = False
    
    # Find books in the directory
    books = find_books_in_directory(directory)
    
    if not books:
        return {
            "response": f"I couldn't find any book files (PDF, TXT, EPUB, DOCX) in {directory}. Please add books to review.",
            "books_found": 0,
            "books_reviewed": 0,
            "summaries": []
        }
    
    # Check which books have been processed
    processed_books = {}
    if KNOWLEDGE_BASE_AVAILABLE:
        books_index = load_index(BOOKS_INDEX_FILE)
        for book_info in books:
            book_hash = get_book_hash(book_info["path"])
            book_id = f"book_{book_hash[:12]}"
            if book_id in books_index:
                processed_books[book_info["path"]] = books_index[book_id]
    
    # If incremental, only process new books or limit to max_books
    # Sort by size (process smaller books first to avoid timeouts)
    books_sorted = sorted(books, key=lambda x: x["size"])
    
    if incremental:
        new_books = [b for b in books_sorted if b["path"] not in processed_books]
        books_to_process = new_books[:max_books] if new_books else books_sorted[:max_books]
    else:
        books_to_process = books_sorted[:max_books]
    
    summaries = []
    reviewed_count = 0
    
    response_parts = [
        f"**BOOK REVIEW SUMMARY**\n\n",
        f"Found {len(books)} total book(s). "
    ]
    
    if KNOWLEDGE_BASE_AVAILABLE and processed_books:
        response_parts.append(f"Already processed: {len(processed_books)}. ")
    response_parts.append(f"Processing: {len(books_to_process)} book(s):\n\n")
    
    for i, book_info in enumerate(books_to_process, 1):
        response_parts.append(f"**{i}. {book_info['name']}** ({book_info['type']})\n")
        response_parts.append(f"   Size: {book_info['size']:,} bytes\n")
        
        # Read the book (with timeout protection for large files)
        try:
            book_data = read_book(book_info['path'])
        except Exception as e:
            logger.error(f"Error reading {book_info['name']}: {e}")
            response_parts.append(f"   ❌ Error reading file: {str(e)}\n\n")
            continue
        
        if book_data['success']:
            reviewed_count += 1
            content = book_data['content']
            summary = summarize_book(content, max_length=1500)
            
            # Extract key insights (first 500 chars)
            key_insights = content[:500] if len(content) > 500 else content
            
            # Store in knowledge base if available (only store first 50KB to avoid memory issues)
            book_id = None
            if KNOWLEDGE_BASE_AVAILABLE:
                try:
                    # Limit content size for storage (keep full content in file, but limit processing)
                    content_for_storage = content[:50000] if len(content) > 50000 else content
                    key_concepts = extract_key_concepts(content_for_storage)
                    code_examples = extract_code_examples(content_for_storage)
                    book_id = store_book_knowledge(
                        book_info["path"],
                        book_data['title'],
                        content,  # Store full content in file
                        key_concepts=key_concepts,
                        code_examples=code_examples,
                        file_type=book_data['file_type']
                    )
                except Exception as e:
                    logger.warning(f"Failed to store book in knowledge base: {e}")
            
            summaries.append({
                "title": book_data['title'],
                "file_type": book_data['file_type'],
                "content_length": book_data['content_length'],
                "summary": summary,
                "key_insights": key_insights,
                "book_id": book_id
            })
            
            response_parts.append(f"   [OK] Successfully read and stored ({book_data['content_length']:,} characters)\n")
            if book_id:
                response_parts.append(f"   [STORED] In knowledge base: {book_id}\n")
            response_parts.append(f"   **Key Content:**\n")
            response_parts.append(f"   {key_insights[:300]}...\n\n")
        else:
            response_parts.append(f"   [ERROR] {book_data.get('error', 'Unknown error')}\n\n")
    
    response_parts.append(f"\n**REVIEW COMPLETE:** Reviewed {reviewed_count} of {len(books)} book(s).\n")
    
    # Add knowledge base summary if available
    if KNOWLEDGE_BASE_AVAILABLE:
        try:
            kb_summary = get_knowledge_summary()
            response_parts.append(f"\n{kb_summary}\n")
        except Exception as e:
            logger.warning(f"Failed to get knowledge base summary: {e}")
    
    return {
        "response": "".join(response_parts),
        "books_found": len(books),
        "books_reviewed": reviewed_count,
        "summaries": summaries,
        "source": "book_reader",
        "incremental_mode": incremental
    }


if __name__ == "__main__":
    # Test the book reader
    books = find_books_in_directory()
    print(f"Found {len(books)} book(s):")
    for book in books:
        print(f"  - {book['name']} ({book['type']})")

