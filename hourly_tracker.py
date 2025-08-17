# import time
# import attendance_updater

# def hourly_check():
#     print("⏰ Starting hourly location check...")
#     while True:
#         attendance_updater.main()
#         print("✅ Hourly check complete. Waiting 1 hour...")
#         time.sleep(60)  # 1 hour = 3600 sec

# if __name__ == "__main__":
#     hourly_check()

import time
from datetime import datetime
import attendance_updater

def hourly_check():
    print("⏰ Starting hourly location check...")
    while True:
        print(f"\n=== Check started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
        attendance_updater.main()
        print(f"✅ Check complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. Waiting 60 seconds...\n")
        time.sleep(60)  # or any interval you want

if __name__ == "__main__":
    hourly_check()
