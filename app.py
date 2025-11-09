from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import threading
import subprocess
import os
import queue
import time
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")


assistant_process = None
output_queue = queue.Queue()
output_thread = None
is_assistant_running = False

def enqueue_output(out, queue):
    """Reads output from a subprocess and puts it into a queue."""
    for line in iter(out.readline, b''):
        queue.put(line.decode('utf-8').strip())
    out.close()

def read_process_output():
    """Continuously reads output from the assistant process and emits to UI."""
    global is_assistant_running
    
    while is_assistant_running or not output_queue.empty():
        try:
            line = output_queue.get(timeout=0.1)
            
           
            clean_line = line.strip()
            
            
            if re.search(r'(?i)listening\.{3}|waiting for command|listening for audio', clean_line):
                socketio.emit('assistant_status', {'status': 'listening', 'message': 'Listening for command...'})
                socketio.emit('assistant_message', {'message': clean_line, 'type': 'status'})
                
            elif re.search(r'(?i)processing\.{3}|recognizing\.{3}|analyzing command', clean_line):
                socketio.emit('assistant_status', {'status': 'processing', 'message': 'Processing command...'})
                socketio.emit('assistant_message', {'message': clean_line, 'type': 'status'})
                
            elif re.search(r'(?i)you said:|user said:|command:|speech:', clean_line):
                
                command_match = re.search(r'(?i)(you said|user said|command|speech)[:\s]*(.+)', clean_line)
                if command_match:
                    command_text = command_match.group(2).strip()
                    socketio.emit('assistant_command', {'command': command_text})
                    socketio.emit('assistant_message', {'message': f"Command: {command_text}", 'type': 'user'})
                else:
                    socketio.emit('assistant_message', {'message': clean_line, 'type': 'user'})
                    
            elif re.search(r'(?i)assistant:|ai:|response:', clean_line):
               
                response_match = re.search(r'(?i)(assistant|ai|response)[:\s]*(.+)', clean_line)
                if response_match:
                    response_text = response_match.group(2).strip()
                    socketio.emit('assistant_message', {'message': response_text, 'type': 'assistant'})
                else:
                    socketio.emit('assistant_message', {'message': clean_line, 'type': 'assistant'})
                    
            elif re.search(r'(?i)error|failed|exception|could not', clean_line):
                socketio.emit('assistant_message', {'message': clean_line, 'type': 'error'})
                
            elif re.search(r'(?i)starting|ready|initialized', clean_line):
                socketio.emit('assistant_status', {'status': 'running', 'message': 'Assistant is running'})
                socketio.emit('assistant_message', {'message': clean_line, 'type': 'status'})
                
            elif re.search(r'(?i)stopping|shutting down|exit|goodbye', clean_line):
                socketio.emit('assistant_status', {'status': 'stopped', 'message': 'Assistant is stopping'})
                socketio.emit('assistant_message', {'message': clean_line, 'type': 'status'})
                
            elif re.search(r'(?i)sent|completed|success|done|finished', clean_line):
                socketio.emit('assistant_message', {'message': clean_line, 'type': 'status'})
                
            else:
                
                socketio.emit('assistant_message', {'message': clean_line, 'type': 'assistant'})
                
        except queue.Empty:
            time.sleep(0.05)
        except Exception as e:
            print(f"Error reading process output: {e}")
            socketio.emit('assistant_message', {'message': f"Output processing error: {e}", 'type': 'error'})

@app.route('/')
def index():
    return render_template('index_assistant.html')

@app.route('/start_assistant', methods=['POST'])
def start_assistant():
    global assistant_process, output_thread, is_assistant_running
    
    if assistant_process and assistant_process.poll() is None:
        return jsonify({'success': False, 'message': 'Assistant is already running'})

    try:
        
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main_assistant.py')
       
        assistant_process = subprocess.Popen(
            [os.sys.executable, '-u', script_path],  
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,  
            universal_newlines=False
        )
        is_assistant_running = True
        
       
        output_thread = threading.Thread(target=enqueue_output, args=(assistant_process.stdout, output_queue), daemon=True)
        output_thread.start()

      
        emit_thread = threading.Thread(target=read_process_output, daemon=True)
        emit_thread.start()

        socketio.emit('assistant_status', {'status': 'running', 'message': 'Starting assistant...'})
        return jsonify({'success': True, 'message': 'Assistant started successfully'})
        
    except Exception as e:
        is_assistant_running = False
        error_msg = f'Failed to start assistant process: {str(e)}'
        socketio.emit('assistant_message', {'message': error_msg, 'type': 'error'})
        return jsonify({'success': False, 'message': error_msg})

@app.route('/stop_assistant', methods=['POST'])
def stop_assistant():
    global assistant_process, is_assistant_running
    
    if not assistant_process or assistant_process.poll() is not None:
        return jsonify({'success': False, 'message': 'Assistant is not running'})

    try:
        socketio.emit('assistant_status', {'status': 'processing', 'message': 'Stopping assistant...'})
        
       
        assistant_process.terminate()
        
        
        try:
            assistant_process.wait(timeout=5)
            is_assistant_running = False
            socketio.emit('assistant_status', {'status': 'stopped', 'message': 'Assistant stopped successfully'})
            return jsonify({'success': True, 'message': 'Assistant stopped'})
            
        except subprocess.TimeoutExpired:
            
            assistant_process.kill()
            assistant_process.wait()
            is_assistant_running = False
            socketio.emit('assistant_status', {'status': 'stopped', 'message': 'Assistant force-stopped'})
            return jsonify({'success': True, 'message': 'Assistant force-stopped (timeout)'})
            
    except Exception as e:
        is_assistant_running = False
        error_msg = f'Error stopping assistant: {str(e)}'
        socketio.emit('assistant_message', {'message': error_msg, 'type': 'error'})
        return jsonify({'success': False, 'message': error_msg})

@socketio.on('connect')
def handle_connect():
   
    status = 'running' if (assistant_process and assistant_process.poll() is None) else 'stopped'
    status_msg = 'Assistant is running' if status == 'running' else 'Assistant is stopped'
    
    socketio.emit('assistant_status', {'status': status, 'message': status_msg})
    socketio.emit('assistant_message', {'message': f'UI connected. Assistant status: {status}', 'type': 'status'})

if __name__ == '__main__':
    print("Starting AI Assistant Web Interface...")
    print("Open your browser and go to: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, use_reloader=False)
