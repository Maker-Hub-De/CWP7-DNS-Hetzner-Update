import time
import requests
import os
import json
import logging

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

named_directory = ""
auth_api_Token = ""
log_filename = ""

# Funktion zum Laden der Konfiguration aus der JSON-Datei
def load_config(filename):
    global auth_api_Token
    global named_directory
    
    if not os.path.exists(filename):
        logging.error("Configuration file '{}' dosen't exist. Script will be stopped".format(filename))
        exit()

    with open(filename, 'r') as config_file:
        config = json.load(config_file)
        # Extrahiere die Werte aus der Konfiguration
        # directory to watch over
        named_directory = config.get('directory', '/var/named')
        # Authentication Token for the Herzner API
        auth_api_Token = config.get('apiToken', '')

# Überprüfen, ob der Token noch vorhanden ist
def check_auth_api_Token():
    if auth_api_Token == "":
        logging.error("Authentifizierungs-Token is missing. Script will be stopped")
        exit()

# Überprüfe, ob das Verzeichnis existiert
def check_directory():
    global named_directory
    
    if not os.path.exists(named_directory):
        logging.error("Directory '{}' dosen't exist. Script will be stopped".format(named_directory))
        exit()

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if '.db' in event.src_path:
            domain    = self.get_domain(event.src_path)
            file_name = self.get_file_name(event.src_path)

            # Überprüfen ob der auth api token gesetzt ist
            check_auth_api_Token()

            zone_id = self.get_zone_id(domain)

            if zone_id == "":
                # Create new zone
                zone_id = self.create_zone(domain)

            if zone_id:
                self.update_zone_from_file(zone_id, domain, file_name)

    def get_file_name(self, src_path):
        # Deleting all after .db
        file_name = src_path.rsplit('.db', 1)[0]

        # Replace "/." with "/" 
        file_name = file_name.replace('/.', '/')

        # Add file ending to file name
        file_name = file_name + '.db'

        return file_name

    def get_domain(self, src_path):
        # Deleting all after .db
        domain = src_path.rsplit('.db', 1)[0]
        domain = domain.rsplit('/.', 1)[1]
        return domain

    def get_zone_id(self, domain):
        try:
            response = requests.get(
                url="https://dns.hetzner.com/api/v1/zones",
                headers={
                    "Auth-API-Token": auth_api_Token,
                },
                params={
                    "search_name": domain
                }
            )

            if response.status_code == 200:
                # JSON-Daten analysieren
                print(response.content)
                json_object = json.loads(response.content)

                # Zone-ID abrufen
                zone_id = json_object["zones"][0]["id"]
                return zone_id
            elif response.status_code == 404:
                print(response.content)
                return ""
        except requests.exceptions.RequestException:
                return ""

    def create_zone(self, domain):
        print("searching zone")
        try:
            response = requests.post(
                url="https://dns.hetzner.com/api/v1/zones",
                headers={
                    "Content-Type": "application/json",
                    "Auth-API-Token": auth_api_Token,
                },
                data=json.dumps({
                    "name": domain,
                    "ttl": 11400
                })
            )

            if response.status_code == 200:
                print(response.content)
                # JSON-Daten analysieren
                json_object = json.loads(response.content)

                # Zone-ID abrufen
                zone_id = json_object["zone"]["id"]
                return zone_id
            elif response.status_code == 404:
                # try again to get the zone id
                zone_id = self.get_zone_id(domain)
                return zone_id
            elif response.status_code == 422:
                # try again to get the zone id
                zone_id = self.get_zone_id(domain)
                return zone_id
        except requests.exceptions.RequestException:
                return ""

    def update_zone_from_file(self, zone_id, domain, file_name):
        print("update_zone_from_file")
        # HTTP-Anforderung senden, um die geänderte Datei zu übertragen
        with open(file_name, 'rb') as file:

            # Reading bytes from the file and convert it to a string
            file_content = file.read().decode('utf-8')

            # Creating request data
            request_data = f"$ORIGIN {domain}.\n{file_content}"
            try:
                response = requests.post(
                    url=f"https://dns.hetzner.com/api/v1/zones/{zone_id}/import",
                    headers={
                        "Content-Type": "text/plain",
                        "Auth-API-Token": auth_api_Token,
                    },
                    data=request_data
                )
                print('Response HTTP Status Code: {status_code}'.format( status_code=response.status_code))
                print('Response HTTP Response Body: {content}'.format( content=response.content))
            except requests.exceptions.RequestException:
                print('HTTP Request failed')

# Ab hier beginnt der Hauptteil

# Initialisiere das Logging
log_filename = time.strftime("/usr/local/bin/hetzerdns/%Y-%m.hetznerDnsUpdate.log")

logging.basicConfig(filename=log_filename, level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s: %(message)s')

 # Lade die Konfiguration aus der JSON-Datei
load_config('/usr/local/bin/hetzerdns/config.json')

# Überprüfen ob der auth api token gesetzt ist
check_auth_api_Token()

# Überprüfe, ob das Verzeichnis existiert
check_directory()

# Einen Observer erstellen, der das Verzeichnis überwacht
observer = Observer()
observer.schedule(MyHandler(), path=named_directory, recursive=False)

# Observer starten
observer.start()

try:
    while True:
        time.sleep(5)  # Das Programm am Laufen halten
except KeyboardInterrupt:
    observer.stop()

observer.join()  # Warten, bis der Observer beendet ist
