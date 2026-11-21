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
    print("soon ....")


def main():
    if not is_root():
        cprint("[-] Root requis.", Colors.RED, bold=True)
        sys.exit(1)
    
    print("soon...")

if __name__ == "__main__":
    main()