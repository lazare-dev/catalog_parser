#!/usr/bin/env python3
"""
Script to build a macOS application package (.app) and DMG installer.
Uses a more compatible approach with difficult dependencies.
"""

import os
import sys
import shutil
import subprocess

# Configuration
APP_NAME = "Catalog Parser"
VERSION = "1.0.0"
MAIN_SCRIPT = "macos_app.py"

# Create the main script that launches the UI
with open(MAIN_SCRIPT, "w") as f:
    f.write('''#!/usr/bin/env python3
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
''')

# Create a simple setup.py that only includes minimal dependencies
with open('temp_setup.py', 'w') as f:
    f.write('''
from setuptools import setup

setup(
    app=['%s'],
    name='%s',
    version='%s',
    options={
        'py2app': {
            'argv_emulation': False,
            'packages': ['flask'],
            'includes': [],
            'plist': {
                'CFBundleName': '%s',
                'CFBundleDisplayName': '%s',
                'CFBundleVersion': '%s',
                'CFBundleShortVersionString': '%s',
                'NSHumanReadableCopyright': 'Copyright © 2023',
            }
        }
    },
    setup_requires=['py2app'],
)
''' % (MAIN_SCRIPT, APP_NAME, VERSION, APP_NAME, APP_NAME, VERSION, VERSION))

# Clean up previous build
for dir_to_clean in ['build', 'dist']:
    if os.path.exists(dir_to_clean):
        shutil.rmtree(dir_to_clean)

# Build the app with py2app
print("Building macOS application...")
try:
    subprocess.run([sys.executable, 'temp_setup.py', 'py2app'], check=True)
    print("Build successful!")
except subprocess.CalledProcessError as e:
    print(f"Error building application: {e}")
    sys.exit(1)

# Create a DMG using create-dmg
print("Creating DMG installer...")
try:
    subprocess.run([
        'create-dmg',
        '--volname', f"{APP_NAME} Installer",
        '--window-pos', '200', '120',
        '--window-size', '800', '400',
        '--icon-size', '100',
        '--icon', f"{APP_NAME}.app", '200', '200',
        '--hide-extension', f"{APP_NAME}.app",
        '--app-drop-link', '600', '200',
        f"dist/{APP_NAME}-{VERSION}.dmg",
        f"dist/{APP_NAME}.app"
    ], check=True)
    print(f"DMG created: dist/{APP_NAME}-{VERSION}.dmg")
except subprocess.CalledProcessError:
    print("Failed to create DMG. Make sure 'create-dmg' is installed (brew install create-dmg).")
    print(f"The app can still be found at: dist/{APP_NAME}.app")
except FileNotFoundError:
    print("create-dmg command not found. Install with: brew install create-dmg")
    print(f"The app can still be found at: dist/{APP_NAME}.app")

# Clean up temporary files
os.remove(MAIN_SCRIPT)
os.remove('temp_setup.py')
print("Build completed!")