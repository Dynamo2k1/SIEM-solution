import os
import json
from database import connect, close
from datetime import datetime

def ingest_data(directory):
    conn, cursor = connect()
    try:
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                with open(os.path.join(directory, filename), 'r') as file:
                    data = json.load(file)
                    for event in data['events']:
                        # Convert timestamp to MySQL-compatible format
                        timestamp = datetime.strptime(event.get('timestamp'), '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S')
                        source_ip = event.get('source_ip')
                        destination_ip = event.get('destination_ip')
                        event_type = event.get('event_type')
                        user = event.get('user')
                        message = event.get('message')
                        cursor.execute('''
                            INSERT INTO logs (timestamp, source_ip, destination_ip, event_type, user_name, message)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        ''', (timestamp, source_ip, destination_ip, event_type, user, message))
        conn.commit()
    except Exception as e:
        print(f'Error ingesting data: {e}')
    finally:
        close(conn, cursor)

if __name__ == '__main__':
    directory = '/root/myProject/SIEM6/logs'
    ingest_data(directory)
