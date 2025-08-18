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
    all_data = sheet.get_all_records(expected_headers=["Timestamp", "Email address", "Full Name", "Email", "Department/Class", "Your IP Address", "Status"])
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

# import os
# import re
# import subprocess
# import socket
# import time
# from concurrent.futures import ThreadPoolExecutor
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials

# # === Google Sheets Setup ===
# SPREADSHEET_NAME = 'Attendance Logs'
# CREDENTIALS_FILE = 'credentials.json'

# def connect_to_sheet():
#     scope = [
#         "https://spreadsheets.google.com/feeds",
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive.file",
#         "https://www.googleapis.com/auth/drive"
#     ]
#     creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
#     client = gspread.authorize(creds)
#     sheet = client.open(SPREADSHEET_NAME).sheet1
#     return sheet

# # === Ping and Subnet Detection ===
# def ping(ip):
#     # Windows ping (-n), for Linux/Mac change to ["ping", "-c", "1", "-W", "1", ip]
#     subprocess.run(["ping", "-n", "1", "-w", "100", ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# def scan_subnet(base_ip="192.168.0.", start=1, end=254):
#     with ThreadPoolExecutor(max_workers=100) as executor:
#         for i in range(start, end + 1):
#             executor.submit(ping, f"{base_ip}{i}")

# def get_local_subnet():
#     local_ip = socket.gethostbyname(socket.gethostname())
#     subnet_prefix = ".".join(local_ip.split(".")[:3]) + "."
#     return subnet_prefix

# def get_connected_ips():
#     output = subprocess.check_output('arp -a', shell=True).decode()
#     return re.findall(r'(\d+\.\d+\.\d+\.\d+)\s+[\w-]+\s+dynamic', output)

# def normalize_keys(row):
#     return {str(key).strip(): str(value).strip() for key, value in row.items()}

# # === Core Attendance Update Logic ===
# def update_attendance():
#     """Run full attendance check and update Google Sheet. Returns results list."""
#     subnet = get_local_subnet()
#     print(f"📡 Detected Subnet: {subnet}0/24")
#     print("🔍 Scanning Wi-Fi network for connected devices...")
#     scan_subnet(subnet)
#     time.sleep(2)  # wait for ARP refresh

#     print("📥 Fetching updated ARP table...")
#     connected_ips = get_connected_ips()

#     print("🔗 Connecting to Google Sheet...")
#     try:
#         sheet = connect_to_sheet()
#     except Exception as e:
#         print(f"❌ Failed to connect to Google Sheets: {e}")
#         return []

#     all_data = sheet.get_all_records()
#     records = [normalize_keys(row) for row in all_data]

#     # Delete old duplicate rows
#     print("🧹 Cleaning old duplicate entries...")
#     all_rows = sheet.get_all_values()
#     rows_to_delete = [
#         i + 1 for i, row in enumerate(all_rows)
#         if len(row) > 6 and row[6] == "Duplicate Entry"
#     ]
#     for i in reversed(rows_to_delete):
#         sheet.delete_rows(i)

#     print("✏️ Updating attendance...\n")
#     results = []
#     for idx, row in enumerate(records, start=2):  # start=2 → skip headers
#         ip = row.get("Your IP Address", "").strip()
#         if not ip:
#             continue

#         status = "Present" if ip in connected_ips else "Invalid Wi-Fi"
#         try:
#             sheet.update_acell(f"G{idx}", status)
#             results.append({
#                 "name": row.get("Full Name"),
#                 "ip": ip,
#                 "status": status
#             })
#             print(f"{row.get('Full Name')} ({ip}): {status}")
#         except Exception as e:
#             print(f"❌ Failed to update row {idx} for {row.get('Full Name')}: {e}")

#     print("✅ Attendance update complete.\n")
#     return results


# def main():
#     update_attendance()


# if __name__ == "__main__":
#     main()

# import time
# import threading
# import ipaddress
# import subprocess
# from datetime import datetime
# import gspread
# from fastapi import FastAPI
# from apscheduler.schedulers.background import BackgroundScheduler

# # =====================
# # CONFIG
# # =====================
# SPREADSHEET_NAME = "Wi-Fi Attendance Form"
# WORKSHEET_NAME = "Attendance Logs"
# CHECK_INTERVAL = 60  # seconds

# # =====================
# # GLOBAL STATE
# # =====================
# last_status = {"message": "Service starting..."}
# gc = gspread.service_account(filename="credentials.json")
# sheet = gc.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)


# # =====================
# # FUNCTIONS
# # =====================
# def detect_subnet():
#     try:
#         output = subprocess.check_output("hostname -I", shell=True).decode().strip()
#         ip = output.split()[0]  # take first IP
#         net = ipaddress.IPv4Interface(ip + "/24").network
#         return str(net)
#     except Exception as e:
#         return f"Error detecting subnet: {e}"

# def scan_devices():
#     try:
#         output = subprocess.check_output("arp -n", shell=True).decode()
#         devices = []
#         for line in output.splitlines():
#             parts = line.split()
#             if len(parts) >= 2 and parts[0].count(".") == 3:  # looks like IPv4
#                 devices.append(parts[0])
#         return devices
#     except Exception as e:
#         return [f"Error scanning devices: {e}"]



# def update_attendance():
#     """Main task: detect devices + log in Google Sheet."""
#     global last_status
#     try:
#         subnet = detect_subnet()
#         devices = scan_devices()

#         now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

#         # Update Google Sheet
#         for ip in devices:
#             sheet.append_row([now, ip])

#         last_status = {
#             "timestamp": now,
#             "subnet": subnet,
#             "devices_detected": len(devices),
#             "devices": devices,
#             "message": "Attendance updated successfully",
#         }
#         print("✅ Attendance updated:", last_status)
#     except Exception as e:
#         last_status = {"message": f"Error updating attendance: {e}"}
#         print("❌", last_status)


# # =====================
# # FASTAPI APP
# # =====================
# app = FastAPI()


# @app.get("/")
# def home():
#     """Show latest status."""
#     return last_status


# # =====================
# # BACKGROUND SCHEDULER
# # =====================
# scheduler = BackgroundScheduler()
# scheduler.add_job(update_attendance, "interval", seconds=CHECK_INTERVAL)
# scheduler.start()

# # Run once at startup
# update_attendance()
