import socket
import threading
import os
import json
import mysql.connector
from mysql.connector import Error
from configparser import ConfigParser

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

def connect():
    """ Connect to MySQL database """
    try:
        config = read_config()
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            print('Connected to MySQL database')
            return conn
    except Error as e:
        print(e)

def close(conn, cursor):
    """ Close MySQL database connection """
    try:
        cursor.close()
        conn.close()
        print('Connection to MySQL database closed')
    except Error as e:
        print(e)

def ingest_data(directory):
    conn = connect()
    cursor = conn.cursor()
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

# IP address and port to listen on
listen_ip = "192.168.191.207"
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
        
        # Write the JSON data to a file
        filename = f"{output_dir}/agent_{addr[0]}_{addr[1]}.json"
        with open(filename, "w") as f:
            json.dump(json_data, f, indent=4)
        
        # Ingest the data into the database
        ingest_data(output_dir)
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
