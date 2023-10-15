# -*- coding: utf-8 -*-
__author__     = "Mia Sophie Behrendt"
__copyright__  = "Copyright 2023, Maker-Hub.de"
__license__    = "GPL"
__version__    = "1.0.0"
__maintainer__ = "Maker-Hub-De"
__email__      = "github@maker-hub.de"
__status__     = "Development"
__date__       = "12.10.2023"

import logging
import os
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from modules.hetzner_dns import HetznerDNS

class ObserverHandler(FileSystemEventHandler):
    def __init__(self, db_manager, auth_api_token, directory, observer, logger=None):
        super(ObserverHandler, self).__init__()
        self.db_manager = db_manager
        self.auth_api_token = auth_api_token
        self.directory = directory
        self.observer = observer
        self.logger = logger if logger else logging.getLogger("MyObserverHandler")

    def on_created(self, event):
        if event.is_directory:
         return
        check_4_changes()

    def on_deleted(self, event):
        if event.is_directory:
         return
        check_4_changes()

    def on_modified(self, event):
        if event.is_directory:
         return
        check_4_changes()

    def check_4_changes(self):
        # Stop the observer temporarily
        self.observer.unschedule_all()

        current_check_time = datetime.now().timestamp()
        hezner_dns = HetznerDNS(self.auth_api_token)

        file_list = os.listdir(self.directory)
        for file_name in file_list:
            # Use an absolute path to the file
            file_path = os.path.abspath(os.path.join(self.directory, file_name))
            
            if not file_name.endswith('.db') \
            or not os.path.isfile(file_path) \
            or file_name == "hydrogen.ns.hetzner.com.db" \
            or file_name == "oxygen.ns.hetzner.com.db"\
            or file_name == "helium.ns.hetzner.com.db":
                # File/directory is not relevant; Dosen't need a log entry
                continue
            
            if not os.path.exists(file_path):
                self.logger.error(f"File {file_path} not found.")
                continue

            last_modified_file = int(os.path.getmtime(file_path))
            last_modified_db, last_checked = self.db_manager.get_file_info(file_name)

            print(f"Änderung Datei: {last_modified_file}")
            print(f"Änderung db: {last_modified_db}")
            print(f"Check db: {last_checked}")

            if last_modified_db == last_modified_file:
                # Just update the check time
                print("Just update the check time")
                if not self.db_manager.update_file_info(file_name, last_modified_file, current_check_time):
                    self.logger.error("Could not update file {file_name} in database.")
                    continue # Continue to the next file
                    
            if last_checked == None: # No entry found; it could be a new zone
                print("No entry found; it could be a new zone")
                domain = hezner_dns.get_domain(file_name)
                # Try to get a zone ID; the zone may already exist
                zone_id = hezner_dns.get_zone_id(domain)
                if zone_id == None:  # We don't have an existing zone
                    domain = hezner_dns.create_zone(domain)
                if zone_id == None: # Now we schould have a zone id; if not go on
                    self.logger.error("Could not create a new zone")
                    continue  # Continue to the next file

                # Updating the zone data
                hezner_dns.update_zone_from_file(zone_id, domain, file_path)
                # Insert into the database
                if not self.db_manager.insert_file_info(file_name, last_modified_file, current_check_time
                    self.logger.error("Could not insert file {file_name} in datagbase.")
                    continue # Continue to the next file
            # changes that younger then last check and the last check scould be at least 2 seconds in the past   
            elif last_modified_file > last_checked \
            and  last_modified_file != last_modified_db \
            and  last_checked < current_check_time - 2:
                print("Found a changed file")            
                # Found a changed file
                domain = hezner_dns.get_domain(file_name)
                # Try to get a zone ID; the zone may already exist
                zone_id = hezner_dns.get_zone_id(domain)
                if zone_id == None: # Now we schould have a zone id; if not go on
                    domain = hezner_dns.create_zone(domain)

                if zone_id == None: # Now we need to have a zone_id
                    self.logger.error("Could not create new zone")
                    continue # Continue to the next file

                # Updating the zone data
                hezner_dns.update_zone_from_file(zone_id, domain, file_name)
                # Updating the database
                if not self.db_manager.update_file_info(file_name, last_modified_file, current_check_time):
                    self.logger.error("Could not update file {file_name} in datagbase.")
                    continue # Continue to the next file

            else:
                # Just update the check time
                print("Just update the check time")      
                if not self.db_manager.update_file_info(file_name, last_modified_file, current_check_time):
                    self.logger.error("Could not update file {file_name} in datagbase.")
                    continue # Continue to the next file

        # Now checking the files in the database which weren't updated
        # That could happen if the file was deleted
        # First, get all relevant files
        files_in_db = self.db_manager.get_files_not_checked_since(current_check_time)
        
        if not files_in_db:
            return
        
        for file_name in files_in_db:
            # Use an absolute path to the file
            print(file_name[0])
            file_path = os.path.abspath(os.path.join(self.directory, file_name[0]))
                           
            # Check if the file still exists on the file system
            if not os.path.exists(file_path):
            
                # File was deleted
                domain = hezner_dns.get_domain(file_name[0])
                zone_id = hezner_dns.get_zone_id(domain)
                if zone_id:
                     # We have to delete the zone
                    if not hezner_dns.delete_zone(domain):
                        self.logger.error(f"Could not delete zone {domain} from Hetzner DNS.")
                        continue  # Continue to the next file
                    if not self.db_manager.delete_file_info(file_name[0]):
                        self.logger.error(f"Could not delete file {file_name[0]} from database.")
                        continue  # Continue to the next file

        # Start the observer again
        self.observer.schedule(self, path=self.directory, recursive=False)
