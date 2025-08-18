from fastapi import FastAPI
import threading
import time
from attendance_updater import update_attendance

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Wi-Fi Attendance System running with background worker."}

def background_worker():
    while True:
        update_attendance()
        time.sleep(3600)  # wait 1 hour

@app.on_event("startup")
def start_background_worker():
    thread = threading.Thread(target=background_worker, daemon=True)
    thread.start()
