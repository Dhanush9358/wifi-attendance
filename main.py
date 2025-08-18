from fastapi import FastAPI
import threading
from hourly_tracker import start_scheduler

app = FastAPI()

@app.get("/")
def home():
    return {
        "message": "Wi-Fi Attendance System running with background worker.",
        "interval": "Every 1 hour"
    }

# Start the background scheduler in a separate thread
threading.Thread(target=start_scheduler, daemon=True).start()
print("✅ Background scheduler started.")
