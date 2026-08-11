# Resilient DevOps Deployment Framework on GCP

> Complete setup, testing, failure-injection, recovery and viva demonstration guide.

This repository implements a lightweight resilient DevOps deployment framework for a containerized Django application running on Google Cloud Compute Engine.

## 1. Project objective

The framework demonstrates the complete deployment-to-recovery loop:

```text
Code Push -> GitHub Actions -> Docker Build -> SSH Deployment to GCP VM
          -> Docker Container -> /health/ Monitoring -> Failure Detection
          -> Container Restart -> Still Unhealthy? -> Rollback to Stable v1
          -> Health Check Passed
```

Features:
- Django + Gunicorn application
- Docker containerization
- GitHub Actions CI/CD
- GCP Compute Engine deployment
- Application-level `/health/` monitoring
- Automatic container self-healing
- Automatic rollback to `resilient-app:v1`
- Runtime state/event tracking in `status.json`

## 2. Technology stack

| Component | Technology |
|---|---|
| Application | Django |
| Application server | Gunicorn |
| Containerization | Docker |
| Cloud | Google Cloud Platform |
| Compute | Google Compute Engine VM |
| CI/CD | GitHub Actions |
| Deployment | `deploy.sh` + SSH |
| Monitoring | Python `monitor.py` |
| Health API | Django `/health/` |
| Runtime state | `status.json` |
| Source control | Git/GitHub |

## 3. Repository structure

```text
resilient-devops-framework/
├── app/
├── Dockerfile
├── requirements.txt
├── deploy.sh
├── monitor.py
├── status.json
└── .github/workflows/docker-build.yml
```

| File | Purpose |
|---|---|
| `Dockerfile` | Builds the application image |
| `deploy.sh` | Repeatable deployment on the GCP VM |
| `monitor.py` | Health monitoring, self-healing and rollback |
| `status.json` | Runtime state and recovery events |
| `docker-build.yml` | GitHub Actions CI/CD |
| `app/views.py` | Application health endpoint |

## 4. Prerequisites

For local execution:
- Git
- Python 3
- Docker (for container execution)

For the cloud demo:
- GCP Compute Engine VM
- Docker installed on VM
- SSH access
- GitHub repository
- GitHub Actions enabled
- Repository secrets configured

## 5. Clone repository

```bash
git clone https://github.com/codewithgulam/resilient-devops-framework.git
cd resilient-devops-framework
git status
```

## 6. Run locally without Docker

```bash
python3 -m pip install -r requirements.txt
python3 manage.py runserver 0.0.0.0:8000
```

In another terminal:

```bash
curl -i http://localhost:8000/health/
```

Expected:

```text
HTTP/1.1 200 OK
{"status": "healthy"}
```

Stop with `Ctrl+C`.

## 7. Docker build and run

Build:

```bash
docker build -t resilient-app:latest .
docker images | grep resilient-app
```

Run:

```bash
docker run -d \
  --name resilient-container-v2 \
  -p 8000:8000 \
  resilient-app:latest
```

Verify:

```bash
docker ps
curl -i http://localhost:8000/health/
```

Stop/remove when required:

```bash
docker stop resilient-container-v2 2>/dev/null || true
docker rm resilient-container-v2 2>/dev/null || true
```

## 8. GCP VM deployment

SSH to the VM and enter the repository:

```bash
cd ~/resilient-devops-framework
git status
docker --version
docker ps
docker images | grep resilient-app
```

The project keeps a stable rollback image:

```text
resilient-app:v1
```

## 9. Manual deployment with deploy.sh

Make it executable:

```bash
chmod +x deploy.sh
```

Run:

```bash
./deploy.sh
```

The script:
1. enters the repository
2. pulls `master`
3. builds `resilient-app:latest`
4. stops/removes previous deployment containers
5. starts `resilient-container-v2` on port 8000
6. waits for startup
7. checks `/health/`

Verify:

```bash
docker ps
curl -i http://localhost:8000/health/
```

## 10. Verify deployed image

```bash
docker inspect -f '{{.Config.Image}}' resilient-container-v2
```

Expected:

```text
resilient-app:latest
```

## 11. GitHub Actions CI/CD

Workflow:

```text
docker-build
     |
     v
deploy
     |
     v
SSH -> GCP VM -> ./deploy.sh
```

The build job checks out the repository and builds `resilient-app:test`.

The deploy job uses:

```text
GCP_VM_HOST
GCP_VM_USER
GCP_VM_SSH_KEY
```

and remotely executes:

```bash
cd ~/resilient-devops-framework && ./deploy.sh
```

### Required GitHub secrets

| Secret | Purpose |
|---|---|
| `GCP_VM_HOST` | VM host/IP |
| `GCP_VM_USER` | Linux username |
| `GCP_VM_SSH_KEY` | SSH private key |

Never commit the private key or token.

### Test CI/CD

After a source/documentation change:

```bash
git status
git add .
git commit -m "Test CI CD deployment"
git push origin master
```

Then open GitHub → **Actions** and verify:

