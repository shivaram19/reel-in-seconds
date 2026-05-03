# SRE Runbook: Sabrika Brand Manager

**Document ID:** OP-001  
**Version:** 1.0  
**Last Updated:** 2026-05-02  
**Owner:** SRE / DevOps  
**Scope:** Incident response, deployment procedures, and operational playbooks for the Azure VM deployment of Sabrika Brand Manager.

---

## 1. Service Overview

| Attribute | Value |
|-----------|-------|
| Service Name | Sabrika Brand Manager |
| Purpose | Instagram content automation for restaurant social media |
| Deployment | Azure VM `sabrika-app-vm` @ `20.125.62.241:5000` |
| Tech Stack | Flask (Python 3.10), Pillow, YOLOv8, OpenCV, FFmpeg |
| Data Store | JSON files (`data/restaurants.json`) |
| File Storage | `static/{generated,logos,reels,thumbnails,uploads}/` |
| Process Model | Single-node Flask dev server (`python3 app.py` via nohup) |
| Health Endpoint | `GET /api/health` |

---

## 2. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AZURE (sabrika-rg)                           │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  VM: sabrika-app-vm (westus2)                               │    │
│  │  IP: 20.125.62.241                                          │    │
│  │  OS: Ubuntu                                                 │    │
│  │                                                             │    │
│  │  ┌─────────────┐    ┌─────────────────────────────────┐     │    │
│  │  │  nginx      │    │  Flask (port 5000)              │     │    │
│  │  │  (NONE)     │    │  ├─ /api/health                 │     │    │
│  │  │             │    │  ├─ /api/restaurants            │     │    │
│  │  │  Direct     │    │  ├─ /api/generate               │     │    │
│  │  │  exposure   │    │  ├─ /api/reels (V1)             │     │    │
│  │  │             │    │  ├─ /api/reels/v2 (V2)          │     │    │
│  │  │  ⚠️ TODO    │    │  └─ /api/upload                 │     │    │
│  │  │             │    │                                 │     │    │
│  │  │  Add nginx  │    │  Venv: ~/sabrika-brand-manager/│     │    │
│  │  │  reverse    │    │        venv/                    │     │    │
│  │  │  proxy for  │    │  Logs: ~/flask.log              │     │    │
│  │  │  production │    │                                 │     │    │
│  │  └─────────────┘    └─────────────────────────────────┘     │    │
│  │                                                             │    │
│  │  System deps: ffmpeg, libgl1, libglib2.0                    │    │
│  │  Python deps: flask, pillow, ultralytics, opencv-python     │    │
│  │                                                             │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Known Limitation:** Flask dev server is exposed directly on port 5000. No reverse proxy (nginx) is configured. This is acceptable for the current single-user student workload but should be addressed before scaling (see ADR-004).

---

## 3. Incident Response Playbooks

### 3.1 P1: Application Completely Down

**Symptoms:** `curl http://20.125.62.241:5000/api/health` returns connection refused or timeout.

**Response Steps:**

1. **Verify VM is running:**
   ```bash
   az vm show --resource-group sabrika-rg --name sabrika-app-vm \
     --show-details --query "powerState"
   ```
   Expected: `VM running`. If `VM deallocated`, start it:
   ```bash
   az vm start --resource-group sabrika-rg --name sabrika-app-vm
   ```

2. **Check if Flask process is alive:**
   ```bash
   ssh -i ~/.ssh/id_rsa sabrika@20.125.62.241 "ps aux | grep python3"
   ```
   Expected: `python3 app.py` processes visible. If missing, restart:
   ```bash
   ./scripts/deploy.sh
   ```

3. **Check for OOM kill:**
   ```bash
   ssh -i ~/.ssh/id_rsa sabrika@20.125.62.241 "dmesg | grep -i 'killed process' | tail -5"
   ```
   If OOM detected, YOLOv8 inference exceeded RAM. Mitigation: reduce `sample_every_n_frames` in `reel_engine/frame_analyzer.py` (default: 2, increase to 5 for memory-constrained runs).

4. **Check disk full:**
   ```bash
   ssh -i ~/.ssh/id_rsa sabrika@20.125.62.241 "df -h"
   ```
   If `/` is >90% full, clean generated content:
   ```bash
   ssh -i ~/.ssh/id_rsa sabrika@20.125.62.241 \
     "rm -rf ~/sabrika-brand-manager/static/reels/* ~/sabrika-brand-manager/static/thumbnails/*"
   ```

### 3.2 P2: Reel Generation Fails (0s output or error)

**Symptoms:** API returns error, or reel is 0-1 seconds long.

**Response Steps:**

1. **Check logs for the specific error:**
   ```bash
   ./scripts/logs.sh --grep "ERROR"
   ```

2. **Common causes and fixes:**

   | Error Pattern | Root Cause | Fix |
   |---------------|-----------|-----|
   | `No valid video segments` | All scenes <0.5s | Upload longer clips (min 3s) with visible action |
   | `No scenes detected` | YOLO detects nothing | Lower confidence threshold or ensure clips have people/objects |
   | `FFmpeg error` | Corrupted clip | Re-encode clip: `ffmpeg -i bad.mp4 -c copy fixed.mp4` |
   | `Using 1 unique clips` | Scene type uniformity | Fixed in V2 — all clips now get distributed across roles |
   | `OOM` / process killed | RAM exhausted during YOLO | Increase `sample_every_n_frames` to 5 |

