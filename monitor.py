import requests
import subprocess
import time
import json
from datetime import datetime

URL = "http://127.0.0.1:8001/health"
CONTAINER_NAME = "resilient-container"
STABLE_IMAGE = "resilient-app:v1"
STATUS_FILE = "status.json"

restart_attempts = 0
MAX_RESTARTS = 2


def log_event(message):
    try:
        with open(STATUS_FILE, "r") as file:
            data = json.load(file)
    except:
        data = {"events": []}

    timestamp = datetime.now().strftime("%H:%M:%S")
    data.setdefault("events", [])
    data["events"].insert(0, f"[{timestamp}] {message}")

    data["events"] = data["events"][:10]

    with open(STATUS_FILE, "w") as file:
        json.dump(data, file, indent=4)


def update_status(app_status, container_status, attempts, rollback):
    try:
        with open(STATUS_FILE, "r") as file:
            data = json.load(file)
    except:
        data = {"events": []}

    data["application_status"] = app_status
    data["container_status"] = container_status
    data["restart_attempts"] = attempts
    data["rollback_triggered"] = rollback
    data["environment"] = "Local Docker"

    with open(STATUS_FILE, "w") as file:
        json.dump(data, file, indent=4)


def restart_container():
    print("Application unhealthy. Restarting container...")

    update_status("Unhealthy", "Restarting", restart_attempts, "No")
    log_event(f"Restart attempt {restart_attempts}")

    subprocess.run(["docker", "restart", CONTAINER_NAME])

    log_event("Container Restart Successful")

    time.sleep(15)


def rollback():
    print("Restart failed repeatedly. Rolling back...")

    update_status("Unhealthy", "Rollback in Progress", restart_attempts, "Yes")
    log_event("Rollback triggered")

    subprocess.run(["docker", "stop", CONTAINER_NAME])
    subprocess.run(["docker", "rm", CONTAINER_NAME])

    subprocess.run([
        "docker", "run",
        "-d",
        "--name", CONTAINER_NAME,
        "-p", "8001:8000",
        STABLE_IMAGE
    ])

    update_status("Healthy", "Running", 0, "Yes")
    log_event("Stable version restored")


while True:
    try:
        response = requests.get(URL, timeout=15)

        if response.status_code == 200:
            restart_attempts = 0
            failure_count = 0

            print("Health check passed")

            update_status(
                "Healthy",
                "Running",
                restart_attempts,
                "No"
            )

        else:
            failure_count += 1

            print(f"Failure Count: {failure_count}")

            if failure_count >= 3:
                restart_attempts += 1
                restart_container()
                failure_count = 0

    except Exception as e:

        print("ERROR:", e)

        failure_count += 1

        print(f"Failure Count: {failure_count}")
        log_event(f"Health Check Failure Detected ({failure_count})")

        if failure_count >= 3:
            restart_attempts += 1
            restart_container()
            failure_count = 0

    if restart_attempts >= MAX_RESTARTS:
        rollback()
        restart_attempts = 0

    time.sleep(10)