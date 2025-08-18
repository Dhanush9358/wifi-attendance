from fastapi import FastAPI
import threading
import time
import datetime
import attendance_updater  # your existing script (import its functions)

app = FastAPI()

# Store last check time
last_check = {"time": None}

def run_attendance_loop():
    while True:
        print("🔄 Running Wi-Fi Attendance check...")
        try:
            attendance_updater.main()  # call your updater's main function
            last_check["time"] = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        except Exception as e:
            print(f"❌ Error in updater: {e}")
        time.sleep(3600)  # wait 1 hour before next check

# Start the updater in a background thread
threading.Thread(target=run_attendance_loop, daemon=True).start()

@app.get("/")
def home():
    return {"message": "Wi-Fi Attendance Service is running"}

@app.get("/status")
def status():
    return {"last_check": last_check["time"]}
