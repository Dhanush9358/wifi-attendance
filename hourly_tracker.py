from apscheduler.schedulers.background import BackgroundScheduler
from attendance_updater import update_attendance
import time
from main import ATTENDANCE_INTERVAL


def start_scheduler():
    scheduler = BackgroundScheduler()

    # Run every hour (no immediate run at startup)
    scheduler.add_job(update_attendance, 'interval', seconds=ATTENDANCE_INTERVAL)
    print(f"✅ Scheduler started. Attendance will update every {ATTENDANCE_INTERVAL} seconds.")

    scheduler.start()
    print("✅ Scheduler started. Attendance will update every hour.")

    # Keep alive loop
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

