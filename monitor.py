import requests
import subprocess
import time
import json
from datetime import datetime

URL = "http://127.0.0.1:8000/health/"
ACTIVE_CONTAINER = "resilient-container-v2"
STABLE_IMAGE = "resilient-app:v1"
STATUS_FILE = "status.json"

restart_attempts = 0
MAX_RESTARTS = 2
failure_count = 0
self_heal_count = 0
rollback_count=0

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
        data = {}

    data["application_status"] = app_status
    data["container_status"] = container_status
    data["restart_attempts"] = attempts
    data["rollback_triggered"] = rollback
    data["environment"] = "GCP Compute Engine"

    # Preserve existing values
    data.setdefault("self_heal_count", 0)
    data.setdefault("rollback_count", 0)
    data.setdefault("last_event", "")
    data.setdefault("last_health_check", "")
    data.setdefault("events", [])

    with open(STATUS_FILE, "w") as file:
        json.dump(data, file, indent=4)
        
def restart_container():
    global ACTIVE_CONTAINER
    print("Application unhealthy. Restarting container...")

    update_status("Unhealthy", "Restarting", restart_attempts, "No")
    log_event(f"Restart attempt {restart_attempts}")

    result = subprocess.run(["docker", "restart", ACTIVE_CONTAINER])

    if result.returncode != 0:
        print("Container restart failed")
        log_event("Container Restart Failed")
        return

    try:
        with open(STATUS_FILE, "r") as file:
            data = json.load(file)

        data["self_heal_count"] = data.get("self_heal_count", 0) + 1
        data["last_event"] = "Container Restart Successful"

        with open(STATUS_FILE, "w") as file:
            json.dump(data, file, indent=4)

    except Exception as e:
        print("Error updating self-heal count:", e)

    log_event("Container Restart Successful")

    time.sleep(15)


def rollback():
    global ACTIVE_CONTAINER
    print("Restart failed repeatedly. Rolling back...")

    update_status(
        "Unhealthy",
        "Rollback in Progress",
        restart_attempts,
        "Yes"
    )

    log_event("Rollback triggered")

    try:
        with open(STATUS_FILE, "r") as file:
            data = json.load(file)

        data["rollback_count"] = data.get("rollback_count", 0) + 1
        data["last_event"] = "Rollback Triggered"

        with open(STATUS_FILE, "w") as file:
            json.dump(data, file, indent=4)

    except Exception as e:
        print("Error updating rollback count:", e)

    subprocess.run(["docker", "stop", ACTIVE_CONTAINER])
    subprocess.run(["docker", "rm", ACTIVE_CONTAINER])

    subprocess.run([
        "docker", "run",
        "-d",
        "--name", "resilient-container-v1",
        "-p", "8000:8000",
        STABLE_IMAGE
    ])

    ACTIVE_CONTAINER = "resilient-container-v1"

    update_status("Healthy", "Running", 0, "Yes")

    log_event("Stable version restored")


while True:
    try:
        response = requests.get(URL, timeout=15)

        if response.status_code == 200:
            restart_attempts = 0
            failure_count = 0

            print("Health check passed")

            try:
                with open(STATUS_FILE, "r") as file:
                    data = json.load(file)

                data["last_health_check"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data["last_event"] = "Health Check Passed"

                with open(STATUS_FILE, "w") as file:
                    json.dump(data, file, indent=4)

            except Exception as e:
                print("Error updating health check:", e)

            update_status(
                "Healthy",
                "Running",
                restart_attempts,
                data.get("rollback_triggered", "No")
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

        log_event(
            f"Health Check Failure Detected ({failure_count})"
        )

        if failure_count >= 3:
            restart_attempts += 1
            restart_container()
            failure_count = 0

    if restart_attempts >= MAX_RESTARTS:
        rollback()
        restart_attempts = 0

    time.sleep(10)
