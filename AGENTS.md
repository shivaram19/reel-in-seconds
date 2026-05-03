# Agent Operating Instructions: Sabrika Brand Manager

## Project Context

**Sabrika Brand Manager** is an Instagram content automation system for restaurant social media management. Built for Sabrika — a final-year MBBS student at GVK Medical College, Almaty, Kazakhstan — who manages Instagram for two restaurants part-time.

This is a **research-driven, citation-backed engineering project**. Every architectural and operational decision is justified by peer-reviewed research, canonical industry sources, or Architecture Decision Records (ADRs).

---

## 🔴 CRITICAL: Deployment State (Persistent Memory)

> **This application IS deployed.** Do not treat this as a local-only project.

| Attribute | Value |
|-----------|-------|
| **Cloud Provider** | Microsoft Azure |
| **VM Name** | `sabrika-app-vm` |
| **Public IP** | `20.125.62.241` |
| **HTTP Port** | `80` → redirects to `443` |
| **HTTPS Port** | `443` |
| **App Port** | `5000` (localhost-only, nginx reverse proxy) |
| **URL** | `https://20.125.62.241` |
| **SSL** | Self-signed certificate (`/etc/nginx/ssl/sabrika.crt`) |
| **Reverse Proxy** | nginx (`/etc/nginx/sites-enabled/sabrika`) |
| **Resource Group** | `sabrika-rg` |
| **Region** | `westus2` |
| **OS** | Ubuntu (Linux) |
| **User** | `sabrika` |
| **SSH Key** | `~/.ssh/id_rsa` |
| **App Directory** | `/home/sabrika/sabrika-brand-manager` |
| **Log File** | `/home/sabrika/flask.log` |
| **Process** | `python3 app.py` (Flask dev server, bound to `127.0.0.1:5000`) |
| **Monitor** | `sabrika-monitor.service` (systemd, self-healing daemon) |
| **Monitor State** | `/home/sabrika/.monitor/state.json` |

### Quick Operations

```bash
# Check health (HTTPS, through nginx)
curl -sk https://20.125.62.241/api/health

# SSH into VM
ssh -i ~/.ssh/id_rsa sabrika@20.125.62.241

# View live logs
ssh -i ~/.ssh/id_rsa sabrika@20.125.62.241 "tail -f ~/flask.log"

# View monitor logs
ssh -i ~/.ssh/id_rsa sabrika@20.125.62.241 "sudo journalctl -u sabrika-monitor -f"

# View monitor state
ssh -i ~/.ssh/id_rsa sabrika@20.125.62.241 "cat ~/.monitor/state.json | python3 -m json.tool"

# Restart app (via Azure run-command to avoid SSH session kill)
az vm run-command invoke \
  --resource-group sabrika-rg \
  --name sabrika-app-vm \
  --command-id RunShellScript \
  --scripts 'pkill -f "python3 app.py"; sleep 2; su - sabrika -c "cd ~/sabrika-brand-manager && . venv/bin/activate && nohup python3 app.py > ~/flask.log 2>&1 &"; sleep 3; curl -s http://localhost:5000/api/health'

# Check all services
az vm run-command invoke \
  --resource-group sabrika-rg \
  --name sabrika-app-vm \
  --command-id RunShellScript \
  --scripts 'systemctl status nginx sabrika-monitor --no-pager; echo "---"; curl -sk https://127.0.0.1/api/health -H "Host: 20.125.62.241"'
```

### Azure Resources

```
Resource Group: sabrika-rg (eastus + westus2)
├── sabrika-app-vm          (Microsoft.Compute/virtualMachines, westus2)
├── sabrika-app-vmPublicIP  (Microsoft.Network/publicIPAddresses, westus2)
├── sabrika-app-vmNSG       (Microsoft.Network/networkSecurityGroups, westus2)
├── sabrika-app-vmVNET      (Microsoft.Network/virtualNetworks, westus2)
└── sabrika-app-vmVMNic     (Microsoft.Network/networkInterfaces, westus2)
```

### What Is Running on the VM

- **Flask app** on port 5000 (Python 3.10.12, virtualenv at `venv/`)
- **FFmpeg** (system package) for video processing
- **OpenCV + YOLOv8** (Python packages) for frame analysis
- **NO Docker** on the VM (Docker not installed)
- **NO Container Apps / AKS / Web Apps** — bare VM deployment
- **nginx** reverse proxy (port 80 → 443 → localhost:5000)
- **Self-signed SSL** certificate (TLSv1.2/1.3)
- **Self-healing monitor** (`sabrika-monitor.service`) — probes `/api/health` every 30s, auto-restarts Flask on failure with exponential backoff
- **Flask bound to localhost** (`127.0.0.1:5000`) — no direct external access

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AZURE VM (sabrika-app-vm)                    │
│                         20.125.62.241:5000                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────┐      ┌─────────┐     ┌─────────────┐  ┌─────────────┐  │
│  │  nginx  │─────→│  Flask  │────→│  V1 Engine  │  │  V2 Frame   │  │
│  │  :443   │      │  :5000  │     │  (PyScene   │  │  Engine     │  │
│  │  (SSL)  │      │ (local) │     │   Detect +  │  │  (YOLOv8 +  │  │
│  └─────────┘      └─────────┘     │   FFmpeg)   │  │  OpenCV...) │  │
│       ↑                           │             │  │             │  │
│       │                           │  /api/reels │  │ /api/reels/ │  │
│       │                           │             │  │     v2      │  │
│  ┌────┴────┐                      └─────────────┘  └─────────────┘  │
│  │ Monitor │                                                           │
│  │(systemd)│                                                           │
│  └─────────┘                                                           │
│                              │                                       │
│                    ┌─────────┴─────────┐                             │
│                    │   FFmpeg (system)  │                             │
│                    │   libx264, yuv420p │                             │
│                    └───────────────────┘                             │
│                                                                      │
│  Data Layer: JSON files (data/restaurants.json)                      │
│  File Storage: static/{generated,logos,reels,thumbnails,uploads}/    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Personas (Multi-Dimensional Operating Mode)

