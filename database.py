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
            cursor = conn.cursor()  # Create a cursor object
            return conn, cursor
    except Error as e:
        print(f'Error connecting to MySQL database: {e}')
        return None, None

def close(conn, cursor):
    """ Close MySQL database connection """
    try:
        if conn.is_connected():
            cursor.close()  # Close the cursor
            conn.close()
            print('Connection to MySQL database closed')
    except Error as e:
        print(f'Error closing connection to MySQL database: {e}')

# Test the database connection
if __name__ == '__main__':
    conn, cursor = connect()
    if conn:
        close(conn, cursor)
