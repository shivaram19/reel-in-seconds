# SRE / DevOps Skill

## Description

Site Reliability Engineering and DevOps automation for the Sabrika Brand Manager project. This skill provides persistent deployment memory, operational automation, and incident response capabilities that survive across CLI sessions.

**When to use:**
- Deploying code changes to the Azure VM
- Investigating application failures or slow performance
- Checking application health or viewing logs
- Any question about infrastructure, deployment, or operations

## Deployment State (Persistent Memory)

> **The application IS deployed.** Do not treat this as local-only.

| Attribute | Value |
|-----------|-------|
| **Cloud Provider** | Microsoft Azure |
| **VM Name** | `sabrika-app-vm` |
| **Public IP** | `20.125.62.241` |
| **Port** | `5000` |
| **URL** | `http://20.125.62.241:5000` |
| **Resource Group** | `sabrika-rg` |
| **Region** | `westus2` |
| **SSH User** | `sabrika` |
| **SSH Key** | `~/.ssh/id_rsa` |
| **App Directory** | `/home/sabrika/sabrika-brand-manager` |
| **Log File** | `/home/sabrika/flask.log` |

## Quick Operations

### Check Health
```bash
curl http://20.125.62.241:5000/api/health
```

### Deploy Latest Code
```bash
./scripts/deploy.sh           # Deploy + verify
./scripts/deploy.sh --logs    # Deploy + tail logs
./scripts/deploy.sh --check   # Deploy + API check
```

### View Logs
```bash
./scripts/logs.sh                    # Tail last 50 lines
./scripts/logs.sh --grep "ERROR"     # Find errors
./scripts/logs.sh --reel-report      # Last generation trace
./scripts/logs.sh --clip-usage       # Which clips were used
./scripts/logs.sh --follow           # Real-time tail
```

### Health Monitoring
```bash
./scripts/health-check.sh         # Single check
./scripts/health-check.sh --watch # Loop every 30s
./scripts/health-check.sh --alert # Exit 1 on failure
```

### Restart App (Azure Run-Command)
```bash
az vm run-command invoke \
  --resource-group sabrika-rg \
  --name sabrika-app-vm \
  --command-id RunShellScript \
  --scripts 'pkill -f "python3 app.py"; sleep 2; su - sabrika -c "cd ~/sabrika-brand-manager && . venv/bin/activate && nohup python3 app.py > ~/flask.log 2>&1 &"; sleep 3; curl -s http://localhost:5000/api/health'
```

## Architecture

```
Azure VM (sabrika-app-vm) @ 20.125.62.241:5000
├── Flask app (port 5000, python3 app.py via nohup)
├── V1 Reel Engine (PySceneDetect + FFmpeg)
├── V2 Reel Engine (YOLOv8 + OpenCV + Domain Mapping + Narrative Assembly)
├── Image Generator (Pillow)
├── JSON data store (data/restaurants.json)
└── File storage (static/{generated,logos,reels,thumbnails,uploads}/)
```

**NO Docker** on VM. **NO nginx** reverse proxy. Flask dev server exposed directly.

## Incident Response

| Severity | Symptom | Quick Fix |
|----------|---------|-----------|
| P1 | App down / connection refused | `./scripts/deploy.sh` |
| P2 | Reel generation fails / 0s output | `./scripts/logs.sh --reel-report` then check clip duration |
| P3 | Frontend 404 / missing CSS | `Ctrl+F5` hard refresh, then `./scripts/deploy.sh` |
| P4 | Slow response / timeout | `./scripts/health-check.sh` check CPU/memory |

## Files

- `AGENTS.md` — Deployment state, architecture, operating instructions
- `scripts/deploy.sh` — One-command deployment
- `scripts/health-check.sh` — Health monitoring
- `scripts/logs.sh` — Log access and analysis
- `docs/operations/runbook.md` — Incident response playbooks
- `docs/adrs/ADR-004-devops-infrastructure.md` — DevOps architecture decisions
