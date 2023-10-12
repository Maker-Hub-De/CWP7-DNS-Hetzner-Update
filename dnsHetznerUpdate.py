#!/usr/bin/python3
import os
import sqlite3
import logging
import json
import time
import requests
import sys

from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class HeznerDNS:
    def __init__(self, auth_api_token, logging):
        # Use an absolute path to the SQLite database file
        self.auth_api_token = auth_api_token
        self.logging = logging
        
    def get_domain(self, file_name):
        # Extract the domain name from the file name by removing the '.db' extension
        domain, _ = os.path.splitext(file_name)
        
        # In case there's a path, extract the last part
        domain = domain.split('/.')[-1]  
        
        #domain = file_name.rsplit('.db', 1)[0]
        #domain = domain.rsplit('/.', 1)[1]
        return domain

    def get_zone_id(self, domain):
        try:
            response = requests.get(
                url="https://dns.hetzner.com/api/v1/zones",
                headers={
                    "Auth-API-Token": self.auth_api_token,
                },
                params={
                    "search_name": domain
                }
            )

            if response.status_code == 200: # Successful response
                # Parse JSON data    
                try:
                    json_object = json.loads(response.content)
                except json.JSONDecodeError as e:
                    logging.error(f"Couldn't get the new zone id")
                    logging.error(f"Error decoding JSON: {str(e)}")
                    return None

                # Retrieve the zone ID
                zone_id = json_object["zones"][0]["id"]
                return zone_id
            else:
                return None
        except requests.exceptions.RequestException:
            return None

    def create_zone(self, domain):
        try:
            response = requests.post(
                url="https://dns.hetzner.com/api/v1/zones",
                headers={
                    "Content-Type": "application/json",
                    "Auth-API-Token": self.auth_api_token,
                },
                data=json.dumps({
                    "name": domain,
                    "ttl": 11400
                })
            )

            if response.status_code in [200, 201]:  # ok & Created
                # Parse JSON data
                try:
                    json_object = json.loads(response.content)
                except json.JSONDecodeError as e:
                    logging.error(f"Coundn't get the new zone id")
                    logging.error(f"Error decoding JSON: {str(e)}")
                    return None
                    
                # Retrieve the zone ID
                zone_id = json_object["zone"]["id"]
                
            elif response.status_code in [401, 404, 406]:  # Unauthorized, not found, Not acceptable
                return None
            elif response.status_code == 422: # Unprocessable entity
                # Try again to get the zone ID
                zone_id = self.get_zone_id(domain)
                return zone_id
            else:
                return None
        except requests.exceptions.RequestException:
            return None

    def delete_zone(self, zone_id):
        try:
            response = requests.post(
                url=f"https://dns.hetzner.com/api/v1/zones/{zone_id}",
                headers={
                    "Auth-API-Token": self.auth_api_token,
                },
            )

            if response.status_code == 200: # Successful response
                print(response.content)
                return True
            else:
                return False
        except requests.exceptions.RequestException:
            return False
    
    def update_zone_from_file(self, zone_id, domain, file_name):
        # Send an HTTP request to transmit the modified file
        with open(file_name, 'rb') as file:

            # Read bytes from the file and convert it to a string
            file_content = file.read().decode('utf-8')

            # Create request data
            request_data = f"$ORIGIN {domain}.\n{file_content}"
            try:
                response = requests.post(
                    url=f"https://dns.hetzner.com/api/v1/zones/{zone_id}/import",
                    headers={
                        "Content-Type": "text/plain",
                        "Auth-API-Token": self.auth_api_token,
                    },
                    data=request_data
                )
                
                if response.status_code in [200, 201]:  # Successful response, Create
                    print(response.content)
                    return True
                else:
                    return False
            except requests.exceptions.RequestException:
                return False

