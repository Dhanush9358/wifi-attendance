from apscheduler.schedulers.background import BackgroundScheduler
from attendance_updater import update_attendance
import time
from main import ATTENDANCE_INTERVAL
from datetime import datetime

def start_scheduler():
    scheduler = BackgroundScheduler()

    # Run first immediately, then every ATTENDANCE_INTERVAL seconds
    scheduler.add_job(
        update_attendance,
        'interval',
        seconds=ATTENDANCE_INTERVAL,
        next_run_time=datetime.now()  # immediate first run
    )

    scheduler.start()
    print(f"✅ Scheduler started. Attendance will update every {ATTENDANCE_INTERVAL} seconds.")

    # Keep alive loop
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
