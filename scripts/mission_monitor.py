#!/usr/bin/env python3
"""
Mission-Aware Monitor Extension — Semantic Health Probes
=========================================================

The base monitor checks "is Flask responding?"
This extension checks "is the system fulfilling its mission?"

Mission definition (derived from ADRs and user requirements):
  1. Restaurant data must be loadable
  2. Image generation must produce valid output
  3. Reel pipeline must process clips into video
  4. No ERROR-level logs in recent window
  5. VM resources must stay within bounds

Why this exists:
  - The user asked for "mission awareness" — a system that knows what it
    SHOULD do, not just whether it's up.
  - This is semantic validation, not just syntactic (HTTP 200).
  - Research basis: Leucker & Schallhart (2009) on runtime verification —
    checking behavior against a specification at runtime.

Citation:
  [^1]: Leucker, M., & Schallhart, C. (2009). A brief account of runtime
        verification. Journal of Logic and Algebraic Programming, 78(5).
"""

import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import urllib.request
import urllib.error
import ssl

# ── CONFIGURATION ──
BASE_URL = "https://127.0.0.1"
HOST_HEADER = "20.125.62.241"
LOG_FILE = "/home/sabrika/flask.log"
STATE_DIR = Path("/home/sabrika/.monitor")
MISSION_STATE_FILE = STATE_DIR / "mission_state.json"

# VM resource thresholds
MEM_THRESHOLD_PCT = 90
DISK_THRESHOLD_PCT = 90
LOAD_THRESHOLD = 4.0

# ── SSL CONTEXT (self-signed cert) ──
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# ── LOGGING ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("mission-monitor")


# ── DATA STRUCTURES ──

@dataclass
class MissionCheck:
    name: str
    passed: bool
    details: str
    response_time_ms: float = 0.0


@dataclass
class MissionState:
    timestamp: str
    overall_status: str  # "healthy", "degraded", "failing"
    mission_score: float  # 0.0–1.0 fraction of checks passed
    checks: List[dict]
    vm_resources: dict
    recent_errors: int


# ── CORE FUNCTIONS ──

def _api_call(path: str, method="GET", payload=None) -> tuple:
    """Make HTTPS API call through nginx. Returns (status, body, elapsed_ms)."""
    url = f"{BASE_URL}{path}"
    start = time.time()
    try:
        req = urllib.request.Request(
            url,
            headers={"Host": HOST_HEADER, "Content-Type": "application/json"},
            method=method,
        )
        if payload:
            req.data = json.dumps(payload).encode("utf-8")
        with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as resp:
            body = resp.read().decode("utf-8")
            elapsed = (time.time() - start) * 1000
            return resp.status, body, elapsed
    except urllib.error.HTTPError as e:
        elapsed = (time.time() - start) * 1000
        return e.code, e.read().decode("utf-8", errors="replace"), elapsed
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return 0, str(e), elapsed


def check_restaurant_data() -> MissionCheck:
    """Mission 1: Restaurant data must be loadable."""
    status, body, elapsed = _api_call("/api/restaurants")
    if status != 200:
        return MissionCheck("restaurant_data", False, f"HTTP {status}", elapsed)
    try:
        data = json.loads(body)
        if not isinstance(data, list) or len(data) == 0:
            return MissionCheck("restaurant_data", False, "Empty or invalid list", elapsed)
        # Verify The Pakwaan (id: 1) exists
        pakwaan = next((r for r in data if r.get("id") == 1), None)
        if not pakwaan:
            return MissionCheck("restaurant_data", False, "The Pakwaan (id:1) missing", elapsed)
        return MissionCheck("restaurant_data", True, f"{len(data)} restaurants, Pakwaan found", elapsed)
    except json.JSONDecodeError:
        return MissionCheck("restaurant_data", False, "Non-JSON response", elapsed)


def check_image_generation() -> MissionCheck:
    """Mission 2: Image generation must produce valid output."""
    status, body, elapsed = _api_call("/api/generate", method="POST", payload={
        "restaurant_id": 1,
        "type": "story"
    })
    if status != 200:
        return MissionCheck("image_generation", False, f"HTTP {status}", elapsed)
    try:
        data = json.loads(body)
        if "image_url" in data or "url" in data:
            return MissionCheck("image_generation", True, "Image URL returned", elapsed)
        return MissionCheck("image_generation", False, "No image_url in response", elapsed)
    except json.JSONDecodeError:
        return MissionCheck("image_generation", False, "Non-JSON response", elapsed)


