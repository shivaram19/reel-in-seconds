#!/usr/bin/env bash
#
# logs.sh — Quick Log Access and Analysis
# ========================================
#
# Purpose: Streamlined access to application logs on the Azure VM
# without requiring manual SSH + grep commands.
#
# Why this exists:
#   - The Flask app logs to /home/sabrika/flask.log on the VM.
#   - During reel generation, detailed YOLOv8 and FFmpeg logs are written.
#   - Manual SSH + tail + grep is repetitive and error-prone.
#   - Structured log access is a prerequisite for diagnostic root-cause
#     analysis per AGENTS.md § Diagnostic Problem-Solver [^1].
#
# Usage:
#   ./scripts/logs.sh                    # Tail last 50 lines
#   ./scripts/logs.sh --tail 100         # Tail last N lines
#   ./scripts/logs.sh --grep "ERROR"     # Filter for errors
#   ./scripts/logs.sh --grep "Reassigned" # Show role distribution
#   ./scripts/logs.sh --grep "Using"     # Show clip usage summary
#   ./scripts/logs.sh --reel-report      # Show last reel generation report
#   ./scripts/logs.sh --download         # Download full log to local
#
# Citation:
#   [^1]: AGENTS.md § Diagnostic Problem-Solver, voice-revenge-vizuara-ai
#   [^2]: docs/adrs/ADR-004-devops-infrastructure.md

set -euo pipefail

# ── CONFIGURATION ──
VM_IP="20.125.62.241"
SSH_KEY="${HOME}/.ssh/id_rsa"
VM_USER="sabrika"
REMOTE_LOG="/home/sabrika/flask.log"
LOCAL_LOG_DIR="./logs"

# ── COLOR OUTPUT ──
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[LOGS]${NC} $*"; }

# ── MAIN ──

mkdir -p "$LOCAL_LOG_DIR"

CMD="${1:---tail}"
ARG="${2:-50}"

case "$CMD" in
    --tail|-t)
        log_info "Tailing last ${ARG} lines from ${REMOTE_LOG}..."
        ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no \
            "${VM_USER}@${VM_IP}" "tail -n ${ARG} ${REMOTE_LOG}"
        ;;
    
    --grep|-g)
        log_info "Searching for '${ARG}' in ${REMOTE_LOG}..."
        ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no \
            "${VM_USER}@${VM_IP}" "grep -n '${ARG}' ${REMOTE_LOG} | tail -30"
        ;;
    
    --reel-report|-r)
        log_info "Extracting last reel generation report..."
        ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no \
            "${VM_USER}@${VM_IP}" "grep -E '\[generate_reel\]|\[DomainMapper\]|\[FFmpegPipeline\]|\[NarrativeAssembler\]' ${REMOTE_LOG} | tail -40"
        ;;
    
    --errors|-e)
        log_info "Extracting recent errors..."
        ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no \
            "${VM_USER}@${VM_IP}" "grep -n 'ERROR\|Exception\|Traceback' ${REMOTE_LOG} | tail -20"
        ;;
    
    --clip-usage|-c)
        log_info "Showing clip usage from recent generations..."
        ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no \
            "${VM_USER}@${VM_IP}" "grep -E 'Clip [0-9]+|unique clips|Reassigned' ${REMOTE_LOG} | tail -30"
        ;;
    
    --download|-d)
        local_file="${LOCAL_LOG_DIR}/flask-$(date +%Y%m%d-%H%M%S).log"
        log_info "Downloading ${REMOTE_LOG} to ${local_file}..."
        scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
            "${VM_USER}@${VM_IP}:${REMOTE_LOG}" "$local_file"
        log_info "Downloaded to: ${local_file}"
        ;;
    
    --follow|-f)
        log_info "Following log in real-time (Ctrl+C to exit)..."
        ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no \
            "${VM_USER}@${VM_IP}" "tail -f ${REMOTE_LOG}"
        ;;
    
    *)
        echo "Usage: $0 [OPTION] [ARG]"
        echo ""
        echo "Options:"
        echo "  --tail N       Tail last N lines (default: 50)"
        echo "  --grep PATTERN Search for pattern"
        echo "  --reel-report  Show last reel generation details"
        echo "  --errors       Show recent errors"
        echo "  --clip-usage   Show which clips were used"
        echo "  --download     Download full log to ./logs/"
        echo "  --follow       Follow log in real-time"
        echo ""
        echo "Examples:"
        echo "  $0 --grep 'Reassigned'        # See role distribution"
        echo "  $0 --grep 'Using 6 unique'    # See clip utilization"
        echo "  $0 --reel-report              # Full generation trace"
        exit 1
        ;;
esac
