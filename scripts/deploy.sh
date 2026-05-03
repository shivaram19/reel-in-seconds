#!/usr/bin/env bash
#
# deploy.sh — One-Command Deployment to Azure VM
# =================================================
#
# Purpose: Sync local code changes to the deployed Azure VM and restart
# the Flask application with zero downtime awareness.
#
# Why this exists:
#   - Manual SCP + SSH restart is error-prone and forgets steps.
#   - The VM has NO Docker — deployment is file-sync + process restart.
#   - Azure run-command is used for restart to avoid SSH session kill
#     when pkill terminates the shell that spawned it.
#
# Research basis:
#   - Azure VM run-command: Recommended by Microsoft for agent-less
#     remote execution [docs.microsoft.com/azure/virtual-machines/run-command]
#   - nohup + background process: POSIX-standard detached process
#     management, more reliable than systemd for simple Flask apps.
#
# Usage:
#   ./scripts/deploy.sh              # Deploy current working tree
#   ./scripts/deploy.sh --logs       # Deploy and tail logs
#   ./scripts/deploy.sh --check      # Deploy and run health check
#
# Prerequisites:
#   - az CLI installed and authenticated
#   - SSH key at ~/.ssh/id_rsa with access to sabrika@20.125.62.241
#   - Azure subscription with sabrika-rg resource group
#
# Citation:
#   [^1]: docs/adrs/ADR-004-devops-infrastructure.md (Deployment Procedures)

set -euo pipefail

# ── CONFIGURATION ──
VM_IP="20.125.62.241"
VM_USER="sabrika"
SSH_KEY="${HOME}/.ssh/id_rsa"
RG="sabrika-rg"
VM_NAME="sabrika-app-vm"
REMOTE_DIR="/home/sabrika/sabrika-brand-manager"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# ── COLOR OUTPUT ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ── STEP 1: VALIDATE PREREQUISITES ──
log_info "Validating prerequisites..."

if ! command -v az &> /dev/null; then
    log_error "Azure CLI (az) not found. Install: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
    exit 1
fi

if ! az account show &> /dev/null; then
    log_error "Not logged into Azure. Run: az login"
    exit 1
fi

if [[ ! -f "$SSH_KEY" ]]; then
    log_error "SSH key not found: $SSH_KEY"
    exit 1
fi

# ── STEP 2: SYNC CODE TO VM ──
log_info "Syncing code to ${VM_USER}@${VM_IP}..."

# Sync Python source files, templates, static assets, data
rsync -avz --delete \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='*.log' \
    --exclude='venv' \
    --exclude='.git' \
    --exclude='yolov8n.pt' \
    --exclude='static/generated/*' \
    --exclude='static/reels/*' \
    --exclude='static/thumbnails/*' \
    --exclude='static/uploads/*' \
    --exclude='static/temp_reels/*' \
    --exclude='.claude' \
    --exclude='.claude-flow' \
    --exclude='.mcp.json' \
    -e "ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no" \
    "${LOCAL_DIR}/" \
    "${VM_USER}@${VM_IP}:${REMOTE_DIR}/"

log_info "Code sync complete."

# ── STEP 3: RESTART APPLICATION ──
log_info "Restarting Flask application on VM..."

# Use Azure run-command to avoid SSH session being killed by pkill
az vm run-command invoke \
    --resource-group "$RG" \
    --name "$VM_NAME" \
    --command-id RunShellScript \
    --scripts "
pkill -f 'python3 app.py' 2>/dev/null || true
sleep 2
su - sabrika -c 'cd ${REMOTE_DIR} && . venv/bin/activate && nohup python3 app.py > ~/flask.log 2>&1 &'
sleep 3
curl -s http://localhost:5000/api/health
echo ''
" \
    --output none

log_info "Application restarted."

# ── STEP 4: HEALTH CHECK ──
log_info "Running health check..."

HEALTH=$(curl -sk --max-time 10 "https://${VM_IP}/api/health" 2>/dev/null || echo "FAILED")

if echo "$HEALTH" | grep -q '"status": "ok"'; then
    CODE_HASH=$(echo "$HEALTH" | grep -o '"code_hash": "[^"]*"' | cut -d'"' -f4)
    log_info "Health OK — code_hash: ${CODE_HASH}"
else
    log_error "Health check FAILED"
    log_error "Response: ${HEALTH}"
    exit 1
fi

# ── STEP 5: OPTIONAL POST-DEPLOY ACTIONS ──
for arg in "$@"; do
    case "$arg" in
        --logs)
            log_info "Tailing logs (Ctrl+C to exit)..."
            ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no \
                "${VM_USER}@${VM_IP}" "tail -f ~/flask.log"
            ;;
        --check)
            log_info "Full API check..."
            curl -sk "https://${VM_IP}/api/restaurants" | python3 -m json.tool | head -20
            ;;
    esac
done

log_info "Deployment complete. App live at: https://${VM_IP}/"
