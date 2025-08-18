from fastapi import FastAPI
from contextlib import asynccontextmanager
import threading
import time
import os

from attendance_updater import update_attendance

# Interval (default = 1 hour = 3600 seconds)
INTERVAL = int(os.getenv("ATTENDANCE_INTERVAL", 3600))

def background_worker():
    while True:
        print("\n=== Running attendance updater ===")
        update_attendance()
        print("=== Attendance updater finished ===\n")
        time.sleep(INTERVAL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    thread = threading.Thread(target=background_worker, daemon=True)
    thread.start()
    print("Background worker started ✅")
    yield
    # Shutdown
    print("Shutting down background worker ❌")

app = FastAPI(lifespan=lifespan)

@app.get("/")
def home():
    return {
        "message": "Wi-Fi Attendance System running with background worker.",
        "interval_seconds": INTERVAL
    }
