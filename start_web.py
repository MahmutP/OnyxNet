import http.server
import socketserver
import webbrowser
import threading
import time
import os
import subprocess

PORT = 8000
# Since we chdir to 'web', the URL is now just /index.html
URL = f"http://localhost:{PORT}/index.html"

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass # Suppress logs for cleaner output

def get_version():
    try:
        commit_count = int(subprocess.check_output(
            ["git", "rev-list", "--count", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip())
        
        major = commit_count // 100
        minor = (commit_count % 100) // 10
        patch = commit_count % 10
        return f"v{major}.{minor}.{patch}"
    except:
        return "v1.0.0"

def generate_version_js():
    version = get_version()
    print(f"[*] Detected Version: {version}")
    
    # Write to web/js/version.js
    js_content = f'const ONYX_VERSION = "{version}";'
    try:
        with open("web/js/version.js", "w") as f:
            f.write(js_content)
    except Exception as e:
        print(f"[!] Failed to write version.js: {e}")

def start_server():
    # Generate version file before changing directory
    generate_version_js()
    
    # Change working directory to 'web' to prevent exposing other project files
    os.chdir("web")
    
    with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
        print(f"[*] Serving HTTP on port {PORT}...")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()

if __name__ == "__main__":
    print(f"[*] Opening browser: {URL}")
    
    # Run server in a separate thread so we can join main thread or just block
    # Actually, serve_forever blocks.
    
    # Open browser after a slight delay to ensure server is ready (though TCP bind is fast)
    threading.Timer(1.0, lambda: webbrowser.open(URL)).start()
    
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n[!] Web Server stopped.")
