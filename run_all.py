import subprocess
import time
import os
import sys

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(root_dir, 'Server', 'app.py')
    client_script = os.path.join(root_dir, 'Client', 'client.py')
    
    print("Starting Server...")
    # Open new command prompt for Server
    subprocess.Popen(f'start cmd /k python "{server_script}"', shell=True)
    
    time.sleep(2)
    
    print("Starting Client...")
    # Open new command prompt for Client
    subprocess.Popen(f'start cmd /k python "{client_script}"', shell=True)
    
    print("Done! Check the new windows.")

if __name__ == "__main__":
    main()
