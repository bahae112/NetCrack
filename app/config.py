# app/config.py
from app.config import Colors, cprint
import os
import re
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABS_DIR = os.path.join(PROJECT_ROOT, "labs")
CAPTURES_DIR = os.path.join(PROJECT_ROOT, "captures")

os.makedirs(CAPTURES_DIR, exist_ok=True)


class Colors:
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
    RED = "\033[31m"; GREEN = "\033[32m"; YELLOW = "\033[33m"
    BLUE = "\033[34m"; MAGENTA = "\033[35m"; CYAN = "\033[36m"


def cprint(msg, color=Colors.RESET, bold=False, end="\n"):
    prefix = Colors.BOLD if bold else ""
    print(f"{prefix}{color}{msg}{Colors.RESET}", end=end)


def run(cmd, background=False, capture=True):
    """Exécute une commande shell. Retourne le code de retour."""
    try:
        if background:
            subprocess.Popen(cmd, shell=True,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            return 0
        res = subprocess.run(cmd, shell=True, text=True,
                             stdout=subprocess.PIPE if capture else None,
                             stderr=subprocess.PIPE if capture else None)
        if capture and res.stdout:
            print(res.stdout.strip())
        return res.returncode
    except Exception as e:
        print(f"[-] Erreur : {e}")
        return 1


def ask(prompt, default=None, validator=None):
    while True:
        q = f"{prompt} [{default}] : " if default is not None else f"{prompt} : "
        ans = input(q).strip()
        if ans == "" and default is not None:
            ans = default
        if validator and not validator(ans):
            print("[-] Valeur invalide, réessayez.")
            continue
        return ans







def show_banner():
    """Affiche le banner NetCrack coloré dans la console."""

    VERSION = "1.0.1"

    _ART = r"""
    _   _      _    ____                _    
    | \ | | ___| |_ / ___|_ __ __ _  ___| | __
    |  \| |/ _ \ __| |   | '__/ _` |/ __| |/ /
    | |\  |  __/ |_| |___| | | (_| | (__|   < 
    |_| \_|\___|\__|\____|_|  \__,_|\___|_|\_\
    """

    _TAGLINE = "WiFi Pentest Toolkit — WEP / WPA / WPA2"
    line = "=" * 60
    cprint(line, Colors.CYAN)
    for row in _ART.strip("\n").split("\n"):
        cprint(row, Colors.RED, bold=True)
    cprint(line, Colors.CYAN)
    cprint(f"  {_TAGLINE}", Colors.YELLOW, bold=True)
    cprint(f"  v{VERSION}", Colors.YELLOW, bold=True)
    cprint("  Usage légal uniquement — réseaux autorisés", Colors.DIM)
    cprint(line, Colors.CYAN)
    print()

def list_interfaces():
    print("\n[i] Interfaces réseau disponibles :")
    run("ip -o link show | awk -F': ' '{print $2}' | grep -v lo")
    print()


def is_root():
    return os.geteuid() == 0


def is_valid_mac(mac):
    return re.match(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$", mac) is not None


def is_valid_channel(ch):
    return ch.isdigit() and 1 <= int(ch) <= 14


def iface_exists(name):
    return os.path.exists(f"/sys/class/net/{name}")