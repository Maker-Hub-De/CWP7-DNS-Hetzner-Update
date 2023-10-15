# configUpdate.py
# -*- coding: utf-8 -*-
__author__     = "Mia Sophie Behrendt"
__copyright__  = "Copyright 2023, Maker-Hub.de"
__license__    = "GPL"
__version__    = "1.0.0"
__maintainer__ = "Maker-Hub-De"
__email__      = "github@maker-hub.de"
__status__     = "Development"
__date__       = "12.10.2023"

import json
import os
import sys
import time
import logging

def update_config(api_token, directory):
    try:
        # Check if an API token and an existing directory are provided
        if not api_token:
            return "Error: API token is missing"
        if not os.path.exists(directory):
            return "Error: The directory does not exist on file system"

        # Path to the directory where the script is located
        script_directory = os.path.dirname(os.path.abspath(__file__))

        # Initialize logging
        log_filename = os.path.join(script_directory, time.strftime("%Y.%m.hetznerDnsUpdate.log"))
        logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')
        my_logger = logging.getLogger("hetznerDnsUpdate")

        # Read the existing configuration from the file
        with open('/usr/local/bin/hetznerdns/config.json', 'r') as config_file:
            config = json.load(config_file)

        # Update the values
        config['apiToken'] = api_token
        config['directory'] = directory

        # Write the updated configuration back to the file
        with open('/usr/local/bin/hetznerdns/config.json', 'w') as config_file:
            json.dump(config, config_file, indent=4)

        my_logger.info("Configuration updated successfully")
        return "Successfully updated"
    except Exception as e:
        my_logger.error(f"Error updating the configuration: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python configUpdate.py <API token> <directory>")
    else:
        api_token = sys.argv[1]
        directory = sys.argv[2]
        result = update_config(api_token, directory)
        print(result)
