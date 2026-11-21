#!/bin/bash
for p in hostapd dnsmasq airodump-ng aireplay-ng; do
    sudo pkill "$p" 2>/dev/null || true
done
sudo iptables -t nat -F 2>/dev/null || true
sudo iptables -F 2>/dev/null || true
sudo sysctl -w net.ipv4.ip_forward=0 >/dev/null
# NOUVEAU : nettoyer le bridge et la conf lab
sudo ip link set br0 down 2>/dev/null || true
sudo ip link delete br0 type bridge 2>/dev/null || true
sudo rm -f /etc/dnsmasq.d/airsnitch-lab.conf
echo "[+] Nettoyage effectué."