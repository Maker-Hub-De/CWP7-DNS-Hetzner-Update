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
        self.check_4_changes()

    def on_deleted(self, event):
        if event.is_directory:
            return
        self.check_4_changes()

    def on_modified(self, event):
        if event.is_directory:
            return
        self.check_4_changes()

    def check_4_changes(self):
        # Stop the observer temporarily
        self.observer.unschedule_all()

        current_check_time = datetime.now().timestamp()
        hetzner_dns = HetznerDNS(self.auth_api_token)

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
                # That should never happen, because we read the directory directly before but who knows :-)
                self.logger.error(f"File {file_path} not found.")
                continue

            last_modified_file = int(os.path.getmtime(file_path))
            last_modified_db, last_checked = self.db_manager.get_file_info(file_name)

            # Checking if the file was ever checked
            if last_checked == None:
                # The file was never checked => it could be a new zone or a file that was never checked before
                # Getting domain from file name
                domain = hetzner_dns.get_domain(file_name)
                
                # Try to get a zone ID; the zone may already exist and only the database entry was missing
                zone_id = hetzner_dns.get_zone_id(domain)
                
                if zone_id == None:  # We don't have an existing zone
                    domain = hetzner_dns.create_zone(domain)
                    
                if zone_id == None: # Now we should have a zone id; if not, there is a problem in the DNS app.
                    self.logger.error("Could not create a new zone")
                    continue  # Continue to the next file

                # Now we can updating the zone data
                if not hetzner_dns.update_zone_from_file(zone_id, domain, file_name):
                    # The log will be written within the method update_zone_from_file
                    # we just need to contiue to not update the database and can try it the next time
                    continue  # Continue to the next file
                
                # Adding new file to the database
                if not self.db_manager.insert_file_info(file_name, last_modified_file, current_check_time)
                    self.logger.error(f"Could not insert file {file_name} in database.")
                    continue # Continue to the next file
                
            # Checking if the file was modified
            elif last_modified_db == last_modified_file:
                # No modification found => just update the check time
                print("Just update the check time")
                if not self.db_manager.update_file_info(file_name, last_modified_file, current_check_time):
                    self.logger.error("Could not update file {file_name} in database.")
                    continue # Continue to the next file

            # changes that younger then last check and the last check scould be at least 2 seconds in the past
            # We checking for the two seconds, because the dns update from the CWP7 frontend trigger several
            # changes in the directory but we want only to send one update. Dont SPAM the API :-)
            elif last_modified_file > last_checked \
            and  last_modified_file != last_modified_db \
            and  last_checked < current_check_time - 2:        
                # Found a changed file that is relevant
                domain = hetzner_dns.get_domain(file_name)
                
                # Try to get a zone ID; the zone may already exist
                zone_id = hetzner_dns.get_zone_id(domain)
                
                if zone_id == None: # Now we schould have a zone id; if not go on
                    domain = hetzner_dns.create_zone(domain)

                if zone_id == None: # Now we should have a zone id; if not, there is a problem in the DNS app.
                    self.logger.error("Could not create new zone")
                    continue # Continue to the next file

                # Updating the zone data
                hetzner_dns.update_zone_from_file(zone_id, domain, file_name)
                if not hetzner_dns.update_zone_from_file(zone_id, domain, file_name):
                    # The log will be written within the method update_zone_from_file
                    # we just need to contiue to not update the database and can try it the next time
                    continue  # Continue to the next file
                    
                # Updating the database
                if not self.db_manager.update_file_info(file_name, last_modified_file, current_check_time):
                    self.logger.error(f"Could not update file {file_name} in database.")
                    continue # Continue to the next file

            else:
                # In any other case Just updating the check time. I have no idea which case it could be but let us make the program robust :-)   
                if not self.db_manager.update_file_info(file_name, last_modified_file, current_check_time):
                    self.logger.error(f"Could not update file {file_name} in database.")
                    continue # Continue to the next file

        # Now checking the files in the database which weren't updated
        # That could happen if the file was deleted
        # First, get all relevant files
        files_in_db = self.db_manager.get_files_not_checked_since(current_check_time)

        # All files where updated => Nothing to do
        if not files_in_db:
            return

        # Checking all entries in the database
        for file_name in files_in_db:
            # Use an absolute path to the file
            file_path = os.path.abspath(os.path.join(self.directory, file_name[0]))
                           
            # Check if the file still exists on the file system
            if not os.path.exists(file_path): # File was deleted
                # Getting domain from filename
                domain = hetzner_dns.get_domain(file_name[0])
                
                # Seaching the zone id
                zone_id = hetzner_dns.get_zone_id(domain)
                
                if zone_id: # We found a zone id
                     # Deleting the zone id
                    if not hetzner_dns.delete_zone(domain):
                        self.logger.error(f"Could not delete zone {domain} from Hetzner DNS.")
                        continue  # Continue to the next file
                # It doesn't matter if we found a zone id, we will delete the file entry in the data
                # base because we assuming that the api is working and we getting the data from it
                if not self.db_manager.delete_file_info(file_name[0]):
                    self.logger.error(f"Could not delete file {file_name[0]} from database.")
                        continue  # Continue to the next file

        # Start the observer again
        self.observer.schedule(self, path=self.directory, recursive=False)
