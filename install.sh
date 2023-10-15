#!/bin/bash
echo "Installing Addon: Update DNS zone data on Hetzner name server via API"

# Check if wget is installed; if not, install it
if ! command -v wget &> /dev/null; then
  echo "Wget is not installed. Installing it."
  sudo dnf install wget -y
fi

# Install watchdog if not already installed
if ! command -v watchdog &> /dev/null; then
  echo "Watchdog is not installed. Installing it."
  sudo dnf install python3-watchdog -y
fi

# Creating directory
sudo mkdir -p /usr/local/bin/hetznerdns/
sudo mkdir -p /usr/local/bin/hetznerdns/modules/

# Download python program from GitHub
sudo wget -O /usr/local/bin/hetznerdns/hetznerDnsUpdate.py         https://raw.githubusercontent.com/Maker-Hub-De/CWP7-DNS-Hetzner-Update/main/hetznerDnsUpdate.py
sudo wget -O /usr/local/bin/hetznerdns/config.json                 https://raw.githubusercontent.com/Maker-Hub-De/CWP7-DNS-Hetzner-Update/main/config.json
sudo wget -O /usr/local/bin/hetznerdns/configGet.py                https://raw.githubusercontent.com/Maker-Hub-De/CWP7-DNS-Hetzner-Update/main/configGet.py
sudo wget -O /usr/local/bin/hetznerdns/configUpdate.py             https://raw.githubusercontent.com/Maker-Hub-De/CWP7-DNS-Hetzner-Update/main/configUpdate.py
sudo wget -O /usr/local/bin/hetznerdns/modules/__init__.py         https://raw.githubusercontent.com/Maker-Hub-De/CWP7-DNS-Hetzner-Update/main/modules/__init__.py
sudo wget -O /usr/local/bin/hetznerdns/modules/db_manager.py       https://raw.githubusercontent.com/Maker-Hub-De/CWP7-DNS-Hetzner-Update/main/modules/db_manager.py
sudo wget -O /usr/local/bin/hetznerdns/modules/hetzner_dns.py      https://raw.githubusercontent.com/Maker-Hub-De/CWP7-DNS-Hetzner-Update/main/modules/hetzner_dns.py
sudo wget -O /usr/local/bin/hetznerdns/modules/observer_handler.py https://raw.githubusercontent.com/Maker-Hub-De/CWP7-DNS-Hetzner-Update/main/modules/observer_handler.py

# Set permissions
sudo chmod 900 /usr/local/bin/hetznerdns/hetznerDnsUpdate.py
sudo chmod 700 /usr/local/bin/hetznerdns/config.json
sudo chmod 705 /usr/local/bin/hetznerdns/configGet.py
sudo chmod 705 /usr/local/bin/hetznerdns/configUpdate.py
sudo chmod 700 /usr/local/bin/hetznerdns/modules/__init__.py
sudo chmod 700 /usr/local/bin/hetznerdns/modules/db_manager.py
sudo chmod 700 /usr/local/bin/hetznerdns/modules/hetzner_dns.py
sudo chmod 700 /usr/local/bin/hetznerdns/modules/observer_handler.py

# Add service user
sudo useradd -r -M -s /sbin/nologin hetznerdnsuser

# Set owner
sudo chown -R hetznerdnsuser: /usr/local/bin/hetznerdns/

# Donload plugin page and make it avalible
wget -O /usr/local/cwpsrv/htdocs/resources/admin/modules/hetznerDnsUpdate.php https://github.com/Maker-Hub-De/CWP7-DNS-Hetzner-Update/raw/main/hetznerDnsUpdate.php

# Check and add menu entry to 3rdparty.php
menu_entry='<li><a href="index.php?module=hetznerDnsUpdate"><span class="icon16 icomoon-icon-arrow-right-3"></span>Hetzner DNS Zone update</a></li>'
if ! grep -q "$menu_entry" /usr/local/cwpsrv/htdocs/resources/admin/include/3rdparty.php; then
  echo "Adding menu entry to 3rdparty.php."
  echo $menu_entry >> /usr/local/cwpsrv/htdocs/resources/admin/include/3rdparty.php
fi

# Downloading service
wget -O /etc/systemd/system/hetznerDnsUpdate.service https://github.com/Maker-Hub-De/CWP7-DNS-Hetzner-Update/raw/main/hetznerDnsUpdate.service

# Enable the new systemd service
sudo systemctl enable hetznerDnsUpdate.service

# right now we wont want to start the service
# sudo systemctl start hetznerDnsUpdate.service

echo "Installation completed."
echo "You can start the service manually with:"
echo "sudo systemctl start hetznerDnsUpdate.service"
