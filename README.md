# SIEM6 Project Documentation

## Overview
The SIEM6 Project is a Security Information and Event Management (SIEM) system designed to collect, store, and analyze log data from various sources. It consists of agents that send log data to a central manager, which then processes and stores this information in a MySQL database for further analysis.

## Prerequisites
- Python 3.6 or higher
- MySQL Server
- A Unix/Linux environment (e.g., Ubuntu, CentOS, Kali Linux)
- `mysql-connector-python` package
- Network access between agents and manager

## Setup Instructions
1. **MySQL Database Setup**
   - Install MySQL Server on your system.
   - Create a database named `siem_database`.
   - Inside `siem_database`, create a table for storing logs with the required schema.
2. **Python Environment Setup**
   - Ensure Python 3.6 or higher is installed on your system.
   - Install `mysql-connector-python` using pip: `pip install mysql-connector-python`.
3. **Configuration**
   - Update `config.ini` with your MySQL database credentials.

## Components
### 1. `config.ini`
A configuration file containing MySQL database connection details.

### 2. `database.py`
Defines functions for connecting to and disconnecting from the MySQL database.

### 3. `data_ingestion.py`
Responsible for ingesting JSON formatted log data from the `logs` directory into the MySQL database.

### 4. `manager.py`
Acts as a central manager, listening for log data from agents over the network, storing received logs in JSON format in the `received_data` directory, and then ingesting them into the MySQL database.

### 5. `logs` Directory
Stores JSON formatted log data to be ingested into the database.

### 6. `received_data` Directory
Temporary storage for log data received from agents before being ingested into the database.

## Running the Project
1. Start the MySQL database service.
2. Run `manager.py` to start listening for log data from agents.
3. Deploy and run agent scripts on client machines to start sending log data to the manager.

# Agent.py Documentation

The `agent.py` script is designed to run on client machines and send log data to the central manager of the SIEM system. It uses Scapy for packet sniffing and analysis, extracting relevant information from network packets and sending it to the manager for further processing.

## Prerequisites
- Python 3.x
- Scapy library
- Network access to the manager

## Usage
1. **Configuration**: Set the `manager_ip` and `manager_port` variables to the IP address and port of the SIEM manager.
2. **Running the Agent**: Execute the script on client machines to start sending log data to the manager.

## Functionality
- **Packet Analysis**: Uses Scapy to analyze network packets and extract source IP addresses and event types.
- **Event Detection**: Detects Nmap scans, SSH brute force attempts, and other networking connections.
- **Data Formatting**: Formats packet information into JSON format for transmission to the manager.
- **Data Transmission**: Sends JSON-formatted data to the manager using a socket connection.

## Important Note
Replace the placeholder IP address `192.168.1.2` with the actual destination IP address in the `analyze_packet` function to accurately reflect the destination of the network traffic.

## Example Usage
```python
python3 agent.py
