#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__     = "Mia Sophie Behrendt"
__copyright__  = "Copyright 2023, Maker-Hub.de"
__license__    = "GPL"
__version__    = "1.0.0"
__maintainer__ = "Maker-Hub-De"
__email__      = "github@maker-hub.de"
__status__     = "Development"
__date__       = "12.10.2023"

import os
import logging
import time
#import sys
import fcntl
import atexit
import json
from watchdog.observers import Observer
from modules import db_manager
from modules import hetzner_dns
from modules import observer_handler

observer_started = False

# Function to load the configuration from the JSON file
def load_config(filename, logger=None):
    my_logger = logger if logger else logging.getLogger("hetznerDnsUpdate")
    if not os.path.exists(filename):
        my_logger.error("Configuration file '{}' doesn't exist. Script will be stopped")
        sys.exit(1)

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
        my_logger.error(f"Error loading configuration: {str(e)}")
        sys.exit(1)

# Check if the authentication API token is present
def check_auth_api_token(api_token, logger=None):
    my_logger = logger if logger else logging.getLogger("hetznerDnsUpdate")  
    
    if api_token == "":
        my_logger.error("Authentifizierungs-Token is missing. Script will be stopped")
        sys.exit(1)

# Check if the directory exists
def check_directory(named_directory, logger=None):
    my_logger = logger if logger else logging.getLogger("hetznerDnsUpdate")

    if not os.path.exists(named_directory):
        my_logger.error("Watch dog directory '{}' dosen't exist. Script will be stopped".format(named_directory))
        sys.exit(1)

def remove_lock_file(lock_file, logger=None):
    my_logger = logger if logger else logging.getLogger("hetznerDnsUpdate")

    try:
        lock_file.close()
        os.remove("dnsUpdate.lock")
    except Exception as e:
        my_logger.error(f"Erro during deleten lock file: {str(e)}")

def stop_observer(observer):
    global observer_started
    if observer_started:
        my_observer.stop()
        my_observer.join()

# The main part starts here
if __name__ == "__main__":
    # Path to the directory where the script is located
    script_directory = os.path.dirname(os.path.abspath(__file__))

    # Initialize logging
    log_filename = os.path.join(script_directory, time.strftime("%Y.%m.hetznerDnsUpdate.log"))
    logging.basicConfig(filename=log_filename, \
                        level=logging.INFO, \
                        format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')

    my_logger = logging.getLogger("hetznerDnsUpdate")
    
    lock_file = open("dnsUpdate.lock", "w")
    try:
        fcntl.lockf(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
         my_logger.error("Another instance is already running.")
         sys.exit(1)

    # Create an Observer that monitors the directory
    my_observer = Observer()
    
    atexit.register(stop_observer, my_observer)
    atexit.register(remove_lock_file, lock_file)
    
    # Load the configuration from the JSON file
    config_file_path = os.path.join(script_directory, 'config.json')  # Path and file name to the config file in the script directory
    named_directory, auth_api_token = load_config(config_file_path)

    # Check if the authentication API token is set
    check_auth_api_token(auth_api_token, my_logger)

    # Check if the directory exists
    check_directory(named_directory, my_logger)

    # Create an instance of the DBManager class with file path to the database
    db_file_path = os.path.join(script_directory, 'file_info.db')  # Pfad zur Datenbankdatei im Skriptverzeichnis

    my_db_manager = db_manager.DBManager(db_file_path)

    # Create the table if it doesn't exist
    my_db_manager.create_table()
    
    # Configure and start the observer
    my_observer_handler = ObserverHandler(my_db_manager, auth_api_token, named_directory, my_observer)
    my_observer.schedule(my_observer_handler, path=named_directory, recursive=False)
    
    # my_observer.schedule(ObserverHandler(my_db_manager, auth_api_token, named_directory, my_observer), path=named_directory, recursive=False)
    my_observer.start()
    observer_started = True

    try:
        while True:
            time.sleep(5)  # Adjust the monitoring interval here
    except KeyboardInterrupt:
        exit()