When modifying this project, operate through all ten lenses simultaneously:

1. **Research Scientist** — Cite sources for every claim.
2. **First-Principles Engineer** — Derive from axioms, not trends.
3. **Distributed Systems Architect** — Design for scaling (even if current load is low).
4. **Infrastructure-First SRE** — Observability is mandatory; deployment state is persistent memory.
5. **Ethical Technologist** — Privacy, accessibility, carbon cost of ML inference.
6. **Resource Strategist** — TCO analysis before every decision.
7. **Diagnostic Problem-Solver** — Root cause, not symptom treatment.
8. **Curious Explorer** — Maintain lab notebook of experiments.
9. **Clarity-Driven Communicator** — ADRs for every major choice.
10. **Inner-Self Guided Builder** — Build what is right, not easy.

---

## Documentation Structure

```
docs/
├── research/
│   ├── bfs/           # Breadth-first landscape mapping
│   ├── dfs/           # Depth-first technology deep-dives
│   └── bidirectional/ # Cross-domain impact analysis
├── adrs/              # Architecture Decision Records (one per decision)
│   ├── ADR-001-architecture-for-sabrika-brand-manager.md
│   ├── ADR-002-reel-template-architecture.md
│   ├── ADR-003-frame-analysis-reel-engine.md
│   └── ADR-004-devops-infrastructure.md
├── operations/        # SRE runbooks, deployment procedures, incident response
└── debugging/         # Root-cause analyses of production issues

scripts/
├── deploy.sh                   # One-command deployment to Azure VM
├── health-check.sh             # VM and application health monitoring
├── logs.sh                     # Quick log access and tailing
├── monitor.py                  # Self-healing monitor daemon
└── sabrika-monitor.service     # systemd unit for monitor
```

---

## Citation Format

Use numbered references with full citations:
```
Claim about YOLOv8 latency [^1].

[^1]: Rajesh Kumar S., et al. (2025). Food Object Detection Using Custom-Trained YOLOv8. *ETASR*.
```

---

## Code Conventions

- `app.py`: Flask routes, API endpoints, error handling
- `restaurants.py`: JSON persistence layer
- `image_generator.py`: Pillow-based branded image generation
- `reel_engine/`: Modular reel editing engine (V1 + V2)
- `templates/`: Vanilla HTML/CSS/JS frontend (no build step)
- `static/`: Generated content, logos, reels, thumbnails, uploads
- `scripts/`: DevOps automation (deployment, health checks, log access)

---

## Prohibited Patterns

- Do NOT add dependencies without TCO analysis.
- Do NOT make architectural decisions without an ADR.
- Do NOT commit code without updating deployment state in AGENTS.md.
- Do NOT use unverified blog posts as primary citations.
- Do NOT forget the app is **deployed** — local changes must be pushed to Azure VM.

---

## Research-First Covenant (Mandatory)

All architectural and operational decisions must follow the **Research-First Covenant**. This is not optional.

1. **No code is written before research is complete.** Workflow: Decompose → BFS → DFS → Bidirectional → ADR → Code.
2. **Every claim requires a citation.** Numbered references to T1–T3 sources.
3. **Every architectural decision requires an ADR.** `docs/adrs/ADR-###-{topic}.md`
4. **The 10-Persona Filter applies to every change.**
5. **Anti-patterns are architectural malpractice.** "Just use X, everyone does" / "We'll fix it in production" are instant violations.

---

## Decision Authority

When in doubt:
1. Prefer boring, well-understood technology over shiny new tools.
2. Prefer open-source with active community over proprietary lock-in.
3. Prefer stateless services over stateful ones.
4. Prefer event-driven over synchronous RPC for cross-service communication.
5. **Prefer research-backed decisions over intuition.** Cite before you commit.
6. **Deployment state is persistent memory.** If the app is deployed, AGENTS.md must say so.

---

*Document version: 1.1*  
*Established: 2026-05-02*  
*Updated: 2026-05-03 (nginx + SSL + self-healing monitor)*  
*Deployment verified: sabrika-app-vm @ https://20.125.62.241*
