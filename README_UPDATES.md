# Project Updates

## Server
- The server (`Server/app.py`) is configured to listen on all interfaces.
- **Critical Fix**: Fixed static file pathing so images save correctly regardless of where the script is run from.
- **Features**: 
  - **Camera Stream**: Live webcam video.
  - **Screen Share**: Live screen mirroring (Monitor).

## Client (Windows)
- Source: `Client/client.py`
- Executable: `Build/AsyncRAT_Client.exe` (Building...)
- **Configuration**: Defaults to connecting to `170.64.186.179`.
- **New Features**: 
  - **Start Screen Share**: Mirrors the desktop screen to the server (blue border).
  - **Start Live Stream**: Mirrors webcam to the server (green border).

## Client (Android)
- **APK**: See `Client/Android/HOW_TO_BUILD_APK.txt`.
- **Note**: Screen sharing on Android requires different permissions (MediaProjection), which is complex to implement in a simple script. The current 'monitor' command may not work on Android without native Java code. Camera stream should work if permissions are granted.

## Testing
1. Run Server: `python Server/app.py`
2. Run Client: `python Client/client.py`
3. Web UI:
   - Click "Watch Feed" for Camera.
   - Click "Watch Screen" for Screen Share.
