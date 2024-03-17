import socket
import threading
import os
import json
import mysql.connector
from mysql.connector import Error
from configparser import ConfigParser

# Initialize variables to store networking and logs data
networking_data = []
logs_data = []

# Connect to MySQL database
def connect():
    """ Connect to MySQL database """
    try:
        config = read_config()
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        if conn.is_connected():
            print('Connected to MySQL database')
            return conn, cursor
    except Error as e:
        print(e)

def read_config(filename='config.ini', section='mysql'):
    parser = ConfigParser()
    parser.read(filename)
    config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in the {filename} file')
    return config

def close(conn, cursor):
    """ Close MySQL database connection """
    try:
        cursor.close()
        conn.close()
        print('Connection to MySQL database closed')
    except Error as e:
        print(e)

def ingest_data(conn, cursor, directory):
    try:
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                with open(os.path.join(directory, filename), 'r') as file:
                    data = json.load(file)
                    timestamp = data.get('timestamp')
                    source_ip = data.get('source_ip')
                    destination_ip = data.get('destination_ip')
                    event_type = data.get('event_type')
                    user = data.get('user_name')
                    message = data.get('message')
                    cursor.execute('''
                        INSERT INTO logs (timestamp, source_ip, destination_ip, event_type, user_name, message)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (timestamp, source_ip, destination_ip, event_type, user, message))
                    conn.commit()
    except Exception as e:
        print(f'Error ingesting data: {e}')
    finally:
        close(conn, cursor)

# Function to get the private IP address of the machine
def get_private_ip():
    try:
        # Create a temporary socket to get the local IP address
        temp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        temp_sock.connect(("8.8.8.8", 80))  # Connect to a known external server
        local_ip = temp_sock.getsockname()[0]
        temp_sock.close()
        return local_ip
    except Exception as e:
        print(f"Error getting local IP address: {e}")
        return None

# Automatically detect the private IP address
listen_ip = get_private_ip()
if not listen_ip:
    print("Failed to detect manager's private IP address")
    exit()

print(f"Detected manager's private IP address: {listen_ip}")

# IP address and port to listen on
listen_port = 12345

# Directory to store received data
output_dir = "received_data"
os.makedirs(output_dir, exist_ok=True)

# Function to handle incoming connections
def handle_connection(conn, addr):
    print(f"Agent connected from {addr}")
    try:
        # Receive data from the agent
        data = conn.recv(1024)
        
        # Convert the received data to JSON format
        try:
            json_data = json.loads(data.decode())
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON data: {e}")
            return
        
        # Check the message type
        if "timestamp" in json_data and "source_ip" in json_data:
            # This is a log message from the agent
            filename = f"{output_dir}/log_{addr[0]}_{addr[1]}.json"
            with open(filename, "w") as f:
                json.dump(json_data, f, indent=4)
        elif "System" in json_data and "Application" in json_data:
            # This is the Windows logs data
            filename = f"{output_dir}/windows_logs.json"
            with open(filename, "w") as f:
                json.dump(json_data, f, indent=4)
        else:
            # This is networking data
            filename = f"{output_dir}/networking_{addr[0]}_{addr[1]}.json"
            with open(filename, "w") as f:
                json.dump(json_data, f, indent=4)
    except Exception as e:
        print(f"Error handling connection: {e}")
    finally:
        # Close the connection
        conn.close()

# Create a socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Bind the socket to the IP address and port
    sock.bind((listen_ip, listen_port))
    # Listen for incoming connections
    sock.listen()
    print(f"Manager is listening on {listen_ip}:{listen_port}")

    # Main loop to accept incoming connections
    while True:
        # Accept incoming connections
        conn, addr = sock.accept()
        # Handle the connection in a new thread
        threading.Thread(target=handle_connection, args=(conn, addr)).start()
except Exception as e:
    print(f"Error starting manager: {e}")
finally:
    # Close the socket
    sock.close()

# Save networking data to a file
with open("networking_data.json", "w") as f:
    for data in networking_data:
        json.dump(data, f, indent=4)

# Save logs data to a file
with open("logs_data.json", "w") as f:
    for data in logs_data:
        json.dump(data, f, indent=4)

# Connect to MySQL database and ingest logs data
conn, cursor = connect()
ingest_data(conn, cursor, output_dir)
