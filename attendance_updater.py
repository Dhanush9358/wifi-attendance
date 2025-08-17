import os
import re
import subprocess
import socket
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
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).sheet1
    return sheet

# === Ping and Subnet Detection ===
def ping(ip):
    subprocess.run(["ping", "-n", "1", "-w", "100", ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def scan_subnet(base_ip="192.168.0.", start=1, end=254):
    with ThreadPoolExecutor(max_workers=100) as executor:
        for i in range(start, end + 1):
            executor.submit(ping, f"{base_ip}{i}")

def get_local_subnet():
    local_ip = socket.gethostbyname(socket.gethostname())
    subnet_prefix = ".".join(local_ip.split(".")[:3]) + "."
    return subnet_prefix

def get_connected_ips():
    output = subprocess.check_output('arp -a', shell=True).decode()
    return re.findall(r'(\d+\.\d+\.\d+\.\d+)\s+[\w-]+\s+dynamic', output)

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
    all_data = sheet.get_all_records()
    records = [normalize_keys(row) for row in all_data]

    # Delete old duplicate rows
    print("Cleaning old duplicate entries...")
    all_rows = sheet.get_all_values()
    rows_to_delete = [i + 1 for i, row in enumerate(all_rows) if len(row) > 6 and row[6] == "Duplicate Entry"]
    for i in reversed(rows_to_delete):  # Delete from bottom to top
        sheet.delete_rows(i)

    known_ips = [row.get("Your IP Address") for row in records if row.get("Your IP Address")]
    matched_ips = []

    print("Updating attendance...\n")
    for idx, row in enumerate(records, start=2):
        ip = row.get("Your IP Address", "").strip()
        status_cell = f"G{idx}"
        if not ip:
            continue

        if ip in connected_ips:
            sheet.update(status_cell, [["Present"]])
            print(f"{row.get('Full Name')} ({ip}): Present")
        else:
            sheet.update(status_cell, [["Invalid Wi-Fi"]])
            print(f"{row.get('Full Name')} ({ip}): Invalid Wi-Fi")


if __name__ == "__main__":
    main()
