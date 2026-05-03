# ADR-005: Self-Healing Monitor Daemon

## Status
**Accepted** — Implemented 2026-05-03

## Context

Our single-node Azure VM deployment has a critical weakness: if the Flask dev server crashes (OOM, unhandled exception, port conflict), the application becomes unavailable until a human intervenes. With nginx now reverse-proxying traffic, a dead backend means 502 Bad Gateway for all users.

We need a watcher that:
1. Detects failure within 30 seconds (not minutes)
2. Auto-restarts the application (not just alerts)
3. Learns from failure patterns (not just logs)
4. Survives its own failure (not a single point of failure)

## Decision

Build a **standalone Python monitor daemon** (`scripts/monitor.py`) running as a systemd service. It probes `/api/health` every 30s, restarts Flask on failure with exponential backoff, and persists state to JSON for trend analysis.

### Why not just systemd `Restart=always` on Flask?

| Approach | Pros | Cons |
|----------|------|------|
| systemd `Restart=always` | Simple, native | No health probing — restarts on crash but not on hung/deadlocked state. No failure history. |
| systemd + `ExecStartPost` health check | Still simple | Fragile bash scripts, no structured state, hard to extend. |
| **Standalone Python monitor** (chosen) | Structured logging, JSON state, backoff logic, VM resource tracking, extensible | One more process to manage. |

### Why not a cloud-native solution (Azure Monitor, Datadog)?

- Cost: Azure Monitor Application Insights is ~$2.30/GB ingested. For a $30/mo VM, that's disproportionate.
- Control: We want the monitor to SSHlessly restart the app — external SaaS can't do that.
- Learning: Building it ourselves teaches us the failure modes of our own system.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Azure VM (sabrika-app-vm)                          │
│                                                     │
│  ┌──────────┐    proxy_pass    ┌─────────────────┐ │
│  │  nginx   │ ───────────────→ │  Flask (5000)   │ │
│  │  :443    │                  │  127.0.0.1:5000 │ │
│  └──────────┘                  └─────────────────┘ │
│         ↑                            ↑              │
│         │                            │ restart      │
│         │         health probe       │ on fail      │
│         └────────────────────────────┘              │
│                   monitor.py                        │
│              (systemd service)                      │
│                                                     │
│  State: ~/.monitor/state.json                       │
│  Logs:  ~/.monitor/monitor.log                      │
└─────────────────────────────────────────────────────┘
```

## Monitor Behavior

| State | Action |
|-------|--------|
| Health check OK | Log success, reset failure counter |
| 1st failure | Log warning, continue monitoring |
| 2nd consecutive failure | Attempt restart (5s backoff) |
| 3rd consecutive failure | Attempt restart (15s backoff) |
| 4th+ failure | Attempt restart (30-60s backoff) |
| Recovery detected | Mark last failure as resolved, log recovery time |

## State File Format

`~/.monitor/state.json`:
```json
{
  "monitor_started": "2026-05-03T12:00:00Z",
  "last_check": "2026-05-03T12:05:00Z",
  "app_status": "healthy",
  "consecutive_failures": 0,
  "total_restarts": 2,
  "total_checks": 600,
  "uptime_seconds": 300.0,
  "probe_results": [...],
  "failure_history": [...],
  "vm_resources": {
    "disk_used_pct": 45,
    "mem_used_pct": 72.3,
    "load_avg_1m": 0.85
  }
}
```

## Failure Pattern Learning

The monitor captures:
- Time-of-day failure correlation (e.g., OOM at 2am when batch jobs run)
- Recovery time after restart (trending up = degrading health)
- VM resource state at failure time (correlate crashes with memory spikes)

Future work: Feed this data into a simple classifier to predict failures before they happen (e.g., "memory > 90% for 5 min → 80% chance of OOM in next 10 min").

## Commands

```bash
# Check monitor status
sudo systemctl status sabrika-monitor

# View monitor logs
sudo journalctl -u sabrika-monitor -f

# View monitor state
cat ~/.monitor/state.json | python3 -m json.tool

# Stop monitor (app will no longer auto-restart)
sudo systemctl stop sabrika-monitor

# Restart monitor
sudo systemctl restart sabrika-monitor
```

## Consequences

### Positive
- **Sub-60s recovery time** from most failures (vs. potentially hours of human response)
- **Structured failure history** enables pattern detection and preventive fixes
- **VM resource correlation** helps distinguish app bugs from infrastructure limits
- **Standalone** — survives Flask crashes, restart loops, and OOM kills

### Negative
- **One more moving part** — the monitor itself can fail (mitigated by systemd `Restart=always`)
- **No external alerting** — if the VM itself dies, we only know when a user complains (acceptable for MVP; add Slack webhook later)
- **Self-signed SSL** — monitor must skip cert verification for localhost HTTPS (controlled risk)

## References

- [^1]: Beyer, B., et al. (2016). *Site Reliability Engineering*. O'Reilly. Chapter 6.
- [^2]: `scripts/monitor.py` — implementation
- [^3]: `scripts/sabrika-monitor.service` — systemd unit
