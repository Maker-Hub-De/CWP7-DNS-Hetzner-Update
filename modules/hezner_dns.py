# -*- coding: utf-8 -*-
__author__     = "Mia Sophie Behrendt"
__copyright__  = "Copyright 2023, Maker-Hub.de"
__license__    = "GPL"
__version__    = "1.0.0"
__maintainer__ = "Maker-Hub-De"
__email__      = "github@maker-hub.de"
__status__     = "Development"
__date__       = "12.10.2023"

import requests
import json
import logging

class HeznerDNS:
    def __init__(self, auth_api_token, logger=None):
        self.auth_api_token = auth_api_token
        self.logger = logger if logger else logging.getLogger("HeznerDNS")

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

    def update_zone_from_file(self, zone_id, domain, file_path):
        # Use an absolute path to the file
        file_path = os.path.abspath(file_path)
        
        if not os.path.exists(file_path):
            logging.error(f"File {file_path} not found.")
            return False
                
        # Send an HTTP request to transmit the modified file
        print(f"Open file {file_path} for read")
        with open(file_path, 'rb') as file:

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