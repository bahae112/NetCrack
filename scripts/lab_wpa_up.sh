
#!/bin/bash
set -e
cd "$(dirname "$0")/.."
sudo python3 -m app.lab_setup --mode wpa \
    --interface "${1:-wlan1}" --internet-interface "${2:-eth0}" \
    --ssid AP1 --channel 6 --key 1234567890