# ADR-004: DevOps Infrastructure and Deployment Strategy

**Date:** 2026-05-02
**Status:** Accepted
**Deciders:** SRE / Infrastructure Team
**Scope:** Deployment platform, operational automation, and observability for Sabrika Brand Manager

---

## 1. Context

The application is functionally complete (image generation, V1 reel engine, V2 frame-analysis reel engine) and deployed. However, deployment knowledge was **ephemeral** — stored only in chat history and agent context. Every new CLI session required rediscovery of:
- Where the app is deployed (Azure VM? Container? Web App?)
- How to access it (SSH? Web UI?)
- How to restart it after code changes
- How to diagnose failures

This violates the AGENTS.md Research-First Covenant principle that **deployment state is persistent memory** [^1].

**Constraints:**
- Zero recurring SaaS costs (student budget)
- Single developer (no dedicated ops team)
- Must work from Kazakhstan (international API availability)
- Must survive across CLI sessions without re-discovery

---

## 2. Decision Drivers

| Driver | Priority | Rationale |
|--------|----------|-----------|
| **Deployment Memory** | Critical | New agents must know deployment state without re-discovery |
| **Operational Automation** | Critical | Manual SCP+SSH restart is error-prone |
| **Observability** | High | Cannot debug what you cannot see |
| **Cost** | High | Zero recurring infrastructure costs |
| **Reliability** | Medium | Single-node acceptable for 2-restaurant workload |
| **Scalability** | Low | Fixed at 2 restaurants; unlikely to grow beyond 5 |

---

## 3. Considered Options

### Option A: Azure Container Apps (ACA)
- Serverless container platform, pay-per-use
- Built-in health probes, auto-restart, scaling
- Requires Docker image build + ACR registry
- **Rejected:** Adds container complexity; free tier limited to 2 vCPU, 4GB RAM which is tight for YOLOv8 inference. Docker not currently installed on dev machine.

### Option B: Azure App Service (Linux Container)
- PaaS with built-in CI/CD from GitHub
- Managed platform, auto-patching
- **Rejected:** Free tier (F1) has 1GB RAM and 1GB disk — insufficient for YOLOv8 model loading + FFmpeg temp files. Paid tier ($54/mo Basic) violates cost constraint.

### Option C: Azure VM (Bare Metal) — CURRENT, ACCEPTED
- Full control, no abstraction overhead
- Existing VM `sabrika-app-vm` already provisioned
- Direct file system access for JSON data store and static files
- **Accepted:** Meets all constraints. VM is already running and serving traffic.

### Option D: GitHub Actions + Azure VM Self-Hosted Runner
- Automated deployment on every push
- **Rejected:** Overkill for single-developer project. Adds GitHub Actions complexity and runner maintenance. Manual deploy with `./scripts/deploy.sh` is sufficient.

### Option E: Kubernetes (AKS) / Docker Compose
- Container orchestration, declarative deployments
- **Rejected:** Massive overkill for a single-node Flask app. AKS has no free tier. Docker Compose requires Docker on VM (not installed).

---

## 4. Decision

> **Continue with Azure VM bare-metal deployment. Add operational automation (scripts), persistent deployment memory (AGENTS.md), and observability (health checks, log access).**

### 4.1 Deployment State Persistence

**AGENTS.md** at project root contains:
- VM IP, resource group, region, SSH credentials
- Quick operations (health check, SSH, restart)
- Azure resource inventory
- What is running on the VM
- Architecture diagram

This file is loaded by any agent entering the project, eliminating re-discovery cost.

### 4.2 Operational Automation

**scripts/deploy.sh**: One-command deployment
- Rsyncs code to VM (excluding generated content, logs, model weights)
- Restarts Flask app via Azure run-command (avoids SSH session kill)
- Runs health check verification
- Options: `--logs` (tail after deploy), `--check` (API verification)

