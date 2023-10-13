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
sudo mkdir -p /usr/local/bin/hetzerdns/

# Download files from GitHub
wget -O /usr/local/bin/hetzerdns/dnsUpdate.py https://github.com/Maker-Hub-De/CWP7-DNS-Hetzner-Update/raw/main/dnsHetznerUpdate.py
wget -O /usr/local/cwpsrv/htdocs/resources/admin/modules/dns_hetzner_update.php https://github.com/Maker-Hub-De/CWP7-DNS-Hetzner-Update/raw/main/dns_hetzner_update.php
wget -O /etc/systemd/system/hetzerDnsUpdate.service https://github.com/Maker-Hub-De/CWP7-DNS-Hetzner-Update/raw/main/hetzerDnsUpdate.service
wget -O /usr/local/bin/hetzerdns/db_manager.py.py https://raw.githubusercontent.com/Maker-Hub-De/CWP7-DNS-Hetzner-Update/main/modules/db_manager.py
wget -O /usr/local/bin/hetzerdns/hezner_dns.py https://raw.githubusercontent.com/Maker-Hub-De/CWP7-DNS-Hetzner-Update/main/modules/hezner_dns.py
wget -O /usr/local/bin/hetzerdns/observer_handler.py https://raw.githubusercontent.com/Maker-Hub-De/CWP7-DNS-Hetzner-Update/main/modules/observer_handler.py
# Check and add menu entry to 3rdparty.php
menu_entry='<li><a href="index.php?module=dns_hetzner_update"><span class="icon16 icomoon-icon-arrow-right-3"></span>Hetzner DNS Zone update</a></li>'
if ! grep -q "$menu_entry" /usr/local/cwpsrv/htdocs/resources/admin/include/3rdparty.php; then
  echo "Adding menu entry to 3rdparty.php."
  echo $menu_entry >> /usr/local/cwpsrv/htdocs/resources/admin/include/3rdparty.php
fi

# Set permissions to execute file
chmod +x /usr/local/bin/hetzerdns/dnsUpdate.py

# Enable and start the new systemd service
sudo systemctl enable hetzerDnsUpdate.service
# right now we wont want to start the service
# sudo systemctl start hetzerDnsUpdate.service

echo "Installation completed."
echo "You can start the service manually with:"
echo "sudo systemctl start hetzerDnsUpdate.service"
