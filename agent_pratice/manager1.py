import socket
import threading
import hashlib

# IP address and port to listen on
listen_ip = "192.168.100.44"
listen_port = 12345
secret_key = "my_secret_key"

# Function to handle incoming connections
def handle_connection(conn, addr):
    print(f"Agent connected from {addr}")
    try:
        # Receive encrypted data from the agent
        data = conn.recv(1024)
        decrypted_data = hashlib.sha256((secret_key + data.decode()).encode()).hexdigest()
        print(f"Decrypted data from agent ({addr}): {decrypted_data}")
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
