
"""
Start script for the AI Assistant Web Interface
"""
import os
import sys
from app import socketio, app

if __name__ == '__main__':
    print("Starting AI Assistant Web Interface...")
    print("Open your browser and go to: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, use_reloader=False)
