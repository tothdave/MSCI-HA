import argparse
import netifaces
import os
from datetime import datetime


# Configuration: Load environment variables or set defaults
POD_NAME = os.getenv("POD_NAME", "POD_NAME")
IP_RANGES_DIR_PATH = os.getenv("IP_RANGES_DIR_PATH", "./")
IP_RANGES_FILE_NAME = os.getenv("IP_RANGES_FILE_NAME", "ip-ranges")

FILE_EXTENSION = ".csv"

current_date = datetime.now().strftime('%Y-%m-%d')

IP_RANGES_FILE_PATH = os.path.join(IP_RANGES_DIR_PATH, f"{IP_RANGES_FILE_NAME}_{current_date}{FILE_EXTENSION}")


def get_and_save_ip_ranges() -> None:

    ip_ranges: list[str] = get_ip_ranges()
    print(f"Got the following IPs: {ip_ranges}. Saving to file...")

    os.makedirs(IP_RANGES_DIR_PATH, exist_ok=True)
    save_ip_ranges(ip_ranges)


def save_ip_ranges(ip_ranges: list[str]) -> None:
    try:
        with open(IP_RANGES_FILE_PATH, "a") as file:
            for ip_range in ip_ranges:
                file.write(f"{POD_NAME},{ip_range}\n")
        print(f"IP ranges successfully saved to {IP_RANGES_FILE_PATH}")
    except Exception as e:
        print(f"Error saving IP ranges to file: {e}")


def get_ip_ranges() -> list[str]:

    ip_ranges: list[str] = []
    for interface in netifaces.interfaces():
        addresses = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in addresses:
            for addr in addresses[netifaces.AF_INET]:
                ip = addr['addr']
                netmask = addr['netmask']
                if ip and netmask:
                    ip_network = f"{ip}/{netmask_to_cidr(netmask)}"
                    ip_ranges.append(ip_network)
    return ip_ranges


def netmask_to_cidr(netmask: str) -> int:
    return sum([bin(int(octet)).count('1') for octet in netmask.split('.')])


def check_collisions(file_path: str):
    print("Check for collisions")

def main() -> None:
    parser = argparse.ArgumentParser(description="IP Tool")
    parser.add_argument("--check-collision", type=str, help="File path to check for IP collisions.")
    args = parser.parse_args()

    if args.check_collision:
        check_collisions(args.check_collision)
    else:
        print("Gathering IP ranges.")
        get_and_save_ip_ranges()

if __name__ == "__main__":
    main()