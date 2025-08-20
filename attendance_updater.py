# import re
# import subprocess
# import socket
# import platform
# import time
# from concurrent.futures import ThreadPoolExecutor
# from datetime import datetime

# import gspread
# from oauth2client.service_account import ServiceAccountCredentials



# # === Google Sheets Setup ===
# SPREADSHEET_NAME = "Attendance Logs"
# CREDENTIALS_FILE = "credentials.json"

# def connect_to_sheet():
#     scope = [
#         "https://spreadsheets.google.com/feeds",
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive.file",
#         "https://www.googleapis.com/auth/drive",
#     ]
#     creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
#     client = gspread.authorize(creds)
#     sheet = client.open(SPREADSHEET_NAME).sheet1
#     return sheet

# # === Ping & Subnet Detection ===
# IS_WINDOWS = platform.system().lower().startswith("win")

# def ping(ip: str):
#     if IS_WINDOWS:
#         cmd = ["ping", "-n", "1", "-w", "200", ip]
#     else:
#         cmd = ["ping", "-c", "1", "-W", "1", ip]
#     subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# def get_local_subnet() -> str:
#     try:
#         local_ip = socket.gethostbyname(socket.gethostname())
#         parts = local_ip.split(".")
#         if len(parts) == 4:
#             return ".".join(parts[:3]) + "."
#     except Exception:
#         pass
#     return "192.168.1."

# def scan_subnet(base_ip_prefix: str, start: int = 1, end: int = 254):
#     with ThreadPoolExecutor(max_workers=100) as executor:
#         for i in range(start, end + 1):
#             executor.submit(ping, f"{base_ip_prefix}{i}")
#     time.sleep(2)

# def get_connected_ips():
#     ips = set()
#     try:
#         if IS_WINDOWS:
#             output = subprocess.check_output("arp -a", shell=True).decode(errors="ignore")
#             for ip, _hw, _dyn in re.findall(r"(\d+\.\d+\.\d+\.\d+)\s+([-\w]+)\s+(\w+)", output):
#                 ips.add(ip)
#         else:
#             try:
#                 output = subprocess.check_output(["ip", "neigh", "show"], text=True)
#                 for ip in re.findall(r"(\d+\.\d+\.\d+\.\d+)\s+dev", output):
#                     ips.add(ip)
#             except Exception:
#                 output = subprocess.check_output("arp -an", shell=True, text=True)
#                 for ip in re.findall(r"\((\d+\.\d+\.\d+\.\d+)\)", output):
#                     ips.add(ip)
#     except Exception:
#         pass
#     return ips

# def normalize_keys(row):
#     return {str(k).strip(): str(v).strip() for k, v in row.items()}

# # === Core Update ===
# def update_attendance():
#     print("\n=== Running attendance updater ===")
#     print("Timestamp:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

#     subnet = get_local_subnet()
#     print(f"Detected Subnet: {subnet}0/24")

#     print("Scanning Wi-Fi network for connected devices...")
#     scan_subnet(subnet)

#     print("Fetching updated ARP table...")
#     connected_ips = get_connected_ips()

#     print("Connecting to Google Sheet...")
#     sheet = connect_to_sheet()

#     expected = [
#         "Timestamp",
#         "Email address",
#         "Full Name",
#         "Email",
#         "Department/Class",
#         "Your IP Address",
#         "Status",
#     ]
#     all_data = sheet.get_all_records(expected_headers=expected)
#     records = [normalize_keys(row) for row in all_data]

#     print("Cleaning old duplicate entries...")
#     all_rows = sheet.get_all_values()
#     rows_to_delete = [i + 1 for i, row in enumerate(all_rows) if len(row) > 6 and row[6] == "Duplicate Entry"]
#     for i in reversed(rows_to_delete):
#         try:
#             sheet.delete_rows(i)
#         except Exception:
#             pass

#     print("Updating attendance...\n")
#     for idx, row in enumerate(records, start=2):
#         ip = row.get("Your IP Address", "").strip()
#         full_name = row.get("Full Name", "").strip()
#         status_cell = f"G{idx}"

#         if not ip:
#             continue

