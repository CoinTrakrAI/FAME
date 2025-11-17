#!/usr/bin/env python3
"""
Simple local server to run FAME Chat HTML interface
Just double-click this file or run: python start_fame_chat.py
"""

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

PORT = 8000
HTML_FILE = "fame_chat.html"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check if HTML file exists
    if not Path(HTML_FILE).exists():
        print(f"ERROR: {HTML_FILE} not found!")
        print(f"Looking in: {script_dir}")
        input("Press Enter to exit...")
        return
    
    # Start server
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        url = f"http://localhost:{PORT}/{HTML_FILE}"
        print("=" * 60)
        print("FAME Chat Server Starting...")
        print("=" * 60)
        print(f"Server running at: {url}")
        print(f"Opening in your browser...")
        print("=" * 60)
        print("Press Ctrl+C to stop the server")
        print()
        
        # Open browser
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Could not open browser automatically: {e}")
            print(f"Please open: {url}")
        
        # Serve forever
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped. Goodbye!")

if __name__ == "__main__":
    main()

