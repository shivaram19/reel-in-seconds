#!/usr/bin/env bash
#
# health-check.sh — Application and VM Health Monitoring
# ========================================================
#
# Purpose: Comprehensive health check covering application API,
# VM resources, running processes, disk usage, and recent errors.
#
# Why this exists:
#   - Reactive debugging ("the app is down") costs more than proactive
#     monitoring. Google SRE Book recommends health probes as the
#     foundation of service reliability [^1].
#   - The Flask dev server has no built-in health endpoint beyond our
#     custom /api/health — we need external validation.
#   - VM resource exhaustion (disk full, OOM) is the most common cause
#     of outages for single-node deployments.
#
# Usage:
#   ./scripts/health-check.sh              # Full health report
#   ./scripts/health-check.sh --watch      # Loop every 30s
#   ./scripts/health-check.sh --alert      # Exit 1 on any failure
#
# Citation:
#   [^1]: Beyer, B., et al. (2016). Site Reliability Engineering.
#         O'Reilly Media. Chapter 6: Monitoring Distributed Systems.
#   [^2]: docs/adrs/ADR-004-devops-infrastructure.md

set -euo pipefail

# ── CONFIGURATION ──
VM_IP="20.125.62.241"
HEALTH_URL="http://${VM_IP}:5000/api/health"
RESTAURANTS_URL="http://${VM_IP}:5000/api/restaurants"
SSH_KEY="${HOME}/.ssh/id_rsa"
VM_USER="sabrika"
WATCH_INTERVAL=30

# ── COLOR OUTPUT ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS="${GREEN}PASS${NC}"
FAIL="${RED}FAIL${NC}"
WARN="${YELLOW}WARN${NC}"

# ── CHECK FUNCTIONS ──

check_http() {
    local url="$1"
    local name="$2"
    local response
    local status
    
    response=$(curl -s --max-time 10 "$url" 2>/dev/null || echo "TIMEOUT")
    
    if echo "$response" | grep -q '"status": "ok"'; then
        echo -e "  $PASS  $name"
        return 0
    elif [[ "$response" == "TIMEOUT" ]]; then
        echo -e "  $FAIL  $name (timeout)"
        return 1
    else
        echo -e "  $FAIL  $name (unexpected response)"
        return 1
    fi
}

check_vm_resource() {
    local resource="$1"
    local threshold="$2"
    local cmd="$3"
    local value
    
    value=$(ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no \
        "${VM_USER}@${VM_IP}" "$cmd" 2>/dev/null || echo "ERROR")
    
    if [[ "$value" == "ERROR" ]]; then
        echo -e "  $FAIL  $resource (SSH failed)"
        return 1
    fi
    
    if awk "BEGIN {exit !($value $threshold)}"; then
        echo -e "  $WARN  $resource: ${value} (threshold: ${threshold})"
        return 1
    else
        echo -e "  $PASS  $resource: ${value}"
        return 0
    fi
}

check_process() {
    local name="$1"
    local pattern="$2"
    local count
    
    count=$(ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no \
        "${VM_USER}@${VM_IP}" "ps aux | grep -E '$pattern' | grep -v grep | wc -l" 2>/dev/null || echo "0")
    
    if [[ "$count" -gt 0 ]]; then
        echo -e "  $PASS  $name running ($count process(es))"
        return 0
    else
        echo -e "  $FAIL  $name NOT running"
        return 1
    fi
}

check_recent_errors() {
    local log_file="/home/sabrika/flask.log"
    local error_count
    
    error_count=$(ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no \
        "${VM_USER}@${VM_IP}" "grep -c 'ERROR\|Exception\|Traceback' $log_file 2>/dev/null || echo 0")
    
    if [[ "$error_count" -eq 0 ]]; then
        echo -e "  $PASS  No errors in $log_file"
        return 0
    elif [[ "$error_count" -lt 5 ]]; then
        echo -e "  $WARN  $error_count errors in $log_file"
        return 0
    else
        echo -e "  $FAIL  $error_count errors in $log_file"
        return 1
    fi
}

# ── MAIN HEALTH REPORT ──

run_checks() {
    local failed=0
    
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Sabrika Brand Manager — Health Report${NC}"
    echo -e "${BLUE}  $(date -u +'%Y-%m-%d %H:%M:%S UTC')${NC}"
    echo -e "${BLUE}  VM: ${VM_IP}${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo ""
    
    echo -e "${YELLOW}Application Layer:${NC}"
    check_http "$HEALTH_URL" "API Health" || ((failed++))
    check_http "$RESTAURANTS_URL" "API Restaurants" || ((failed++))
    echo ""
    
    echo -e "${YELLOW}Process Layer:${NC}"
    check_process "Flask app" "python3 app.py" || ((failed++))
    echo ""
    
    echo -e "${YELLOW}VM Resources:${NC}"
    check_vm_resource "Disk usage (/)" "> 90" "df / | tail -1 | awk '{print \$5}' | sed 's/%//'" || ((failed++))
    check_vm_resource "Memory usage" "> 90" "free | grep Mem | awk '{printf \"%.0f\", \$3/\$2 * 100.0}'" || ((failed++))
    check_vm_resource "Load average (1m)" "> 4.0" "uptime | awk -F'load average:' '{print \$2}' | awk '{print \$1}' | sed 's/,//'" || ((failed++))
    echo ""
    
    echo -e "${YELLOW}Log Health:${NC}"
    check_recent_errors || ((failed++))
    echo ""
    
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    if [[ "$failed" -eq 0 ]]; then
        echo -e "${GREEN}  ALL CHECKS PASSED${NC}"
    else
        echo -e "${RED}  $failed CHECK(S) FAILED${NC}"
    fi
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo ""
    
    return "$failed"
}

# ── EXECUTION MODES ──

if [[ "${1:-}" == "--watch" ]]; then
    while true; do
        clear
        run_checks || true
        echo "Refreshing in ${WATCH_INTERVAL}s... (Ctrl+C to stop)"
        sleep "$WATCH_INTERVAL"
    done
elif [[ "${1:-}" == "--alert" ]]; then
    run_checks
else
    run_checks || true
fi
