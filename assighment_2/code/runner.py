import subprocess
import os

# Path to your virtual environment's Python executable
venv_python = os.path.join('B:', 'College', 'SMAI', 'assighment_2', 'code', 'newenv', 'Scripts', 'python.exe')

# Absolute path to main.py
main_py_path = r'B:\College\SMAI\assighment_2\code\main.py'

# Absolute paths to input and output files, replacing backslashes with forward slashes
commands = [
    [venv_python, main_py_path, os.path.abspath('..//EUCLIDEAN_50.txt').replace("\\", "/"), os.path.abspath('output_E50.txt').replace("\\", "/")],
    [venv_python, main_py_path, os.path.abspath('..//EUCLIDEAN_100.txt').replace("\\", "/"), os.path.abspath('output_E100.txt').replace("\\", "/")],
    [venv_python, main_py_path, os.path.abspath('..//EUCLIDEAN_200.txt').replace("\\", "/"), os.path.abspath('output_E200.txt').replace("\\", "/")],
    [venv_python, main_py_path, os.path.abspath('..//NON_EUCLIDEAN_50.txt').replace("\\", "/"), os.path.abspath('output_NE50.txt').replace("\\", "/")],
    [venv_python, main_py_path, os.path.abspath('..//NON_EUCLIDEAN_100.txt').replace("\\", "/"), os.path.abspath('output_NE100.txt').replace("\\", "/")],
    [venv_python, main_py_path, os.path.abspath('..//NON_EUCLIDEAN_200.txt').replace("\\", "/"), os.path.abspath('output_NE200.txt').replace("\\", "/")]
]

# Function to run commands with a timeout
def run_with_timeout(command):
    try:
        # Debugging: print the command to verify the paths
        print(f"Running command: {' '.join(command)}")
        
        # Run the command as a subprocess
        process = subprocess.Popen(command)
        
        # Wait for the process to finish or time out after 10 seconds
        process.wait(timeout=10)
        
        print(f"Command {command} finished successfully.")
    
    except subprocess.TimeoutExpired:
        print(f"Timeout reached! Command {command} terminated.")
    except FileNotFoundError as e:
        print(f"FileNotFoundError: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Run each command in the list
for command in commands:
    run_with_timeout(command)