class DBManager:
    def __init__(self, db_filename, logging):
        # Use an absolute path to the SQLite database file
        self.db_filename = os.path.abspath(db_filename)
        self.logging = logging

        # Check if the database file already exists; if not, create it
        if not os.path.exists(self.db_filename):
            self.create_db_file()
        else:
            self.logging.info(f"Database file '{self.db_filename}' found")

    def __del__(self):
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
        except sqlite3.Error as e:
            self.logging.error(f"Error closing the database connection: {str(e)}")

    def create_db_file(self):
        try:
            with sqlite3.connect(self.db_filename) as conn:
                self.logging.info(f"Database file '{self.db_filename}' created")
        except sqlite3.Error as e:
            self.logging.error(f"Error creating database file: {str(e)}")
            exit()  # Exit the program

    def create_table(self):
        try:
            with sqlite3.connect(self.db_filename) as conn:
                cursor = conn.cursor()
                # Check if the table already exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='file_info'")
                table_exists = cursor.fetchone()

                if not table_exists:
                    # Create table
                    cursor.execute('''
                        CREATE TABLE file_info (
                            filename TEXT PRIMARY KEY,
                            last_checked DATETIME
                        )
                    ''')
                    conn.commit()
                    self.logging.info("Table file_info created")
                else:
                    self.logging.info("Table file_info exists")
        except sqlite3.Error as e:
            self.logging.error(f"Error creating table: {str(e)}")

    def insert_file_info(self, filename, last_checked):
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO file_info (filename, last_checked) VALUES (?, ?)", (filename, last_checked))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            self.logging.error(f"Error inserting file info: {str(e)}")
            return False

    def update_file_info(self, filename, last_checked):
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            cursor.execute("UPDATE file_info SET last_checked = ? WHERE filename = ?", (last_checked, filename))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            self.logging.error(f"Error updating file info: {str(e)}")
            return False

    def delete_file_info(self, filename):
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM file_info WHERE filename = ?", (filename,))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            self.logging.error(f"Error deleting file info: {str(e)}")
            return False

    def get_file_info(self, filename):
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            cursor.execute("SELECT last_checked FROM file_info WHERE filename = ?", (filename,))
            last_checked = cursor.fetchone()
            conn.close()
            return last_checked[0] if last_checked else None
        except sqlite3.Error as e:
            self.logging.error(f"Error getting file info: {str(e)}")
            return None

    def get_files_not_checked_since(self, since_datetime):
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            cursor.execute("SELECT filename, last_checked FROM file_info WHERE last_checked <= ?", (since_datetime,))
            rows = cursor.fetchall()
            conn.close()
            return rows
        except sqlite3.Error as e:
            self.logging.error(f"Error getting files not checked since: {str(e)}")
            return []

    class MyObserverHandler(FileSystemEventHandler):
        def __init__(self, db_manager, auth_api_token, logging, directory):
            super(MyObserverHandler, self).__init__()
            self.db_manager = db_manager
            self.auth_api_token = auth_api_token
            self.logging = logging
            self.directory = directory
            
        def on_modified(self, event):
            current_check_time = datetime.now()
            hezner_dns = HeznerDNS(self.auth_api_token, logging)
            
            files_on_disk = [f for f in os.listdir(self.directory) if f.endswith('.db')]
            for file_name in files_on_disk:
                last_modified = datetime.fromtimestamp(os.path.getmtime(os.path.join(self.directory, file_name)))
                last_checked = self.db_manager.get_file_info(file_name)

                if last_checked == None: # No entry found; it could be a new zone
                    domain = hezner_dns.get_domain(file_name)
                    # Try to get a zone ID; the zone may already exist
                    zone_id = hezner_dns.get_zone_id(domain)
                    if zone_id == None:  # We don't have an existing zone 
                        domain = hezner_dns.create_zone(domain)
                    if zone_id == None: # Now we schould have a zone id; if not go on
                        logging.error("Could not create a new zone")
                        continue  # Continue to the next file
                            
                    # Updating the zone data
                    hezner_dns.update_zone_from_file(zone_id, domain, file_name)
                    # Insert into the database
                    self.db_manager.insert_file_info(file_name, current_check_time)
                        
                elif last_modified > last_checked           # changes that younger then last check
                and  last_checked < current_check_time - 2: # the last check scould be at least 2 seconds in the past
                    # Found a changed file
                    domain = hezner_dns.get_domain(file_name)
                    # Try to get a zone ID; the zone may already exist
                    zone_id = hezner_dns.get_zone_id(domain)
                    if zone_id == None: # Now we schould have a zone id; if not go on
                        domain = hezner_dns.create_zone(domain)
                        
                    if zone_id == None: # Now we need to have a zone_id
                        logging.error("Could not create new zone")
                        continue # Continue to the next file
                        
                    # Updating the zone data
                    hezner_dns.update_zone_from_file(zone_id, domain, file_name)
                    # Updating the database
                    if self.db_manager.update_file_info(file_name, current_check_time) == False:
                        logging.error("Could not update file {file_name} in datagbase.")
                        continue # Continue to the next file
                        
                else:
                    # Just update the check time
                    if self.db_manager.update_file_info(file_name, current_check_time) == False:
                        logging.error("Could not update file {file_name} in datagbase.")
                        continue # Continue to the next file
                    
            # Now checking the files in the database which weren't updated
            # That could happen if the file was deleted
            # First, get all relevant files
            files_in_db = self.db_manager.get_files_not_checked_since(current_check_time)
            for file_name in files_in_db:
                # Check if the file still exists on the file system
                if not os.path.exists(os.path.join(self.directory, file_name)):
                    # File was deleted
                    domain = hezner_dns.get_domain(file_name)
                    zone_id = hezner_dns.get_zone_id(domain)
                    if zone_id:
                         # We have to delete the zone
                        if hezner_dns.delete_zone(domain) == False:
                            logging.error(f"Could not delete zone {domain} from Hetzner DNS.")
                            continue  # Continue to the next file
                         if self.db_manager.delete_file_info(file_name) == False:
                            logging.error(f"Could not delete file {file_name} from database.")
                            continue  # Continue to the next file
                            
                        
