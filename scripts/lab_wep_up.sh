
#!/bin/bash
set -e
cd "$(dirname "$0")/.."
INTERFACE="${1:-wlan1}"
INET="${2:-eth0}"
sudo python3 -m app.lab_setup --mode wep \
    --interface "$INTERFACE" --internet-interface "$INET" \
    --ssid AP1 --channel 6 --key 1234567890