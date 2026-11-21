
# app/lab_setup.py
import argparse
import os
import sys

from app.config import (
    Colors, cprint, run, ask, list_interfaces, is_root, iface_exists,
    is_valid_channel, LABS_DIR,
)

DNSMASQ_TEMPLATE = os.path.join(LABS_DIR, "dnsmasq.conf")
HOSTAPD_TEMPLATES = {
    "wep": os.path.join(LABS_DIR, "wep_lab", "hostapd_wep.conf"),
    "wpa": os.path.join(LABS_DIR, "wpa_lab", "hostapd_wpa.conf"),
}

# NOUVEAU : templates spécifiques au lab AirSnitch :







def _render(path, **kwargs):
    with open(path) as f:
        return f.read().format(**kwargs)


def configure_ap(interface, ssid, channel, key, mode="wep",
                 bssid=None, internet_interface=None):
    """Démarre hostapd + dnsmasq + NAT. Retourne True/False."""
    if mode not in HOSTAPD_TEMPLATES:
        print(f"[-] Mode inconnu : {mode}")
        return False

    if run("which hostapd > /dev/null 2>&1") != 0:
        print("[-] hostapd manquant. Lance : sudo /dependencies/install_deps_wpa_wep.sh")
        return False

    # 1. Génération du fichier hostapd depuis le template
    if mode == "wep":
        conf = _render(HOSTAPD_TEMPLATES[mode],
                       interface=interface, ssid=ssid,
                       channel=channel, wep_key0=key)
    else:
        conf = _render(HOSTAPD_TEMPLATES[mode],
                       interface=interface, ssid=ssid,
                       channel=channel, wpa_passphrase=key)

    os.makedirs("/etc/hostapd", exist_ok=True)
    with open("/etc/hostapd/ap.conf", "w") as f:
        f.write(conf)
    print("[*] Config écrite : /etc/hostapd/ap.conf")

    # 2. BSSID personnalisé (optionnel)
    if bssid:
        print(f"[*] Changement BSSID → {bssid}")
        run(f"ip link set {interface} down", capture=False)
        run(f"macchanger -m {bssid} {interface}", capture=False)
        run(f"ip link set {interface} up", capture=False)

    # 3. Lancer hostapd
    print("[*] Lancement hostapd...")
    run("pkill hostapd", capture=False)
    if run("hostapd -B /etc/hostapd/ap.conf", capture=False) != 0:
        print("[-] hostapd a échoué (carte incompatible ? mode AP non supporté ?)")
        return False

    # 4. IP sur l'interface AP
    print(f"[*] Attribution 192.168.10.1/24 à {interface}")
    run(f"ip addr flush dev {interface}", capture=False)
    run(f"ip addr add 192.168.10.1/24 dev {interface}", capture=False)

    # 5. dnsmasq
    dns_conf = _render(DNSMASQ_TEMPLATE, ap_interface=interface)
    with open("/etc/dnsmasq.conf", "w") as f:
        f.write(dns_conf)
    print("[*] Lancement dnsmasq...")
    run("pkill dnsmasq", capture=False)
    run("dnsmasq --conf-file=/etc/dnsmasq.conf", background=True)

    # 6. NAT
    if internet_interface:
        enable_nat(interface, internet_interface)

    print(f"[+] AP '{ssid}' actif sur {interface} (canal {channel}, mode {mode}).")
    return True


# NOUVEAU : configuration lab AirSnitch (dual-AP + bridge + ap_isolate=1)







def enable_nat(ap_interface, internet_interface):
    print("[*] Forwarding + NAT...")
    run("sysctl -w net.ipv4.ip_forward=1", capture=False)
    run(f"iptables -t nat -A POSTROUTING -o {internet_interface} -j MASQUERADE",
        capture=False)
    run(f"iptables -A FORWARD -i {ap_interface} -o {internet_interface} -j ACCEPT",
        capture=False)
    run(f"iptables -A FORWARD -i {internet_interface} -o {ap_interface} "
        f"-m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT", capture=False)


# ---------- CLI / interactif ----------

def _interactive():
    cprint("Configuration interactive du Point d'Accès", Colors.GREEN, bold=True)
    print("1. Mode WEP\n2. Mode WPA-PSK\n")
    print("3. Mode AirSnitch") 
    mode = {"1": "wep", "2": "wpa","3":"airsnitch"}[
        ask("Votre choix [1/2/3]", default="2",
            validator=lambda x: x in ("1", "2","3"))
    ]

    if mode == "airsnitch":
        _interactive_airsnitch() 
    list_interfaces()
    iface = ask("Interface AP (ex: wlan1)", default="wlan1",
                validator=iface_exists)
    inet = ask("Interface Internet (ex: eth0)", default="eth0",
               validator=iface_exists)
    ssid = ask("SSID", default="AP1")
    channel = ask("Canal (1-14)", default="6", validator=is_valid_channel)
    key = ask("Clé (WEP hex ou passphrase WPA)", default="1234567890")
    bssid = input("BSSID personnalisé (vide = aucun) : ").strip() or None

    if input("Confirmer ? (o/n) : ").strip().lower() != "o":
        print("[*] Annulé.")
        sys.exit(0)

    ok = configure_ap(iface, ssid, channel, key, mode=mode,
                      bssid=bssid, internet_interface=inet)
    sys.exit(0 if ok else 1)




#NOUVEAU : INTERACTIVE AIRSNITCH 









def _cli():
    p = argparse.ArgumentParser(description="Setup AP WEP / WPA / AirSnitch lab")
    p.add_argument("--mode", choices=["wep", "wpa", "airsnitch"], required=True)

    # Communs WEP/WPA
    p.add_argument("--interface", default=None)
    p.add_argument("--ssid", default="AP1")
    p.add_argument("--channel", default="6")
    p.add_argument("--key", default="1234567890")
    p.add_argument("--bssid", default=None)

    # AirSnitch
    p.add_argument("--ap1", default=None)
    p.add_argument("--ap2", default=None)
    p.add_argument("--bridge", default="br0")
    p.add_argument("--bridge-ip", default="192.168.10.1")
    p.add_argument("--ssid1", default="Lab-AP1")
    p.add_argument("--ssid2", default="Lab-AP2")
    p.add_argument("--channel1", default="1")
    p.add_argument("--channel2", default="6")
    p.add_argument("--password", default="1234567890")

    p.add_argument("--internet-interface", default=None)
    a = p.parse_args()

    if a.mode == "airsnitch":
        if not a.ap1 or not a.ap2:
            print("[-] --ap1 et --ap2 sont requis en mode airsnitch.")
            sys.exit(1)
        ok = configure_airsnitch_lab(
            a.ap1, a.ap2, a.bridge, a.bridge_ip,
            a.ssid1, a.ssid2, a.channel1, a.channel2,
            a.password, a.internet_interface,
        )
    else:
        if not a.interface:
            print("[-] --interface requis.")
            sys.exit(1)
        ok = configure_ap(a.interface, a.ssid, a.channel, a.key,
                          mode=a.mode, bssid=a.bssid,
                          internet_interface=a.internet_interface)
    # ▲▲▲ FIN DU BLOC ▲▲▲

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    if not is_root():
        cprint("[-] Root requis (sudo).", Colors.RED, bold=True)
        sys.exit(1)
    _cli() if len(sys.argv) > 1 else _interactive()