```text
Docker Build and Deploy
├── docker-build ✓
└── deploy ✓
```

Verify on VM:

```bash
docker ps
curl -i http://localhost:8000/health/
```

## 12. Health monitoring

The monitor checks:

```text
http://127.0.0.1:8000/health/
```

Important configuration:

```python
ACTIVE_CONTAINER = "resilient-container-v2"
STABLE_IMAGE = "resilient-app:v1"
MAX_RESTARTS = 2
```

The monitoring loop waits 10 seconds between checks. A successful restart waits 15 seconds before continuing.

Run:

```bash
python3 monitor.py
```

Normal output:

```text
Health check passed
Health check passed
```

## 13. Self-healing mechanism

Recovery rule:

```text
3 consecutive health-check failures
            ↓
       restart container
            ↓
        wait 15 sec
            ↓
        check health
```

If the restart works, monitoring continues normally.

### Viva self-healing demo

Say:

> “I will now demonstrate automated self-healing. I will introduce an application failure and show that the monitoring process detects consecutive failures and automatically restarts the active container.”

Run the monitor:

```bash
python3 monitor.py
```

During the controlled failure test, expected output includes:

```text
Failure Count: 1
Failure Count: 2
Failure Count: 3
Application unhealthy. Restarting container...
resilient-container-v2
```

Then verify recovery:

```bash
docker ps
curl -i http://localhost:8000/health/
cat status.json
```

Point out:
- `HTTP/1.1 200 OK`
- `self_heal_count`
- `Container Restart Successful`
- `application_status: Healthy`

## 14. Rollback mechanism

Self-healing is the first recovery layer. The framework allows two restart attempts.

```text
Restart attempt 1
      ↓
Still unhealthy
      ↓
Restart attempt 2
      ↓
Still unhealthy
      ↓
Rollback
      ↓
resilient-app:v1
      ↓
Health check 200
```

Rollback:
1. stops active container
2. removes active container
3. starts `resilient-container-v1` from `resilient-app:v1`
4. switches the active container tracker to v1
5. records rollback state/events
6. resumes health monitoring

### Viva rollback demo

Say:

> “If restart-based recovery is unsuccessful, the framework escalates to automated rollback using the known-good v1 image.”

Run the controlled rollback/failure-injection procedure used for the project, then:

```bash
python3 monitor.py
```

Expected escalation:

```text
Application unhealthy. Restarting container...
...
Restart failed repeatedly. Rolling back...
```

Verify:

```bash
docker ps
docker inspect -f '{{.Config.Image}}' resilient-container-v1
curl -i http://localhost:8000/health/
cat status.json
```

Expected image:

```text
resilient-app:v1
```

Expected health:

```text
HTTP/1.1 200 OK
```

## 15. Failure injection for a controlled demo

For the project demonstration, failure was injected by creating a temporary broken image in which the health endpoint returned HTTP 500/unhealthy. The healthy source was restored afterwards.

**Do not leave the repository in the broken state.**

Before any failure-injection experiment, make a safety copy:

```bash
cp app/views.py /tmp/views.healthy.py
```

Confirm the healthy implementation:

```bash
grep -n -A3 "def health" app/views.py
```

Healthy implementation:

```python
def health(request):
    return JsonResponse({"status": "healthy"})
```

If you intentionally create a temporary broken test image, restore immediately after the experiment:

```bash
cp /tmp/views.healthy.py app/views.py
```

Then verify:

```bash
grep -n -A3 "def health" app/views.py
git status
```

The final repository should contain the healthy source.

## 16. Runtime status

```bash
cat status.json
```

Important fields:

| Field | Meaning |
|---|---|
| `application_status` | Current application state |
| `container_status` | Current container state |
| `restart_attempts` | Current restart counter |
| `rollback_triggered` | Whether rollback has occurred |
| `environment` | Deployment environment |
| `self_heal_count` | Successful container restart recoveries |
| `rollback_count` | Rollback operations |
| `last_event` | Latest event |
| `last_health_check` | Last successful check timestamp |
| `events` | Recent recovery history |

Counters are cumulative across demonstrations; do not interpret them as a single experiment.

## 17. Python validation

Before running `monitor.py` after changes:

```bash
python3 -m py_compile monitor.py
```

No output means the syntax check passed.

## 18. Useful Docker commands

```bash
docker ps
docker ps -a
docker images | grep resilient-app
docker logs resilient-container-v2
docker inspect -f '{{.Config.Image}}' resilient-container-v2
docker restart resilient-container-v2
docker stop resilient-container-v2
docker rm resilient-container-v2
```

If a container name is already in use:

```bash
docker rm -f resilient-container-v2
```

## 19. Troubleshooting

### Port 8000 is busy