3. **Generate a reel report for diagnosis:**
   ```bash
   ./scripts/logs.sh --reel-report
   ```

### 3.3 P3: Frontend Not Loading / 404 on Static Files

**Symptoms:** HTML loads but CSS/JS fails, or images don't display.

**Response Steps:**

1. **Hard refresh:** The frontend uses cache-busting (`?v=2`) but browser cache may still be stale. Instruct user to `Ctrl+F5`.

2. **Verify static files exist on VM:**
   ```bash
   ssh -i ~/.ssh/id_rsa sabrika@20.125.62.241 \
     "ls -la ~/sabrika-brand-manager/static/style.css ~/sabrika-brand-manager/templates/index.html"
   ```

3. **If missing, redeploy:**
   ```bash
   ./scripts/deploy.sh
   ```

### 3.4 P4: Slow Response Times

**Symptoms:** Image generation or reel creation takes >30 seconds.

**Response Steps:**

1. **Check VM CPU/memory:**
   ```bash
   ./scripts/health-check.sh
   ```

2. **Identify bottleneck:**
   - Image generation slow → Pillow rendering is CPU-bound. Normal for complex gradients.
   - Reel generation slow → YOLOv8 inference on CPU. Expected: ~15-40s for 30s reel with 8 clips.

3. **Mitigation options:**
   - Increase `sample_every_n_frames` in `frame_analyzer.py` (trade accuracy for speed)
   - Reduce target duration from 30s to 15s
   - Upload fewer clips (4 instead of 8)

---

## 4. Deployment Procedures

### 4.1 Standard Deployment

```bash
# One-command deployment
./scripts/deploy.sh

# Deploy and tail logs
./scripts/deploy.sh --logs

# Deploy and verify API
./scripts/deploy.sh --check
```

### 4.2 Hotfix Deployment (Single File)

```bash
# Fix a bug in one file and deploy only that file
scp -i ~/.ssh/id_rsa reel_engine/ffmpeg_pipeline.py \
  sabrika@20.125.62.241:~/sabrika-brand-manager/reel_engine/

# Restart via Azure run-command (avoids SSH session kill)
az vm run-command invoke \
  --resource-group sabrika-rg \
  --name sabrika-app-vm \
  --command-id RunShellScript \
  --scripts 'pkill -f "python3 app.py"; sleep 2; su - sabrika -c "cd ~/sabrika-brand-manager && . venv/bin/activate && nohup python3 app.py > ~/flask.log 2>&1 &"'
```

### 4.3 Rollback Procedure

```bash
# SSH into VM
ssh -i ~/.ssh/id_rsa sabrika@20.125.62.241

# Restore from backup (created by deploy.sh on each sync)
cd ~/sabrika-brand-manager
cp -r /tmp/sabrika-backup-<timestamp>/* .

# Restart
pkill -f "python3 app.py"
nohup python3 app.py > ~/flask.log 2>&1 &
```

---

## 5. Monitoring and Alerting

### 5.1 Manual Health Checks

```bash
# Run once
./scripts/health-check.sh

# Run in watch mode (refreshes every 30s)
./scripts/health-check.sh --watch

# Exit with error code on failure (for CI/CD)
./scripts/health-check.sh --alert
```

### 5.2 Log Analysis

```bash
# Tail recent logs
./scripts/logs.sh

# Search for specific patterns
./scripts/logs.sh --grep "Reassigned"     # Role distribution
./scripts/logs.sh --grep "Using 6 unique" # Clip utilization
./scripts/logs.sh --reel-report           # Full generation trace
./scripts/logs.sh --errors                # Recent errors

# Download full log for offline analysis
./scripts/logs.sh --download
```

### 5.3 TODO: Automated Alerting

- [ ] Set up Azure Monitor metrics for VM CPU, memory, disk
- [ ] Configure alert when `/api/health` returns non-200 for >2 minutes
- [ ] Set up log-based alert for `ERROR` or `Exception` frequency >5/hour
- [ ] Add uptime monitoring via external service (e.g., UptimeRobot free tier)

---

## 6. Operational Contacts

| Role | Contact | Escalation |
|------|---------|------------|
| Primary Developer | shivaram19 (GitHub) | Direct |
| End User (Sabrika) | GVK Medical College, Almaty | WhatsApp |
| Azure Subscription | shivaramiitmb085@outlook.com | Azure Support |

---

## 7. References

- [ADR-001: Architecture](/docs/adrs/ADR-001-architecture-for-sabrika-brand-manager.md)
- [ADR-002: Reel Template Architecture](/docs/adrs/ADR-002-reel-template-architecture.md)
- [ADR-003: Frame Analysis Engine](/docs/adrs/ADR-003-frame-analysis-reel-engine.md)
- [ADR-004: DevOps Infrastructure](/docs/adrs/ADR-004-devops-infrastructure.md)
- [AGENTS.md](/AGENTS.md) — Project operating instructions
- [Research Corpus](/docs/research/) — BFS/DFS/bidirectional analysis