def check_reel_pipeline() -> MissionCheck:
    """Mission 3: Reel pipeline must accept requests (full processing is too slow for probe)."""
    status, body, elapsed = _api_call("/api/reels/v2", method="POST", payload={
        "restaurant_id": 1,
        "clips": [],
        "template": "auto",
        "duration": 30
    })
    # Empty clips should return 400 or structured error — either means the endpoint is alive
    if status in (200, 400):
        return MissionCheck("reel_pipeline", True, f"Endpoint responsive (HTTP {status})", elapsed)
    return MissionCheck("reel_pipeline", False, f"HTTP {status}", elapsed)


def check_recent_errors() -> MissionCheck:
    """Mission 4: No excessive ERROR-level logs."""
    try:
        if not os.path.exists(LOG_FILE):
            return MissionCheck("recent_errors", True, "No log file (fresh start)", 0)
        # Count ERROR/Traceback in last 50 lines
        result = subprocess.run(
            ["tail", "-50", LOG_FILE],
            capture_output=True, text=True, timeout=5
        )
        error_count = sum(1 for line in result.stdout.split("\n") if "ERROR" in line or "Traceback" in line)
        if error_count == 0:
            return MissionCheck("recent_errors", True, "0 errors in last 50 log lines", 0)
        elif error_count < 3:
            return MissionCheck("recent_errors", True, f"{error_count} errors (acceptable)", 0)
        else:
            return MissionCheck("recent_errors", False, f"{error_count} errors in last 50 lines", 0)
    except Exception as e:
        return MissionCheck("recent_errors", False, str(e), 0)


def check_vm_resources() -> Dict:
    """Get current VM resource usage."""
    try:
        df = subprocess.run(
            ["df", "/"], capture_output=True, text=True, timeout=5
        ).stdout.strip().split("\n")[-1].split()
        disk_pct = int(df[4].rstrip("%"))

        mem = subprocess.run(
            ["free"], capture_output=True, text=True, timeout=5
        ).stdout.strip().split("\n")[1].split()
        mem_total = int(mem[1])
        mem_used = int(mem[2])
        mem_pct = round(mem_used / mem_total * 100, 1)

        load = subprocess.run(
            ["uptime"], capture_output=True, text=True, timeout=5
        ).stdout.strip()
        load_avg = float(load.split("load average:")[1].strip().split(",")[0].strip())

        return {
            "disk_used_pct": disk_pct,
            "mem_used_pct": mem_pct,
            "load_avg_1m": load_avg,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def evaluate_mission() -> MissionState:
    """Run all mission checks and return aggregated state."""
    checks = [
        check_restaurant_data(),
        check_image_generation(),
        check_reel_pipeline(),
        check_recent_errors(),
    ]

    vm = check_vm_resources()

    passed = sum(1 for c in checks if c.passed)
    total = len(checks)
    score = passed / total if total > 0 else 0.0

    # VM resource checks are separate warnings
    vm_warnings = []
    if vm.get("mem_used_pct", 0) > MEM_THRESHOLD_PCT:
        vm_warnings.append(f"Memory {vm['mem_used_pct']}% > {MEM_THRESHOLD_PCT}%")
    if vm.get("disk_used_pct", 0) > DISK_THRESHOLD_PCT:
        vm_warnings.append(f"Disk {vm['disk_used_pct']}% > {DISK_THRESHOLD_PCT}%")
    if vm.get("load_avg_1m", 0) > LOAD_THRESHOLD:
        vm_warnings.append(f"Load {vm['load_avg_1m']} > {LOAD_THRESHOLD}")

    if score == 1.0 and not vm_warnings:
        status = "healthy"
    elif score >= 0.5:
        status = "degraded"
    else:
        status = "failing"

    state = MissionState(
        timestamp=datetime.utcnow().isoformat(),
        overall_status=status,
        mission_score=round(score, 2),
        checks=[asdict(c) for c in checks],
        vm_resources=vm,
        recent_errors=sum(1 for c in checks if c.name == "recent_errors" and not c.passed),
    )

    # Log results
    logger.info(f"Mission score: {score:.0%} — {status}")
    for c in checks:
        icon = "✓" if c.passed else "✗"
        logger.info(f"  {icon} {c.name}: {c.details} ({c.response_time_ms:.1f}ms)")
    if vm_warnings:
        for w in vm_warnings:
            logger.warning(f"  ⚠ VM: {w}")

    return state


def save_state(state: MissionState):
    """Persist mission state to JSON file."""
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        MISSION_STATE_FILE.write_text(json.dumps(asdict(state), indent=2))
    except Exception as e:
        logger.error(f"Failed to save mission state: {e}")


def main():
    logger.info("=" * 50)
    logger.info("Mission-Aware Monitor running")
    logger.info("Validating system mission, not just uptime")
    logger.info("=" * 50)

    state = evaluate_mission()
    save_state(state)

    # Exit with error code if failing (for use in cron/systemd timer)
    if state.overall_status == "failing":
        logger.error("MISSION FAILING — intervention required")
        exit(1)


if __name__ == "__main__":
    main()
