#!/usr/bin/env python3
import os
import sys
import webbrowser
import threading
import time
import subprocess
import signal

# Launch the web server as a subprocess instead of importing directly
def start_server():
    """Start the Flask server as a subprocess"""
    env = os.environ.copy()
    # Use the same Python interpreter that's running this script
    python_path = sys.executable
    server_process = subprocess.Popen(
        [python_path, "-m", "flask", "--app", "web_app", "run", "--port", "54321"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    return server_process

def open_browser():
    """Open the web browser after a short delay"""
    # Wait for the server to start
    time.sleep(2)
    # Open the web browser
    webbrowser.open('http://127.0.0.1:54321/')
    print("Opened browser to Catalog Parser")

def main():
    # Start the server
    server_process = start_server()
    print("Starting Catalog Parser server...")
    
    # Open the browser
    open_browser()
    
    # Keep the main thread alive to prevent the application from exiting
    try:
        while server_process.poll() is None:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Shutting down...")
        server_process.terminate()
    
    print("Catalog Parser shutting down...")

if __name__ == "__main__":
    main()
