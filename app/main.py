
# app/main.py
import sys

from app.config import Colors, cprint, is_root


def _menu():
    print()
    cprint("=" * 55, Colors.YELLOW)
    cprint("   WiFi Pentest Toolkit — Console", Colors.GREEN, bold=True)
    cprint("=" * 55, Colors.YELLOW)
    print("  1. Setup AP (WEP / WPA)")
    print("  2. Attaque WEP")
    print("  3. Attaque WPA/WPA2")
    print("  4. Nettoyage (hostapd, dnsmasq, iptables)")
    print("  0. Quitter")
    return input("\nVotre choix : ").strip()


def _cleanup():
    from app.config import run
    print("[*] Nettoyage...")
    for p in ("hostapd", "dnsmasq", "airodump-ng", "aireplay-ng"):
        run(f"pkill {p}", capture=False)
    run("iptables -t nat -F", capture=False)
    run("iptables -F", capture=False)
    run("sysctl -w net.ipv4.ip_forward=0", capture=False)
    print("[+] Nettoyage effectué.")


def main():
    if not is_root():
        cprint("[-] Ce programme doit être exécuté en root (sudo).",
               Colors.RED, bold=True)
        sys.exit(1)

    while True:
        choice = _menu()
        try:
            if choice == "1":
                from app.lab_setup import _interactive
                _interactive()
            elif choice == "2":
                from app.attacks.wep_cracker import main as wep_main
                wep_main()
            elif choice == "3":
                from app.attacks.wpa_cracker import main as wpa_main
                wpa_main()
            elif choice == "4":
                _cleanup()
            elif choice == "0":
                print("[*] Au revoir.")
                sys.exit(0)
            else:
                print("[-] Choix invalide.")
        except KeyboardInterrupt:
            print("\n[*] Interrompu, retour au menu.")
        except SystemExit:
            print("\n[i] Terminé, retour au menu.")


if __name__ == "__main__":
    main()