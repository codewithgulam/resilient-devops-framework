# Resilient DevOps Deployment Framework

## Update Log - 20 June 2026

### Overview

This update focuses on improving the reliability of the monitoring and self-healing components of the framework. Multiple test scenarios were executed to validate container recovery and automated health monitoring.

---

## Changes Implemented

### 1. Health Monitoring Improvements

* Updated monitoring endpoint from `localhost` to `127.0.0.1` for more reliable communication.
* Increased HTTP health check timeout from 5 seconds to 15 seconds.
* Added detailed exception logging for easier troubleshooting.

### 2. Failure Threshold Logic

* Introduced `failure_count` mechanism.
* Recovery actions are now triggered only after **three consecutive health check failures**.
* This prevents false-positive recovery actions caused by temporary network delays or startup latency.

### 3. Self-Healing Enhancements

* Validated automatic container restart after application failure.
* Added recovery event logging for monitoring and dashboard visibility.
* Improved restart stability by allowing additional startup time after container restart.

### 4. Rollback Workflow Validation

* Verified rollback execution after repeated recovery failures.
* Confirmed restoration of stable application image.
* Updated dashboard event timeline to reflect rollback activities.

### 5. Dashboard Improvements

* Enhanced event tracking through status.json updates.
* Added detailed monitoring events including:

  * Health Check Failure Detection
  * Restart Attempts
  * Container Recovery Events
  * Rollback Events

---

## Testing Performed

### Scenario 1: Self-Healing Validation

Test Steps:

1. Container running in healthy state.
2. Container manually stopped.
3. Monitoring service detected consecutive failures.
4. Failure threshold reached.
5. Automatic restart initiated.
6. Application recovered successfully.

Result:

* Self-healing functionality validated successfully.

### Scenario 2: Rollback Validation

Test Steps:

1. Repeated failures simulated.
2. Maximum restart threshold reached.
3. Rollback process initiated.
4. Stable image restored.

Result:

* Rollback workflow validated successfully.

---

## Current Status

Completed:

* Django Application
* Docker Containerization
* Health Monitoring
* Failure Detection
* Self-Healing Mechanism
* Rollback Mechanism
* GitHub Repository
* GitHub Actions CI Pipeline
* Monitoring Dashboard
* Local Validation Testing

Next Steps:

* GCP Deployment
* Cloud Testing
* Performance Evaluation
* MTTR Measurement
* Final Dissertation Preparation
