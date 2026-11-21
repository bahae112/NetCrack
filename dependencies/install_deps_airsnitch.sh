#!/bin/bash
# scripts/airsnitch_setup.sh
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AIRSNITCH_DIR="${AIRSNITCH_DIR:-$PROJECT_ROOT/external/airsnitch}"

if [[ ! -d "$AIRSNITCH_DIR" ]]; then
    echo "[*] Clonage du dépôt AirSnitch dans $AIRSNITCH_DIR"
    mkdir -p "$(dirname "$AIRSNITCH_DIR")"
    # À remplacer par l'URL réelle de ton dépôt AirSnitch
    git clone https://github.com/vanhoefm/airsnitch.git "$AIRSNITCH_DIR"
else
    echo "[i] Dépôt déjà présent : $AIRSNITCH_DIR"
fi

echo "[*] Dépendances apt pour AirSnitch..."
sudo apt-get update
sudo apt-get install -y \
    libnl-3-dev libnl-genl-3-dev libnl-route-3-dev \
    libssl-dev libdbus-1-dev pkg-config build-essential net-tools \
    python3-venv rfkill git dnsmasq tcpreplay macchanger

echo "[*] Setup du dépôt (setup.sh / build.sh / pysetup.sh)..."
for s in "$AIRSNITCH_DIR/setup.sh" \
         "$AIRSNITCH_DIR/research/build.sh" \
         "$AIRSNITCH_DIR/research/pysetup.sh"; do
    if [[ -f "$s" ]]; then
        echo "[*] $s"
        ( cd "$(dirname "$s")" && bash "$(basename "$s")" )
    fi
done

echo "[+] AirSnitch prêt dans $AIRSNITCH_DIR"