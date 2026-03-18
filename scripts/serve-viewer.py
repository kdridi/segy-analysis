#!/usr/bin/env python3
"""
Simple HTTP server to serve SEG-Y viewer with sample data.
Run: python scripts/serve-viewer.py
Then open: http://localhost:8080/segy-viewer.html
"""

import http.server
import socketserver
import os
import urllib.parse

PORT = 8080
DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class SegyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Enable CORS for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        super().end_headers()

def main():
    os.chdir(DIRECTORY)
    with socketserver.TCPServer(("", PORT), SegyHTTPRequestHandler) as httpd:
        print(f"🌐 SEG-Y Viewer server running at http://localhost:{PORT}/")
        print(f"📁 Serving directory: {DIRECTORY}")
        print(f"📊 Viewer: http://localhost:{PORT}/segy-viewer.html")
        print(f"📁 Sample files in: data/segy-samples/")
        print("\nPress Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")

if __name__ == "__main__":
    main()