# Function to load the configuration from the JSON file
def load_config(filename, logging):
    if not os.path.exists(filename):
        logging.error("Configuration file '{}' doesn't exist. Script will be stopped")
        exit()

    try:
        with open(filename, 'r') as config_file:
            # Reading the configuration file
            config = json.load(config_file)
            # Directory to watch over
            directory = config.get('directory', '/var/named/')
            # Authentication Token for the Hetzner API
            api_token = config.get('apiToken', '')

            return directory, api_token
    except json.JSONDecodeError as e:
        logging.error(f"Error loading configuration: {str(e)}")
        exit()
        
# Check if the authentication API token is present
def check_auth_api_token(api_token):
    if api_token == "":
        logging.error("Authentifizierungs-Token is missing. Script will be stopped")
        exit()

# Check if the directory exists
def check_directory(named_directory):    
    if not os.path.exists(named_directory):
        logging.error("Directory '{}' dosen't exist. Script will be stopped".format(named_directory))
        exit()

# The main part starts here
if __name__ == "__main__":
    script_directory = os.path.dirname(os.path.abspath(__file__))  # Pfad zum Verzeichnis, in dem das Skript liegt

    # Initialize logging
    log_filename = os.path.join(script_directory, time.strftime("%Y.%m.hetznerDnsUpdate.log"))

    logging.basicConfig(filename=log_filename,
                        level=logging.INFO,
                        format='%(asctime)s - %(levelname)s: %(message)s')

    # Load the configuration from the JSON file
    config_file_path = os.path.join(script_directory, 'config.json')  # Pfad zur Config-datei im Skriptverzeichnis
    named_directory, auth_api_token = load_config(config_file_path, logging)

    # Check if the authentication API token is set
    check_auth_api_token(auth_api_token)

    # Check if the directory exists
    check_directory(named_directory)
        
    # Create an instance of the DBManager class with the file path to the database
    db_file_path = os.path.join(script_directory, 'file_info.db')  # Pfad zur Datenbankdatei im Skriptverzeichnis

    db_manager = DBManager(db_file_path, logging)

    # Create the table if it doesn't exist
    db_manager.create_table()

    # Create an Observer that monitors the directory
    observer = Observer()
    observer.schedule(MyObserverHandler(db_manager, auth_api_token, logging, named_directory), path=named_directory, recursive=False)

    # Start the Observer
    observer.start()

    try:
        while True:
            time.sleep(5)  # Adjust the monitoring interval here
    except KeyboardInterrupt:
        # Stop the Observer
        observer.stop()
        # Wait until the Observer is fully stopped
        observer.join()

# Stop the Observer
observer.stop()
# Wait until the Observer is fully stopped
observer.join()
