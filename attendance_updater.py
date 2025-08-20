# attendance_updater.py
import re
import subprocess
import socket
import platform
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === Google Sheets Setup ===
SPREADSHEET_NAME = "Attendance Logs"
CREDENTIALS_FILE = "credentials.json"

def connect_to_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).sheet1
    return sheet


# === Ping & Subnet Detection ===
IS_WINDOWS = platform.system().lower().startswith("win")


def ping(ip: str):
    """OS-aware ping: 1 packet, short timeout, no output."""
    if IS_WINDOWS:
        cmd = ["ping", "-n", "1", "-w", "200", ip]  # Windows
    else:
        cmd = ["ping", "-c", "1", "-W", "1", ip]    # Linux
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def get_local_ip() -> str:
    """
    Get the actual local IPv4 of the container/host by opening a UDP socket.
    More reliable than gethostbyname(gethostname()).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        # Fallback—common private subnet
        ip = "192.168.1.1"
    finally:
        s.close()
    return ip


def get_local_subnet() -> str:
    """
    Best-effort local IPv4 subnet prefix, like '10.0.0.' or '192.168.1.'.
    """
    ip = get_local_ip()
    parts = ip.split(".")
    if len(parts) == 4:
        return ".".join(parts[:3]) + "."
    return "192.168.1."


def scan_subnet(base_ip_prefix: str, start: int = 1, end: int = 254):
    """Parallel ping sweep to populate ARP/neighbor cache, then wait a moment."""
    with ThreadPoolExecutor(max_workers=100) as executor:
        for i in range(start, end + 1):
            executor.submit(ping, f"{base_ip_prefix}{i}")
    # Give the ARP/neighbor table a moment to fill
    time.sleep(2)


def get_connected_ips():
    """
    Return a set of IPv4 addresses found in ARP/neighbor table.
    Supports Windows (`arp -a`) and Linux (`ip neigh` or `arp -an`).
    """
    ips = set()
    try:
        if IS_WINDOWS:
            output = subprocess.check_output("arp -a", shell=True).decode(errors="ignore")
            # Be liberal: grab all IPv4s in the output
            for ip in re.findall(r"\b\d+\.\d+\.\d+\.\d+\b", output):
                ips.add(ip)
        else:
            # Prefer IPv4-only neighbor table if available
            try:
                output = subprocess.check_output(["ip", "-4", "neigh", "show"], text=True)
                for ip in re.findall(r"\b\d+\.\d+\.\d+\.\d+\b", output):
                    ips.add(ip)
            except Exception:
                # Fallback to legacy arp
                output = subprocess.check_output("arp -an", shell=True, text=True)
                for ip in re.findall(r"\((\d+\.\d+\.\d+\.\d+)\)", output):
                    ips.add(ip)
    except Exception:
        # If anything fails, return whatever we have (maybe empty)
        pass
    return ips


# === Helpers ===
def normalize_keys(row):
    return {str(k).strip(): str(v).strip() for k, v in row.items()}


# === Core Update ===
def update_attendance():
    print("\n=== Running attendance updater ===")
    print("Timestamp:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    subnet = get_local_subnet()
    print(f"Detected Subnet: {subnet}0/24")

    print("Scanning Wi-Fi network for connected devices...")
    scan_subnet(subnet)

    print("Fetching updated ARP table...")
    connected_ips = get_connected_ips()

    print("Connecting to Google Sheet...")
    sheet = connect_to_sheet()

    # Enforce headers to avoid header mismatches
    expected = [
        "Timestamp",
        "Email address",
        "Full Name",
        "Email",
        "Department/Class",
        "Your IP Address",
        "Status",
    ]
    all_data = sheet.get_all_records(expected_headers=expected)
    records = [normalize_keys(row) for row in all_data]

    # Delete old duplicate rows (Status == "Duplicate Entry")
    print("Cleaning old duplicate entries...")
    all_rows = sheet.get_all_values()
    rows_to_delete = [i + 1 for i, row in enumerate(all_rows) if len(row) > 6 and row[6] == "Duplicate Entry"]
    for i in reversed(rows_to_delete):
        try:
            sheet.delete_rows(i)
        except Exception:
            pass

    print("Updating attendance...\n")

    # Prepare a batch of statuses for column G (starting at row 2)
    statuses = []
    messages = []
    for idx, row in enumerate(records, start=2):  # start=2 to account for header row
        ip = row.get("Your IP Address", "").strip()
        full_name = row.get("Full Name", "").strip()

        # Default when IP field is empty
        status = ""
        msg = None

        if ip:
            if ":" in ip:
                # IPv6 in sheet; this checker is IPv4-only
                status = "IPv6 (not checked)"
                msg = f"{full_name} ({ip}): IPv6 address not checked"
            elif ip in connected_ips:
                status = "Present"
                msg = f"{full_name} ({ip}): Present"
            else:
                status = "Invalid Wi-Fi"
                msg = f"{full_name} ({ip}): Invalid Wi-Fi"

        statuses.append([status])
        if msg:
            print(msg)

    # Batch update all statuses in one request
    if statuses:
        start_row = 2
        end_row = start_row + len(statuses) - 1
        update_range = f"G{start_row}:G{end_row}"
        try:
            sheet.update(update_range, statuses)
        except Exception as e:
            print(f"Batch update failed ({e}); falling back to per-cell updates.")
            # Fallback to individual updates if batch fails
            for i, val in enumerate(statuses, start=2):
                try:
                    sheet.update(f"G{i}", [val])
                except Exception:
                    pass

    print("=== Attendance updater finished ===\n")


# CLI entrypoint for local runs
def main():
    update_attendance()


if __name__ == "__main__":
    main()
