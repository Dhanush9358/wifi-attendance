import os
import re
import subprocess
import socket
import platform
from concurrent.futures import ThreadPoolExecutor
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === Google Sheets Setup ===
SPREADSHEET_NAME = 'Attendance Logs'
CREDENTIALS_FILE = 'credentials.json'

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

# === Ping and Subnet Detection ===

IS_WINDOWS = platform.system().lower().startswith("win")

def ping(ip: str):
    """OS-aware ping: 1 packet, short timeout, no output."""
    if IS_WINDOWS:
        cmd = ["ping", "-n", "1", "-w", "200", ip]     # Windows
    else:
        cmd = ["ping", "-c", "1", "-W", "1", ip]       # Linux
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def get_local_subnet() -> str:
    """
    Best-effort local IPv4 subnet prefix, like '10.158.108.' or '192.168.1.'.
    """
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
        parts = local_ip.split(".")
        if len(parts) == 4:
            return ".".join(parts[:3]) + "."
    except Exception:
        pass
    # Fallback: common private subnet
    return "192.168.1."

def scan_subnet(base_ip_prefix: str, start=1, end=254):
    """Parallel ping sweep to populate ARP cache."""
    with ThreadPoolExecutor(max_workers=100) as executor:
        for i in range(start, end + 1):
            executor.submit(ping, f"{base_ip_prefix}{i}")

def get_connected_ips():
    """
    Return a set of IPv4 addresses found in ARP/neighbor table.
    Supports both Windows (`arp -a`) and Linux (`ip neigh` or `arp -an`).
    """
    ips = set()

    try:
        if IS_WINDOWS:
            output = subprocess.check_output("arp -a", shell=True).decode(errors="ignore")
            # Example line:  192.168.1.33          00-11-22-33-44-55     dynamic
            for ip, _hw, _dyn in re.findall(r"(\d+\.\d+\.\d+\.\d+)\s+([-\w]+)\s+(\w+)", output):
                ips.add(ip)
        else:
            # Prefer ip neigh on Linux
            try:
                output = subprocess.check_output(["ip", "neigh", "show"], text=True)
                # Example: 192.168.1.5 dev eth0 lladdr aa:bb:cc:dd:ee:ff REACHABLE
                for ip in re.findall(r"(\d+\.\d+\.\d+\.\d+)\s+dev", output):
                    ips.add(ip)
            except Exception:
                # Fallback to legacy arp if ip neigh not available
                output = subprocess.check_output("arp -an", shell=True, text=True)
                # Example: ? (192.168.1.5) at aa:bb:cc:dd:ee:ff [ether] on eth0
                for ip in re.findall(r"\((\d+\.\d+\.\d+\.\d+)\)", output):
                    ips.add(ip)
    except Exception:
        pass

    return ips

def normalize_keys(row):
    return {str(key).strip(): str(value).strip() for key, value in row.items()}

def main():
    subnet = get_local_subnet()
    print(f"Detected Subnet: {subnet}0/24")

    print("Scanning Wi-Fi network for connected devices...")
    scan_subnet(subnet)

    print("Fetching updated ARP table...")
    connected_ips = get_connected_ips()

    print("Connecting to Google Sheet...")
    sheet = connect_to_sheet()
    # Enforce headers to avoid the "duplicate Timestamp" error
    all_data = sheet.get_all_records(expected_headers=["Timestamp", "Email address", "Full Name", "Email", "Department/Class", "Your IP Address", "Status",])
    records = [normalize_keys(row) for row in all_data]

    # Delete old duplicate rows
    print("Cleaning old duplicate entries...")
    all_rows = sheet.get_all_values()
    rows_to_delete = [i + 1 for i, row in enumerate(all_rows) if len(row) > 6 and row[6] == "Duplicate Entry"]
    for i in reversed(rows_to_delete):
        try:
            sheet.delete_rows(i)
        except Exception:
            pass

    print("Updating attendance...\n")
    for idx, row in enumerate(records, start=2):
        ip = row.get("Your IP Address", "").strip()
        full_name = row.get("Full Name", "").strip()
        status_cell = f"G{idx}"

        if not ip:
            continue

        # Present if their IP is in ARP/neighbor table
        if ip in connected_ips:
            sheet.update(status_cell, [["Present"]])
            print(f"{full_name} ({ip}): Present")
        else:
            sheet.update(status_cell, [["Invalid Wi-Fi"]])
            print(f"{full_name} ({ip}): Invalid Wi-Fi")