#         if ip in connected_ips:
#             sheet.update(status_cell, [["Present"]])
#             print(f"{full_name} ({ip}): Present")
#         else:
#             sheet.update(status_cell, [["Invalid Wi-Fi"]])
#             print(f"{full_name} ({ip}): Invalid Wi-Fi")

#     print("=== Attendance updater finished ===\n")

# # CLI entrypoint
# def main():
#     update_attendance()

# if __name__ == "__main__":
#     main()

# import re  -- > present if ip is correct
# import subprocess
# import socket
# import platform
# import time
# from concurrent.futures import ThreadPoolExecutor
# from datetime import datetime

# import gspread
# from oauth2client.service_account import ServiceAccountCredentials

# # === Google Sheets Setup ===
# SPREADSHEET_NAME = "Attendance Logs"
# CREDENTIALS_FILE = "credentials.json"

# def connect_to_sheet():
#     scope = [
#         "https://spreadsheets.google.com/feeds",
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive.file",
#         "https://www.googleapis.com/auth/drive",
#     ]
#     creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
#     client = gspread.authorize(creds)
#     sheet = client.open(SPREADSHEET_NAME).sheet1
#     return sheet

# # === Ping & Subnet Detection ===
# IS_WINDOWS = platform.system().lower().startswith("win")

# def ping(ip: str):
#     """Ping a given IP address to update ARP table (fire-and-forget)."""
#     try:
#         if IS_WINDOWS:
#             subprocess.run(["ping", "-n", "1", "-w", "200", ip],
#                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#         else:
#             subprocess.run(["ping", "-c", "1", "-W", "1", ip],
#                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#     except Exception:
#         pass

# def check_ip_reachable(ip_address: str) -> bool:
#     """Return True if the IP is reachable via ping, False otherwise."""
#     try:
#         subprocess.run(
#             ["ping", "-c", "1", ip_address] if not IS_WINDOWS else ["ping", "-n", "1", ip_address],
#             stdout=subprocess.DEVNULL,
#             stderr=subprocess.DEVNULL,
#             timeout=1
#         )
#         return True
#     except Exception:
#         return False

# def get_local_subnet() -> str:
#     try:
#         local_ip = socket.gethostbyname(socket.gethostname())
#         parts = local_ip.split(".")
#         if len(parts) == 4:
#             return ".".join(parts[:3]) + "."
#     except Exception:
#         pass
#     return "192.168.1."

# def scan_subnet(base_ip_prefix: str, start: int = 1, end: int = 254):
#     """Ping all IPs in the subnet to populate ARP table (fire-and-forget)."""
#     with ThreadPoolExecutor(max_workers=100) as executor:
#         for i in range(start, end + 1):
#             executor.submit(ping, f"{base_ip_prefix}{i}")
#     time.sleep(2)

# def get_connected_ips():
#     """Return a set of all IPv4 addresses in the ARP table."""
#     ips = set()
#     try:
#         if IS_WINDOWS:
#             output = subprocess.check_output("arp -a", shell=True).decode(errors="ignore")
#             for ip, _hw, _dyn in re.findall(r"(\d+\.\d+\.\d+\.\d+)\s+([-\w]+)\s+(\w+)", output):
#                 ips.add(ip)
#         else:
#             try:
#                 output = subprocess.check_output(["ip", "neigh", "show"], text=True)
#                 for ip in re.findall(r"(\d+\.\d+\.\d+\.\d+)\s+dev", output):
#                     ips.add(ip)
#             except Exception:
#                 output = subprocess.check_output("arp -an", shell=True, text=True)
#                 for ip in re.findall(r"\((\d+\.\d+\.\d+\.\d+)\)", output):
#                     ips.add(ip)
#     except Exception:
#         pass
#     return ips

# def normalize_keys(row):
#     return {str(k).strip(): str(v).strip() for k, v in row.items()}

# # === Core Update ===
# def update_attendance():
#     print("\n=== Running attendance updater ===")
#     print("Timestamp:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

#     subnet = get_local_subnet()
#     print(f"Detected Subnet: {subnet}0/24")

#     print("Scanning Wi-Fi network for connected devices...")
#     scan_subnet(subnet)

#     print("Fetching updated ARP table...")
#     connected_ips = get_connected_ips()

#     print("Connecting to Google Sheet...")
#     sheet = connect_to_sheet()

