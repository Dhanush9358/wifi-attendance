# Use official Python slim image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install tools needed for arp and ping
RUN apt-get update && \
    apt-get install -y net-tools iputils-ping && \
    rm -rf /var/lib/apt/lists/*

# Copy the rest of your project files
COPY . /app

# Create logs directory
RUN mkdir -p /app/logs

# Ensure Python output is unbuffered so logs show immediately
ENV PYTHONUNBUFFERED=1

# Set default command to run your hourly tracker
# CMD ["python", "-u", "hourly_tracker.py"]
CMD ["uvicorn", "attendance_updater:app", "--host", "0.0.0.0", "--port", "8000"]


# Build the Docker image
# docker build -t wifi_attendance .

# Remove any old container if it exists
# docker rm -f wifi_attendance_container

# Create new container
# docker run -d --name wifi_attendance_container wifi_attendance

# check logs in real_time
# docker logs -f wifi_attendance_container
