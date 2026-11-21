import os
import re
import subprocess
import sys
import time

from app.config import (
    Colors, cprint, run, ask, list_interfaces, is_root, iface_exists,
    is_valid_mac, is_valid_channel,
)


def _menu():
    print()
    cprint("=" * 55, Colors.YELLOW)
    cprint("Airsnitch — Console", Colors.GREEN, bold=True)
    cprint("=" * 55, Colors.YELLOW)
    print("  1. Airsnitch GTK Abuse")
    print("  2. Airsnitch Gateway Bouncing")
    print("  3. Airsnitch Port stealing")
    print("  0. Quitter")
    return input("\nVotre choix : ").strip()

REQUIRED_TOOLS = ["airmon-ng", "airodump-ng", "aircrack-ng", "aireplay-ng", "iw"]


def check_tools():
    print("soon ....")


def main():
    #if not is_root():
    #    cprint("[-] Root requis.", Colors.RED, bold=True)
    #    sys.exit(1)
    #if not check_tools():
    #    cprint("[-] Tools required",Colors.RED,bold=True)
    choice = _menu()
    print(choice)

if __name__ == "__main__":
    main()