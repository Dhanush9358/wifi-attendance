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

from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from attendance_updater import update_attendance
from datetime import datetime
import os


app = FastAPI()

# Read interval from environment variable (default 3600s = 1 hour)
ATTENDANCE_INTERVAL = int(os.getenv("ATTENDANCE_INTERVAL", 60))

scheduler = BackgroundScheduler()

@app.on_event("startup")
def startup_event():
    # Add job with immediate first run
    scheduler.add_job(
        update_attendance,
        "interval",
        seconds=ATTENDANCE_INTERVAL,
        next_run_time=datetime.now()  # first run immediately
    )
    scheduler.start()
    if ATTENDANCE_INTERVAL >= 60:
        print(f"✅ Scheduler started. Attendance will update every {ATTENDANCE_INTERVAL//60} minutes.")
    else:
        print(f"✅ Scheduler started. Attendance will update every {ATTENDANCE_INTERVAL} seconds.")

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
    print("🛑 Scheduler shut down.")

@app.get("/")
def home():
    return {"message": "Wi-Fi Attendance System running on FastAPI 🚀"}

# Health check for Render (prevents 405 error)
@app.head("/")
def health_check():
    return {"status": "ok"}


