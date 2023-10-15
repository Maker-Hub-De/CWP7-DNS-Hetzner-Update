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
import subprocess
import json

# Function to read the configuration file
def read_config():
    config = {}
    try:
        with open('/usr/local/bin/hetznerdns/config.json', 'r') as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        error_message = {"error": "Config file not found."}
        return error_message
    return config

# Function to check if the service is running
def is_service_running():
    try:
        # Use systemctl to check if the service is active
        result = subprocess.run(['systemctl', 'is-active', 'hetznerDnsUpdate.service'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        return result.returncode == 0
    except Exception as e:
        error_message = {"error": f"Error checking service status: {str(e)}"}
        return error_message

if __name__ == "__main__":
    config = read_config()
    
    if "error" in config:
        print(json.dumps(config, indent=4))
    else:
        service_running = is_service_running()
        # Truncate the API token to the first 5 characters
        truncated_token = config.get("apiToken", "")[:5]

        output = {
            "apiToken": truncated_token + "...",
            "directory": config.get("directory", ""),
            "active": service_running
        }
        print(json.dumps(output, indent=4))
