# from fastapi import FastAPI
# import threading
# from hourly_tracker import start_scheduler

# app = FastAPI()

# @app.get("/")
# def home():
#     return {
#         "message": "Wi-Fi Attendance System running with background worker.",
#         "interval": "Every 1 hour"
#     }

# # Start the background scheduler in a separate thread
# threading.Thread(target=start_scheduler, daemon=True).start()
# print("✅ Background scheduler started.")

# main.py
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import os
import traceback

import attendance_updater  # must provide update_attendance()

# Interval in seconds (default 1 hour)
INTERVAL = int(os.getenv("ATTENDANCE_INTERVAL", 3600))

app = FastAPI(title="Wi-Fi Attendance Service with Scheduler")
scheduler = BackgroundScheduler()
last_run_time: str | None = None  # ISO timestamp string of last run (UTC)


def run_job():
    """Wrapper called by scheduler — updates global last_run_time then runs updater."""
    global last_run_time
    try:
        last_run_time = datetime.datetime.utcnow().isoformat()
        print(f"[{last_run_time}] Running attendance updater...")
        # call the core function that updates the sheet
        attendance_updater.update_attendance()
        print(f"[{datetime.datetime.utcnow().isoformat()}] Attendance run completed.")
    except Exception as e:
        # Keep scheduler alive on exceptions and log stacktrace
        print("Exception while running attendance_updater.update_attendance():")
        traceback.print_exc()


@app.on_event("startup")
def start_scheduler() -> None:
    """Start APScheduler and schedule the job."""
    if not scheduler.running:
        # schedule recurring job
        scheduler.add_job(
            run_job,
            "interval",
            seconds=INTERVAL,
            id="attendance_job",
            replace_existing=True,
            next_run_time=datetime.datetime.utcnow(),  # also trigger first run immediately
        )
        scheduler.start()
        print(f"✅ Scheduler started. Attendance will update every {INTERVAL} seconds.")


@app.on_event("shutdown")
def stop_scheduler() -> None:
    """Shutdown APScheduler on app shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("🛑 Scheduler shut down.")


@app.get("/")
def home():
    return {
        "message": "Wi-Fi Attendance Service running with background worker.",
        "interval_seconds": INTERVAL,
    }


@app.get("/status")
def status():
    """Returns last run time (UTC ISO) and current server time (UTC)."""
    return {
        "last_run_time": last_run_time,
        "server_time": datetime.datetime.utcnow().isoformat(),
    }


