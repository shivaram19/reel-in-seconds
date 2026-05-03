#!/usr/bin/env python3
"""
Self-Healing Monitor — The System That Watches Itself
======================================================

A lightweight, standalone health monitoring daemon that:
  1. Probes the Flask application every 30s
  2. Auto-restarts the app on failure (with backoff)
  3. Records failure patterns for trend analysis
  4. Tracks VM resource usage (CPU, memory, disk)
  5. Exposes a JSON state file for external inspection

Why Python instead of bash:
  - Structured data (JSON state, failure history)
  - Built-in signal handling for graceful shutdown
  - Easy to extend with more probes

Why standalone (not part of Flask):
  - If Flask crashes, the monitor must survive to restart it
  - Separation of concerns: app serves users, monitor serves the app

Architecture:
  - Runs as systemd service (sabrika-monitor.service)
  - Writes state to /home/sabrika/.monitor/state.json
  - Logs to /home/sabrika/.monitor/monitor.log
  - Reads config from /home/sabrika/.monitor/config.json (optional)

Citation:
  [^1]: Google SRE Book, Chapter 6 — Monitoring Distributed Systems
  [^2]: docs/adrs/ADR-005-self-healing-monitor.md
"""

import json
import logging
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
import urllib.request
import urllib.error

# ── CONFIGURATION ──
APP_URL = "https://127.0.0.1/api/health"
APP_START_CMD = "cd /home/sabrika/sabrika-brand-manager && . venv/bin/activate && nohup python3 app.py > ~/flask.log 2>&1 &"
CHECK_INTERVAL = 30  # seconds
STATE_DIR = Path("/home/sabrika/.monitor")
STATE_FILE = STATE_DIR / "state.json"
LOG_FILE = STATE_DIR / "monitor.log"
MAX_FAILURE_HISTORY = 100
RESTART_BACKOFF = [0, 5, 15, 30, 60]  # seconds between restart attempts

# ── DATA STRUCTURES ──

@dataclass
class ProbeResult:
    timestamp: str
    status: str  # "ok", "fail", "timeout"
    response_time_ms: float
    details: str = ""

@dataclass
class FailureEvent:
    timestamp: str
    reason: str
    action_taken: str
    resolved: bool = False
    resolved_at: Optional[str] = None

@dataclass
class SystemState:
    monitor_started: str
    last_check: Optional[str] = None
    app_status: str = "unknown"
    consecutive_failures: int = 0
    total_restarts: int = 0
    total_checks: int = 0
    uptime_seconds: float = 0.0
    probe_results: List[dict] = field(default_factory=list)
    failure_history: List[dict] = field(default_factory=list)
    vm_resources: dict = field(default_factory=dict)

# ── LOGGING SETUP ──

STATE_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("monitor")

# ── SIGNAL HANDLING ──

shutdown_requested = False

def _signal_handler(signum, frame):
    global shutdown_requested
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown_requested = True

signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)

# ── CORE FUNCTIONS ──

def probe_app() -> ProbeResult:
    """Probe the Flask app health endpoint."""
    start = time.time()
    try:
        req = urllib.request.Request(
            APP_URL,
            headers={"Host": "20.125.62.241"},
        )
        # Allow self-signed cert (we control this VM)
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            body = resp.read().decode("utf-8")
            elapsed = (time.time() - start) * 1000
            try:
                data = json.loads(body)
                if data.get("status") == "ok":
                    return ProbeResult(
                        timestamp=datetime.utcnow().isoformat(),
                        status="ok",
                        response_time_ms=round(elapsed, 2),
                        details=f"code_hash={data.get('code_hash', 'unknown')[:8]}",
                    )
                else:
                    return ProbeResult(
                        timestamp=datetime.utcnow().isoformat(),
                        status="fail",
                        response_time_ms=round(elapsed, 2),
                        details=f"status={data.get('status')}",
                    )
            except json.JSONDecodeError:
                return ProbeResult(
                    timestamp=datetime.utcnow().isoformat(),
                    status="fail",
                    response_time_ms=round(elapsed, 2),
                    details=f"non-JSON response: {body[:100]}",
                )
    except urllib.error.HTTPError as e:
        elapsed = (time.time() - start) * 1000
        return ProbeResult(
            timestamp=datetime.utcnow().isoformat(),
            status="fail",
            response_time_ms=round(elapsed, 2),
            details=f"HTTP {e.code}",
        )
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return ProbeResult(
            timestamp=datetime.utcnow().isoformat(),
            status="timeout" if "timeout" in str(e).lower() else "fail",
            response_time_ms=round(elapsed, 2),
            details=str(e)[:200],
        )

