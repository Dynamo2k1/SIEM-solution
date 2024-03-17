from datetime import datetime
import subprocess
import shutil
import mysql.connector
from mysql.connector import Error
import threading
import time
from scapy.all import *
import json
import os

# Connect to MySQL database
def connect():
    try:
        config = {
            'user': 'dynamo89247',
            'password': '1590',
            'host': '192.168.100.44',
            'database': 'siem_database'
        }
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        if conn.is_connected():
            print('Connected to MySQL database')
            return conn, cursor
    except Error as e:
        print(e)
        raise e

# Close MySQL database connection
def close(conn, cursor):
    try:
        cursor.close()
        conn.close()
        print('Connection to MySQL database closed')
    except Error as e:
        print(e)

# Function to create a table for each event if it doesn't exist
def create_table(cursor, event_type):
    try:
        table_name = f"event_{event_type.replace(' ', '_').lower()}"
        query = f"CREATE TABLE IF NOT EXISTS {table_name} (id INT AUTO_INCREMENT PRIMARY KEY, timestamp DATETIME, ip_address VARCHAR(255))"
        cursor.execute(query)
    except Error as e:
        print(f"Error creating table for event {event_type}: {e}")

# Function to create tables for all unique event types
def create_all_tables(cursor, events_data):
    unique_event_types = set()
    for data in events_data:
        if "event_type" in data:
            unique_event_types.add(data["event_type"])
    
    for event_type in unique_event_types:
        create_table(cursor, event_type)

# Function to ingest data into MySQL database
def ingest_data(conn, cursor, data):
    try:
        create_table(cursor, data["event_type"])
        table_name = f"event_{data['event_type'].replace(' ', '_').lower()}"
        query = f"INSERT INTO {table_name} (timestamp, ip_address) VALUES (%s, %s)"
        cursor.execute(query, (data["timestamp"], data["ip_address"]))
        conn.commit()
        print("Data saved to MySQL database")
    except Exception as e:
        print(f"Error saving data to MySQL database: {e}")

# Initialize variables to store IP addresses
attacking_ips = []

# Define a function to analyze packets
def analyze_packet(packet):
    if IP in packet:
        src_ip = packet[IP].src
        destination_ip = packet[IP].dst

        if packet.haslayer(TCP):
            if packet[TCP].flags == 0x02:  # SYN flag set (Nmap scan)
                if src_ip not in attacking_ips:
                    attacking_ips.append(src_ip)
                    data = {"timestamp": datetime.now(), "ip_address": src_ip, "event_type": "Nmap scan"}
                    with open("packet_analysis.json", "a") as file:
                        json.dump(data, file)
                        file.write("\n")
                    ingest_data(conn, cursor, data)
            elif packet[TCP].dport == 22 and packet[TCP].flags == 0x12:  # SSH brute force
                if src_ip not in attacking_ips:
                    attacking_ips.append(src_ip)
                    data = {"timestamp": datetime.now(), "ip_address": src_ip, "event_type": "SSH brute force"}
                    with open("packet_analysis.json", "a") as file:
                        json.dump(data, file)
                        file.write("\n")
                    ingest_data(conn, cursor, data)

def scan_for_malware():
    try:
        # Run the Windows Defender scan command
        malware_scan_path = "C:\\Program Files\\Windows Defender\\MpCmdRun.exe"
        print("Malware Scan Path:", malware_scan_path)
        subprocess.run([malware_scan_path, "-Scan", "-ScanType", "3", "-File", "%windir%\\*"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)

        # Check if the scan results file exists, if not, create an empty file
        scan_results_path = "%ProgramData%\\Microsoft\\Windows Defender\\Scans\\History\\ResultsResource.txt"
        if not os.path.exists(scan_results_path):
            with open(scan_results_path, "w") as file:
                pass

        # Copy the scan results file to the current directory
        shutil.copy2(scan_results_path, ".")

    except Exception as e:
        print(f"Error scanning for malware: {e}")

# Function to run wevtutil command and save output to a JSON file
def run_wevtutil():
    try:
        # Run the wevtutil command for System logs
        system_logs = subprocess.run(["wevtutil", "qe", "System", "/rd:true", "/c:20", "/f:text", "/q:*"],
                                      capture_output=True, text=True)
        system_logs_output = system_logs.stdout

        # Check if the output is empty
        if not system_logs_output:
            raise ValueError("Empty output from wevtutil command")

        # Extract relevant information from the output
        events = []
        current_event = {}
        for line in system_logs_output.splitlines():
            if not line.strip():
                if current_event:
                    events.append(current_event)
                    current_event = {}
            else:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    key, value = parts
                    current_event[key.strip()] = value.strip()

        # Save events to a JSON file
        with open("events.json", "w") as file:
            json.dump(events, file, indent=4)

        # Print or save events data as needed
        print("Events saved to events.json")
    except Exception as e:
        print(f"Error running wevtutil command: {e}")

# Function to read logs data from file and ingest it into MySQL database
def read_and_ingest_data():
    try:
        # Read logs data
        with open("events.json", "r") as file:
            logs_data = json.load(file)

        # Ingest data into MySQL database
        for event in logs_data:
            # Convert timestamp to datetime object
            timestamp = datetime.strptime(event.get("Date", ""), '%Y-%m-%dT%H:%M:%S.%f000Z')
            ingest_data(conn, cursor, {"timestamp": timestamp, "ip_address": "NA", "event_type": event.get("Event ID", "")})
        print("Logs data ingested into MySQL database")
    except Exception as e:
        print(f"Error reading or ingesting data: {e}")

# Function to periodically update MySQL database
def update_mysql():
    while True:
        time.sleep(5)  # Update every 5 seconds
        conn, cursor = connect()
        close(conn, cursor)

# Main function
if __name__ == "__main__":
    conn, cursor = connect()
    try:
        # Start packet sniffing in a separate thread
        threading.Thread(target=lambda: sniff(prn=analyze_packet, filter="ip"), daemon=True).start()

        # Start updating MySQL database in a separate thread
        threading.Thread(target=update_mysql, daemon=True).start()

        # Run malware scan
        scan_for_malware()
        # Run wevtutil command
        run_wevtutil()

        # Read logs data from file and ingest into MySQL database
        if os.path.exists("events.json"):
            with open("events.json", "r") as file:
                events_data = json.load(file)
            create_all_tables(cursor, events_data)
            read_and_ingest_data()
        else:
            print("No events.json file found")
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        close(conn, cursor)

       
