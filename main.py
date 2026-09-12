import threading
import webbrowser
import os
import http.server
import socketserver
from jarvis import run_mr_b

def start_web_server():
    """Runs a background local server on port 8000 for the UI."""
    PORT = 8000
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args): pass 
        
    try:
        with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
            httpd.serve_forever()
    except OSError:
        pass # Fails silently if port 8000 is already in use

if __name__ == "__main__":
    # 1. Start the web server in a background thread
    server_thread = threading.Thread(target=start_web_server, daemon=True)
    server_thread.start()
    
    # 2. Automatically launch the browser UI
    print("🌐 Launching UI in browser...")
    webbrowser.open("http://localhost:8000")
    
    # 3. Start Mr. B's core intelligence loop
    run_mr_b()