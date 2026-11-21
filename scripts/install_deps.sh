#!/bin/bash
set -e
sudo apt-get update
sudo apt-get install -y \
    hostapd dnsmasq iptables macchanger \
    aircrack-ng iw iproute2 wireless-tools net-tools \
    hcxtools hashcat
echo "[+] Dépendances système installées."