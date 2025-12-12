# AsyncRAT-Python

This is a Python-based implementation of a Remote Administration Tool, inspired by AsyncRAT.

## Structure
- **Server**: Hosted on the administrator's machine. Listens for incoming connections.
- **Client**: Run on the target machine. Connects back to the server.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```



2. **Quick Start (Run Both)**:
   ```
   python run_all.py
   ```
   *This will open the Client terminal and start the Flask Web Server.*
   *Go to [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.*

3. **Manual Start**:
   - Start Web Server:
     ```
     python Server/app.py
     ```
   - Start Client:
     ```
     python Client/client.py
     ```
   *Note: For public access, edit `HOST` in `Client/client.py` with your public IP and ensure port 6000 (RAT) is forwarded/open.*


### Building for Target Machine via .exe
To run the client easily on another Windows machine without installing Python:
1. Run the builder script:
   ```
   python build_client.py
   ```
2. Navigate to the `Build` folder.
3. Copy `AsyncRAT_Client.exe` to the target machine and double-click it.
   *Since it was built with `--noconsole`, it will run silently in the background.*

## Disclaimer
This software is for educational purposes only. Do not use on systems you do not own or have permission to access.
