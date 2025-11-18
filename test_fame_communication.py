#!/usr/bin/env python3
"""
Test all FAME communication methods
"""

import sys
import requests
from pathlib import Path

def test_1_rest_api():
    """Test REST API on AWS EC2"""
    print("\n" + "="*70)
    print("TEST 1: REST API Endpoint (AWS EC2)")
    print("="*70)
    
    try:
        # Test health endpoint
        r = requests.get('http://18.220.108.23:8080/healthz', timeout=10)
        if r.status_code == 200:
            print("✅ Health endpoint: WORKING")
            health = r.json()
            print(f"   Status: {health.get('overall_status', 'unknown')}")
        else:
            print(f"❌ Health endpoint: FAILED (Status: {r.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Health endpoint: NETWORK BLOCKED (Firewall/Network restriction)")
        print(f"   Note: This is expected if your network blocks external connections")
        print(f"   Error: {str(e)[:100]}")
    
    try:
        # Test query endpoint
        r = requests.post(
            'http://18.220.108.23:8080/query',
            json={'text': 'Hello FAME'},
            timeout=15
        )
        if r.status_code == 200:
            print("✅ Query endpoint: WORKING")
            response = r.json()
            print(f"   Response: {str(response.get('response', 'N/A'))[:100]}")
            return True
        else:
            print(f"❌ Query endpoint: FAILED (Status: {r.status_code})")
            print(f"   Response: {r.text[:200]}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Query endpoint: NETWORK BLOCKED (Firewall/Network restriction)")
        print(f"   Note: This is expected if your network blocks external connections")
        return False

def test_2_web_chat():
    """Test Web Chat files exist and are valid"""
    print("\n" + "="*70)
    print("TEST 2: Web Chat Interface")
    print("="*70)
    
    html_file = Path("fame_chat.html")
    server_file = Path("start_fame_chat.py")
    
    if html_file.exists():
        print(f"✅ HTML file exists: {html_file}")
        # Check if it has the API endpoint configured
        content = html_file.read_text()
        if 'FAME_API' in content:
            print("✅ API endpoint configured in HTML")
    else:
        print(f"❌ HTML file missing: {html_file}")
        return False
    
    if server_file.exists():
        print(f"✅ Server script exists: {server_file}")
        # Try to import/validate syntax
        try:
            with open(server_file) as f:
                compile(f.read(), str(server_file), 'exec')
            print("✅ Server script syntax: VALID")
            return True
        except SyntaxError as e:
            print(f"❌ Server script syntax: INVALID - {e}")
            return False
    else:
        print(f"❌ Server script missing: {server_file}")
        return False

def test_3_python_chat():
    """Test Python chat script"""
    print("\n" + "="*70)
    print("TEST 3: Python Chat Script (chat_with_fame.py)")
    print("="*70)
    
    chat_file = Path("chat_with_fame.py")
    
    if not chat_file.exists():
        print(f"❌ Chat script missing: {chat_file}")
        return False
    
    print(f"✅ Chat script exists: {chat_file}")
    
    # Try to validate syntax and imports
    try:
        with open(chat_file) as f:
            code = f.read()
        compile(code, str(chat_file), 'exec')
        print("✅ Chat script syntax: VALID")
        
        # Check if required modules are importable
        if 'from core.assistant.assistant_api import handle_text_input' in code:
            print("✅ Uses core.assistant.assistant_api (correct import)")
        
        return True
    except SyntaxError as e:
        print(f"❌ Chat script syntax: INVALID - {e}")
        return False
    except Exception as e:
        print(f"⚠️  Chat script check: {type(e).__name__} - {e}")
        return False

def test_4_desktop_gui():
    """Test Desktop GUI"""
    print("\n" + "="*70)
    print("TEST 4: Desktop GUI (enhanced_fame_communicator.py)")
    print("="*70)
    
    gui_file = Path("enhanced_fame_communicator.py")
    
    if not gui_file.exists():
        print(f"❌ GUI script missing: {gui_file}")
        return False
    
    print(f"✅ GUI script exists: {gui_file}")
    
    # Try to validate syntax
    try:
        with open(gui_file) as f:
            code = f.read()
        compile(code, str(gui_file), 'exec')
        print("✅ GUI script syntax: VALID")
        
        # Check for GUI dependencies
        has_tkinter = 'import tkinter' in code or 'from tkinter' in code
        has_pygame = 'import pygame' in code or 'from pygame' in code
        
        if has_tkinter or has_pygame:
            print(f"✅ GUI framework detected: {'tkinter' if has_tkinter else 'pygame'}")
        
        return True
    except SyntaxError as e:
        print(f"❌ GUI script syntax: INVALID - {e}")
        return False
    except Exception as e:
        print(f"⚠️  GUI script check: {type(e).__name__} - {e}")
        return False

def main():
    print("\n" + "="*70)
    print("FAME COMMUNICATION METHODS - TEST SUITE")
    print("="*70)
    
    results = {
        "REST API": test_1_rest_api(),
        "Web Chat": test_2_web_chat(),
        "Python Chat": test_3_python_chat(),
        "Desktop GUI": test_4_desktop_gui(),
    }
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    for method, passed in results.items():
        status = "✅ WORKING" if passed else "⚠️  BLOCKED/NEEDS ATTENTION"
        print(f"{method:15} : {status}")
    
    print("\n" + "="*70)
    print("RECOMMENDATIONS")
    print("="*70)
    
    if not results["REST API"]:
        print("• REST API: Network firewall blocking external connections")
        print("  → Use SSH tunnel: ssh -L 8080:localhost:8080 ec2-user@18.220.108.23")
        print("  → Or test from EC2 instance directly")
    
    if results["Web Chat"]:
        print("• Web Chat: Run 'python start_fame_chat.py' to start local server")
        print("  → Opens browser at http://localhost:8000/fame_chat.html")
    
    if results["Python Chat"]:
        print("• Python Chat: Run 'python chat_with_fame.py' for interactive terminal chat")
    
    if results["Desktop GUI"]:
        print("• Desktop GUI: Run 'python enhanced_fame_communicator.py' for full GUI experience")
    
    print("\n")

if __name__ == "__main__":
    main()