**scripts/health-check.sh**: Comprehensive monitoring
- Application layer: HTTP health endpoint, API response
- Process layer: Flask process presence
- VM resources: disk usage, memory, load average
- Log health: recent error count
- Modes: single run, `--watch` (loop every 30s), `--alert` (exit 1 on failure)

**scripts/logs.sh**: Structured log access
- `--tail N`: Last N lines
- `--grep PATTERN`: Filtered search
- `--reel-report`: Extract generation trace
- `--clip-usage`: Show which clips were utilized
- `--errors`: Recent errors
- `--download`: Full log download to `./logs/`
- `--follow`: Real-time tail

### 4.3 Observability

**Current state (manual):**
- Health endpoint: `GET /api/health` returns `code_hash`, `server_time`, `status`
- Log file: `/home/sabrika/flask.log` (Flask + app logs)
- VM metrics: Available via Azure Portal or `az vm get-instance-view`

**TODO (future):**
- Azure Monitor agent for VM metrics (CPU, memory, disk)
- Log Analytics workspace for centralized log aggregation
- UptimeRobot or Pingdom free tier for external health checks
- Alert when `/api/health` non-200 for >2 minutes

### 4.4 Incident Response

**docs/operations/runbook.md** contains:
- P1: Application completely down (VM stopped, process killed, OOM)
- P2: Reel generation fails (0s output, FFmpeg errors, no scenes detected)
- P3: Frontend not loading (missing static files, cache issues)
- P4: Slow response times (CPU/memory exhaustion, YOLOv8 CPU bottleneck)
- Deployment procedures (standard, hotfix, rollback)
- Monitoring and alerting guidance

---

## 5. Consequences

### Positive
- **Persistent memory:** AGENTS.md survives across all CLI sessions; any agent knows deployment state immediately.
- **One-command deploy:** `./scripts/deploy.sh` eliminates manual SCP+SSH errors.
- **Proactive health monitoring:** `./scripts/health-check.sh` catches issues before user reports.
- **Structured log access:** `./scripts/logs.sh --reel-report` gives instant insight into generation pipeline.
- **Zero cost:** No new Azure resources; scripts run from local machine.
- **Research-backed:** Every script cites operational best practices (Google SRE Book [^2]).

### Negative
- **No auto-scaling:** VM is single-node. If load increases, manual VM resize required.
- **No CI/CD:** Deployment is manual. GitHub Actions could automate but was rejected as overkill.
- **No containerization:** Bare-metal deployment lacks reproducibility. Docker was considered but not installed on VM.
- **Flask dev server exposed directly:** No reverse proxy (nginx). Acceptable for current load but should be addressed before scaling.
- **No automated alerting:** Health checks are manual. Azure Monitor integration is TODO.

---

## 6. Alternatives Considered (Revisited)

| Option | Why Rejected | When to Reconsider |
|--------|-------------|-------------------|
| Azure Container Apps | Free tier RAM insufficient for YOLOv8 | If app is refactored to offload ML to GPU endpoint |
| Azure App Service | Free tier 1GB RAM too small | Never — paid tier violates cost constraint |
| Kubernetes (AKS) | Massive overkill for single-node app | If scaling to 10+ restaurants with team |
| GitHub Actions | Overkill for single developer | If team grows to 2+ developers |
| Docker on VM | Docker not installed; adds complexity | If reproducibility becomes critical |

---

## 7. References

[^1]: AGENTS.md § Research-First Covenant, voice-revenge-vizuara-ai
[^2]: Beyer, B., et al. (2016). Site Reliability Engineering. O'Reilly Media. Chapter 6: Monitoring Distributed Systems.
[^3]: Microsoft Azure Documentation. Azure Virtual Machines — Run Command. docs.microsoft.com/azure/virtual-machines/run-command
[^4]: docs/operations/runbook.md — SRE Incident Response Playbooks
[^5]: scripts/deploy.sh — One-Command Deployment Automation
[^6]: scripts/health-check.sh — VM and Application Health Monitoring
[^7]: scripts/logs.sh — Structured Log Access and Analysis