```bash
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

Stop the container using port 8000.

### Container name conflict

```bash
docker ps -a | grep resilient-container-v2
docker rm -f resilient-container-v2
```

### Health endpoint refuses connection

```bash
docker ps
docker logs resilient-container-v2
curl -i http://localhost:8000/health/
```

### Health returns 500

```bash
docker logs resilient-container-v2
grep -n -A3 "def health" app/views.py
```

Healthy source should return HTTP 200 and `{"status": "healthy"}`.

### Monitor syntax problem

```bash
python3 -m py_compile monitor.py
```

### GitHub Actions SSH problem

Verify repository secrets and, when testing the local deployment key:

```bash
ssh -o BatchMode=yes -i ~/.ssh/github_actions_deploy localhost 'echo SSH_KEY_OK'
```

Expected:

```text
SSH_KEY_OK
```

## 20. Final viva demo — recommended order

### Demo 1 — Project

Say:

> “This repository contains my application, Docker configuration, CI/CD workflow, deployment automation, monitoring, self-healing and rollback logic.”

Open the GitHub repository.

### Demo 2 — GCP deployment

Say:

> “The application is deployed on a Google Cloud Compute Engine VM.”

Run:

```bash
docker ps
docker images | grep resilient-app
```

### Demo 3 — Health check

Say:

> “The application exposes an application-level health endpoint used by the monitoring system.”

Run:

```bash
curl -i http://localhost:8000/health/
```

Point out `HTTP/1.1 200 OK`.

### Demo 4 — CI/CD

Say:

> “A push to master triggers GitHub Actions. The Docker build job runs first and the deployment job runs after it succeeds.”

Open GitHub → Actions and show both jobs green.

### Demo 5 — Monitoring

Say:

> “The monitoring process polls the health endpoint every ten seconds.”

Run:

```bash
python3 monitor.py
```

### Demo 6 — Self-healing

Say:

> “I will now demonstrate automatic self-healing by introducing an application failure.”

Run the controlled failure procedure, then show:

```bash
docker ps
curl -i http://localhost:8000/health/
cat status.json
```

Point out the restart event and healthy final state.

### Demo 7 — Rollback

Say:

> “If restart-based recovery is unsuccessful, the system escalates to rollback and restores the known-good v1 image.”

After the controlled rollback test:

```bash
docker ps
docker inspect -f '{{.Config.Image}}' resilient-container-v1
curl -i http://localhost:8000/health/
```

Point out `resilient-app:v1` and HTTP 200.

### Demo 8 — Runtime evidence

Say:

> “The framework records recovery state and events for observability.”

Run:

```bash
cat status.json
```

Point out:

```text
application_status
container_status
self_heal_count
rollback_count
last_event
events
```

## 21. One-minute architecture explanation

> “The system starts with source code stored in GitHub. A push to the master branch triggers GitHub Actions. The first job builds the Docker image, and after successful completion the deployment job connects to the GCP Compute Engine VM over SSH and executes deploy.sh. The application runs inside a Docker container and exposes a health endpoint. monitor.py continuously checks this endpoint every ten seconds. Three consecutive failures trigger a container restart. If the application remains unhealthy after two restart attempts, the system rolls back to the stable resilient-app:v1 image. The final health check verifies that the recovered application is healthy.”

## 22. One-line answers for viva

| Question | Answer |
|---|---|
| Why Docker? | To package the application and dependencies into a repeatable runtime unit. |
| Why GCP? | To demonstrate deployment and recovery in a real cloud VM environment. |
| Why GitHub Actions? | To automate build and deployment after source changes. |
| Why health check? | To provide an application-level signal for detecting runtime failure. |
| Why three failures? | To avoid triggering recovery because of one transient failure. |
| Why restart first? | Restart is the least disruptive recovery action for a recoverable runtime failure. |
| Why rollback? | If restart cannot restore the application, the stable version is safer than repeatedly restarting a defective deployment. |
| Why v1? | It is the known-good stable image retained as the rollback target. |
| Why status.json? | To make runtime state and recovery events visible without an external database. |
| Why monitor.py? | It connects application health to Docker recovery actions. |

## 23. Final verification checklist

```bash
git status
docker images | grep resilient-app
docker ps
curl -i http://localhost:8000/health/
python3 -m py_compile monitor.py
grep -n "MAX_RESTARTS\|ACTIVE_CONTAINER\|STABLE_IMAGE" monitor.py
git log --oneline -5
```

Before the viva, verify GitHub Actions:

```text
docker-build ✓
deploy ✓
```

## 24. Security notes

Never commit:
- SSH private keys
- GitHub tokens
- passwords
- cloud credentials
- secret `.env` files

The GitHub Actions private key belongs in GitHub repository Actions secrets, not in source control.

## 25. Project outcome

```text
Automated Build              ✓
Automated Deployment         ✓
Cloud Hosting on GCP         ✓
Application Health Monitoring✓
Automatic Container Restart  ✓
Self-Healing                 ✓
Automated Rollback           ✓
Stable Version Recovery      ✓
Runtime Event Tracking       ✓
```

---

**Repository:** https://github.com/codewithgulam/resilient-devops-framework

**Project:** Resilient DevOps Deployment Framework on GCP with Automated Self-Healing and Rollback for Cloud-Native Applications
