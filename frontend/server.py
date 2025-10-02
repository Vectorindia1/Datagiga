#!/usr/bin/env python3
"""
Simple HTTP server to serve the GigaSheet frontend
"""
import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

PORT = 3000
DIRECTORY = Path(__file__).parent

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def start_server():
    """Start the HTTP server"""
    os.chdir(DIRECTORY)
    
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"[FRONTEND] Server starting at http://localhost:{PORT}")
        print(f"[FILES] Serving files from: {DIRECTORY}")
        print("[BROWSER] Opening browser in 3 seconds...")
        print("Press Ctrl+C to stop the server")
        
        # Open browser after a short delay
        import threading
        import time
        
        def open_browser():
            time.sleep(3)
            try:
                webbrowser.open(f'http://localhost:{PORT}')
                print("[SUCCESS] Browser opened successfully!")
            except Exception as e:
                print(f"[WARNING] Could not open browser automatically: {e}")
                print(f"Please manually open http://localhost:{PORT}")
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[STOPPED] Frontend server stopped.")

if __name__ == "__main__":
    start_server()