#     expected = [
#         "Timestamp",
#         "Email address",
#         "Full Name",
#         "Email",
#         "Department/Class",
#         "Your IP Address",
#         "Status",
#     ]
#     all_data = sheet.get_all_records(expected_headers=expected)
#     records = [normalize_keys(row) for row in all_data]

#     print("Cleaning old duplicate entries...")
#     all_rows = sheet.get_all_values()
#     rows_to_delete = [i + 1 for i, row in enumerate(all_rows) if len(row) > 6 and row[6] == "Duplicate Entry"]
#     for i in reversed(rows_to_delete):
#         try:
#             sheet.delete_rows(i)
#         except Exception:
#             pass

#     print("Updating attendance...\n")
#     for idx, row in enumerate(records, start=2):
#         ip = row.get("Your IP Address", "").strip()
#         full_name = row.get("Full Name", "").strip()
#         status_cell = f"G{idx}"

#         if not ip:
#             continue

#         if re.match(r"\d+\.\d+\.\d+\.\d+", ip):
#             # IPv4 address: check if reachable
#             if check_ip_reachable(ip):
#                 sheet.update(status_cell, [["Present"]])
#                 print(f"{full_name} ({ip}): Present")
#             else:
#                 sheet.update(status_cell, [["Invalid Wi-Fi"]])
#                 print(f"{full_name} ({ip}): Invalid Wi-Fi")
#         else:
#             # IPv6 or invalid format
#             sheet.update(status_cell, [["IPv6 address not checked"]])
#             print(f"{full_name} ({ip}): IPv6 address not checked")

#     print("=== Attendance updater finished ===\n")


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
    """Connect to Google Sheet and return the sheet object."""
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

def ping(ip: str) -> bool:
    """Return True if IP responds to ping."""
    if IS_WINDOWS:
        cmd = ["ping", "-n", "1", "-w", "200", ip]
    else:
        cmd = ["ping", "-c", "1", "-W", "1", ip]
    try:
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result.returncode == 0
    except Exception:
        return False

def normalize_keys(row):
    """Trim spaces from keys and values of a row dict."""
    return {str(k).strip(): str(v).strip() for k, v in row.items()}

# === Real-time Attendance Updater ===
def run_attendance_checker(interval_seconds=30):
    """
    Continuously check attendance in Google Sheet every interval_seconds.
    Marks Present / Invalid Wi-Fi dynamically.
    Keeps a log of status changes.
    """
    sheet = connect_to_sheet()
    expected_headers = [
        "Timestamp",
        "Email address",
        "Full Name",
        "Email",
        "Department/Class",
        "Your IP Address",
        "Status",
        "Status Log"
    ]

    # Keep track of last known status to log changes
    last_status = {}

    print("=== Starting real-time attendance updater ===\n")
    while True:
        print("Timestamp:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # Fetch all student data
        all_data = sheet.get_all_records(expected_headers=expected_headers)
        records = [normalize_keys(row) for row in all_data]

        def check_and_update(row_idx, row):
            ip = row.get("Your IP Address", "").strip()
            full_name = row.get("Full Name", "").strip()
            status_cell = f"G{row_idx + 2}"        # Column G
            log_cell = f"H{row_idx + 2}"           # Column H

            if not ip:
                return

            current_status = "Present" if ping(ip) else "Invalid Wi-Fi"

            # Update status cell
            sheet.update(status_cell, current_status)

            # Update log if status changed
            previous = last_status.get(ip)
            if previous != current_status:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_log = f"{timestamp}: {current_status}"
                try:
                    existing_log = sheet.cell(row_idx + 2, 8).value or ""
                    if existing_log:
                        new_log = existing_log + " | " + new_log
                except Exception:
                    pass
                sheet.update(log_cell, new_log)
                last_status[ip] = current_status

            print(f"{full_name} ({ip}): {current_status}")

        # Multithreaded ping check for all students
        with ThreadPoolExecutor(max_workers=20) as executor:
            for idx, record in enumerate(records):
                executor.submit(check_and_update, idx, record)

        print(f"Sleeping for {interval_seconds} seconds before next check...\n")
        time.sleep(interval_seconds)

# For direct CLI run
def main():
    run_attendance_checker(interval_seconds=30)

# Allow import in FastAPI without running immediately
if __name__ == "__main__":
    main()