def restart_app() -> bool:
    """Restart the Flask application."""
    logger.warning("Attempting app restart...")
    try:
        # Kill existing process
        subprocess.run(
            ["pkill", "-f", "python3 app.py"],
            capture_output=True,
            timeout=10,
        )
        time.sleep(2)
        # Start new process
        # Run directly — monitor already runs as sabrika via systemd
        subprocess.run(
            APP_START_CMD,
            shell=True,
            capture_output=True,
            timeout=15,
        )
        time.sleep(3)
        # Verify
        result = probe_app()
        if result.status == "ok":
            logger.info("App restart successful")
            return True
        else:
            logger.error(f"App restart failed: {result.details}")
            return False
    except Exception as e:
        logger.error(f"Restart error: {e}")
        return False

def get_vm_resources() -> dict:
    """Get current VM resource usage."""
    try:
        # Disk
        df = subprocess.run(
            ["df", "/"], capture_output=True, text=True, timeout=5
        ).stdout.strip().split("\n")[-1].split()
        disk_used_pct = int(df[4].rstrip("%"))
        
        # Memory
        mem = subprocess.run(
            ["free"], capture_output=True, text=True, timeout=5
        ).stdout.strip().split("\n")[1].split()
        mem_total = int(mem[1])
        mem_used = int(mem[2])
        mem_pct = round(mem_used / mem_total * 100, 1)
        
        # Load
        load = subprocess.run(
            ["uptime"], capture_output=True, text=True, timeout=5
        ).stdout.strip()
        load_avg = load.split("load average:")[1].strip().split(",")[0].strip()
        
        return {
            "disk_used_pct": disk_used_pct,
            "mem_used_pct": mem_pct,
            "load_avg_1m": float(load_avg),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}

def save_state(state: SystemState):
    """Persist monitor state to JSON file."""
    try:
        STATE_FILE.write_text(json.dumps(asdict(state), indent=2))
    except Exception as e:
        logger.error(f"Failed to save state: {e}")

def load_state() -> SystemState:
    """Load previous monitor state if exists."""
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text())
            return SystemState(**data)
        except Exception:
            pass
    return SystemState(monitor_started=datetime.utcnow().isoformat())

# ── MAIN LOOP ──

def main():
    state = load_state()
    state.monitor_started = datetime.utcnow().isoformat()
    start_time = time.time()
    
    logger.info("=" * 50)
    logger.info("Self-Healing Monitor started")
    logger.info(f"Target: {APP_URL}")
    logger.info(f"Check interval: {CHECK_INTERVAL}s")
    logger.info(f"State file: {STATE_FILE}")
    logger.info("=" * 50)
    
    last_restart_attempt: Optional[datetime] = None
    
    while not shutdown_requested:
        loop_start = time.time()
        
        # Update uptime
        state.uptime_seconds = round(time.time() - start_time, 1)
        state.last_check = datetime.utcnow().isoformat()
        state.total_checks += 1
        
        # Probe app
        result = probe_app()
        state.probe_results.append(asdict(result))
        state.probe_results = state.probe_results[-MAX_FAILURE_HISTORY:]
        
        if result.status == "ok":
            state.app_status = "healthy"
            if state.consecutive_failures > 0:
                # Mark last failure as resolved
                if state.failure_history and not state.failure_history[-1].get("resolved"):
                    state.failure_history[-1]["resolved"] = True
                    state.failure_history[-1]["resolved_at"] = datetime.utcnow().isoformat()
                logger.info(f"App recovered after {state.consecutive_failures} failures")
            state.consecutive_failures = 0
            logger.info(
                f"Probe OK — {result.response_time_ms}ms | {result.details}"
            )
        else:
            state.consecutive_failures += 1
            state.app_status = f"failing ({state.consecutive_failures} consecutive)"
            logger.warning(
                f"Probe FAIL — {result.status} | {result.details}"
            )
            
            # Decide whether to restart
            should_restart = True
            if last_restart_attempt:
                time_since_restart = (datetime.utcnow() - last_restart_attempt).total_seconds()
                backoff_idx = min(state.consecutive_failures - 1, len(RESTART_BACKOFF) - 1)
                if time_since_restart < RESTART_BACKOFF[backoff_idx]:
                    should_restart = False
                    logger.info(f"Backing off — {RESTART_BACKOFF[backoff_idx] - time_since_restart:.0f}s remaining")
            
            if should_restart:
                action = "restart attempted"
                success = restart_app()
                if success:
                    state.total_restarts += 1
                    last_restart_attempt = datetime.utcnow()
                else:
                    action = "restart failed"
                
                event = FailureEvent(
                    timestamp=datetime.utcnow().isoformat(),
                    reason=result.details,
                    action_taken=action,
                )
                state.failure_history.append(asdict(event))
                state.failure_history = state.failure_history[-MAX_FAILURE_HISTORY:]
        
        # Collect VM resources
        state.vm_resources = get_vm_resources()
        
        # Persist state
        save_state(state)
        
        # Sleep until next check
        elapsed = time.time() - loop_start
        sleep_time = max(0, CHECK_INTERVAL - elapsed)
        time.sleep(sleep_time)
    
    logger.info("Monitor shutting down")
    state.app_status = "monitor_stopped"
    save_state(state)

if __name__ == "__main__":
    main()
