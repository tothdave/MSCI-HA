import argparse
import netifaces
import ipaddress
import os
import pandas as pd
import logging
from datetime import datetime
from itertools import combinations
from filelock import FileLock, Timeout


# Configuration: Load environment variables or set defaults
POD_NAME = os.getenv("POD_NAME", "POD_NAME")
IP_RANGES_DIR_PATH = os.getenv("IP_RANGES_DIR_PATH", "./")
IP_RANGES_FILE_NAME = os.getenv("IP_RANGES_FILE_NAME", "ip-ranges")
COLLISIONS_DIR_PATH = os.getenv("COLLISIONS_DIR_PATH", "./")
COLLISIONS_FILE_NAME = os.getenv("COLLISIONS_FILE_NAME", "collisions")
LOG_LEVEL = os.getenv('LOGLEVEL', 'INFO').upper()

FILE_EXTENSION = ".csv"

current_date = datetime.now().strftime('%Y-%m-%d')

IP_RANGES_FILE_PATH = os.path.join(IP_RANGES_DIR_PATH, f"{IP_RANGES_FILE_NAME}_{current_date}{FILE_EXTENSION}")
COLLISIONS_RESULT_FILE_PATH = os.path.join(COLLISIONS_DIR_PATH, f"{COLLISIONS_FILE_NAME}_{current_date}{FILE_EXTENSION}")

LOCK_FILE_PATH = os.path.join(IP_RANGES_DIR_PATH, f"{IP_RANGES_FILE_NAME}.lock")
file_lock = FileLock(LOCK_FILE_PATH, timeout=10)


# Logging configuration
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)


def get_and_save_ip_ranges() -> None:
    """
    Fetches and saves IP ranges to a file.
    """

    ip_ranges: list[str] = get_ip_ranges()
    logging.info(f"Got the following IPs: {ip_ranges}. Saving to file...")

    os.makedirs(IP_RANGES_DIR_PATH, exist_ok=True)

    try:
        with file_lock:
            save_ip_ranges(ip_ranges)
    except Timeout as e:
        logging.error(f"Failed to acquire file lock: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        if file_lock.is_locked:
            file_lock.release()


def save_ip_ranges(ip_ranges: list[str]) -> None:
    """
    Saves the given IP ranges to a file.

    :param ip_ranges: List of IP ranges to save.
    """

    try:
        with open(IP_RANGES_FILE_PATH, "a") as file:
            for ip_range in ip_ranges:
                file.write(f"{POD_NAME},{ip_range}\n")
        logging.info(f"IP ranges successfully saved to {IP_RANGES_FILE_PATH}")
    except Exception as e:
        logging.error(f"Error saving IP ranges to file: {e}")


def get_ip_ranges() -> list[str]:
    """
    Retrieves IP ranges from system interfaces.

    :return: A list of IP ranges in CIDR format.
    """

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
    """
    Converts netmask to CIDR notation.
    """

    return sum([bin(int(octet)).count('1') for octet in netmask.split('.')])


def check_collisions(file_path: str) -> pd.DataFrame:
    """
    Reads a flat file containing container IP ranges and checks for collisions.

    :param file_path: Path to the flat file containing IP ranges.
    :return: DataFrame containing colliding IP ranges and container identifiers.
    """

    try:
        df = pd.read_csv(file_path, header=None, names=["container_id", "ip_range"])

        df["network"] = df["ip_range"].apply(lambda x: ipaddress.ip_network(x, strict=False))

        collisions = []
        for (i, row1), (j, row2) in combinations(df.iterrows(), 2):
            if row1["network"].overlaps(row2["network"]):
                collisions.append({
                    "network1": str(row1["network"]),
                    "container1": row1["container_id"],
                    "network2": str(row2["network"]),
                    "container2": row2["container_id"]
                })

        collision_df = pd.DataFrame(collisions)

        if not collision_df.empty:
            logging.info(f"Collisions found:\n{collision_df}")
            
            os.makedirs(COLLISIONS_DIR_PATH, exist_ok=True)
            collision_df.to_csv(COLLISIONS_RESULT_FILE_PATH, index=False)
            logging.info(f"Collisions saved to {COLLISIONS_RESULT_FILE_PATH}")
        else:
            logging.info("No collisions detected.")

        return collision_df

    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return pd.DataFrame()

def main() -> None:
    """
    Main function to parse arguments and run the corresponding function.
    """

    parser = argparse.ArgumentParser(description="IP Tool")
    parser.add_argument("--check-collision", type=str, help="File path to check for IP collisions.")
    args = parser.parse_args()

    if args.check_collision:
        logging.info(f"Checking collisions for file: {args.check_collision}")
        check_collisions(args.check_collision)
    else:
        logging.info("Gathering IP ranges.")
        get_and_save_ip_ranges()

if __name__ == "__main__":
    main()