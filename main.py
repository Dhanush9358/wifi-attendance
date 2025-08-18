# from fastapi import FastAPI
# import threading
# import time
# import datetime
# from attendance_updater import update_attendance

# app = FastAPI()

# # Store last results
# attendance_results = {
#     "last_check": None,
#     "records": []
# }

# def run_scheduler():
#     """Run update_attendance every 1 minute in background."""
#     while True:
#         print("🔄 Running scheduled attendance check...")
#         try:
#             results = update_attendance()  # modify updater to return results
#             attendance_results["last_check"] = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
#             attendance_results["records"] = results
#         except Exception as e:
#             print(f"❌ Error in scheduler: {e}")
#         time.sleep(60)  # wait 1 minute

# # Start scheduler in background
# threading.Thread(target=run_scheduler, daemon=True).start()


# @app.get("/")
# def home():
#     return {"message": "Wi-Fi Attendance Service is running"}


# @app.get("/status")
# def status():
#     """Return the latest attendance check results."""
#     return attendance_results
