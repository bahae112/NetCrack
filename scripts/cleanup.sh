#!/bin/bash
for p in hostapd dnsmasq airodump-ng aireplay-ng; do
    sudo pkill "$p" 2>/dev/null || true
done
sudo iptables -t nat -F 2>/dev/null || true
sudo iptables -F 2>/dev/null || true
sudo sysctl -w net.ipv4.ip_forward=0 >/dev/null
echo "[+] Nettoyage effectué."
