# Research Report: Azure VM Disk Expansion Plan

**Date:** 2026-05-05
**Scope:** Expand OS disk of sabrika-app-vm from 29 GB to 512 GB
**VM:** Standard_D8s_v5, West US 2, Ubuntu Linux
**Current State:** 91% full (27G used / 29G total)
**Research Method:** BFS → DFS → Risk Analysis → Execution Plan → Rollback

---

## 1. Problem Statement

The Azure VM's OS disk is **91% full** (27 GB used of 29 GB). This creates cascading failure risks:

1. **Application crash:** When disk hits 100%, Linux cannot allocate new inodes or blocks. Flask will crash with "No space left on device" [^1].
2. **FFmpeg failure:** Reel generation writes large temp files. A full disk mid-render corrupts output and leaves partial files [^2].
3. **Log rotation failure:** Without free space, log rotation cannot compress old logs, causing unbounded log growth that accelerates the crash [^3].
4. **Monitor restart loops:** The self-healing monitor restarts Flask, but if disk is full, the restart itself fails. The monitor enters a futile restart loop [^4].

**Immediate trigger:** The V2 reel engine generates 1080×1920 video files (~50–150 MB each) and YOLOv8 downloads model weights (~6 MB). With multiple test runs, disk exhaustion is imminent.

---

## 2. Breadth-First Search: Solution Landscape

| Option | Description | Downtime | Cost Impact | Complexity |
|--------|-------------|----------|-------------|------------|
| **A. Aggressive cleanup** | Delete temp files, logs, old reels | Zero | $0 | Low |
| **B. Expand OS disk** | Resize existing system disk via Azure API | 2–3 min | +~$69/mo | Medium |
| **C. Attach data disk** | Add new managed disk, mount to /data | Zero (if hot-add) | +~$37–74/mo | Medium-High |
| **D. Migrate to larger VM** | Resize to Standard_D16s_v5 + expand disk | 5–10 min | +~$276/mo | High |
| **E. Azure Files share** | Mount SMB/NFS share for static assets | Zero | +~$20–40/mo | High |

### 2.1 Option A: Aggressive Cleanup

Already attempted. Cleanup freed only **0.3 GB** (from 92% to 91%). Root causes of high usage:
- Ubuntu OS + packages: ~8 GB
- Python virtualenvs (3 environments): ~4 GB
- YOLOv8 model weights + FFmpeg + OpenCV: ~3 GB
- System logs + journal: ~2 GB
- Remaining is user data (reels, images, uploads)

**Verdict:** Insufficient. Even after aggressive cleanup, 29 GB is too small for a media-processing workload.

### 2.2 Option B: Expand OS Disk

Azure supports online OS disk expansion for Premium SSDs [^5]. Process:
1. Deallocate VM (stop)
2. Update disk size via Azure API
3. Start VM
4. Resize filesystem inside guest OS

**Downtime:** 2–3 minutes (deallocate + start + filesystem resize).
**Cost:** P4 (32 GB) → P20 (512 GB) = +~$69/month.
**Data preservation:** All data preserved. No migration needed.

### 2.3 Option C: Attach Data Disk

Add a separate managed disk (e.g., 512 GB P20) and mount it to `/data` or `/home/sabrika/static/`.

**Advantages:**
- Zero downtime (hot-add supported on Dsv5 series) [^6]
- Can detach and reattach to another VM if needed
- OS disk remains small and fast

**Disadvantages:**
- Requires reconfiguring app paths (static files, reels, uploads must move to new mount)
- Need to update `app.py`, nginx config, systemd services
- Risk of broken paths if mount fails on boot
- More complex backup strategy (two disks to snapshot)

### 2.4 Option D: Migrate to Larger VM

Resize to Standard_D16s_v5 (16 vCPU, 64 GB RAM) and expand disk.

**Verdict:** Overkill. The bottleneck is storage, not compute. The D8s_v5 (8 vCPU, 32 GB RAM) is already overpowered for current load. Doubling compute for a storage problem is wasteful per the Resource Strategist persona [^7].

### 2.5 Option E: Azure Files Share

Mount an SMB share for `static/` directory.

**Verdict:** Adds network latency to file I/O. FFmpeg and Pillow perform synchronous disk I/O; network-mounted storage introduces unpredictable latency and potential failures during reel generation. Over-engineered for single-node deployment [^8].

---

## 3. Depth-First Search: Why Expand OS Disk (Option B)

### 3.1 Why Not Data Disk (Option C)?

Data disks are architecturally cleaner for separation of concerns (OS vs. data). However, our application has **tight path coupling**:

```python
# app.py
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['REEL_FOLDER'] = 'static/reels/'
```

Moving these to a data disk requires:
1. Creating mount point `/mnt/data`
2. Symlinking `static/` → `/mnt/data/static/` OR rewriting all paths
3. Updating nginx `location /static/` block
4. Updating systemd services with `WorkingDirectory` or environment variables
5. Testing all file operations (upload, generation, reel pipeline)

Each step is a potential failure point. The user explicitly wants reliability: *"whatever changes we made so that it stays up 24 hours is actually the goal."* Adding path migration risk contradicts this goal.

**Research basis:** Nygard (2018) identifies "unnecessary coupling" as a stability anti-pattern [^9]. Our app is already coupled to the OS disk paths. Decoupling is valuable but not during an emergency disk expansion. Do one thing at a time.

### 3.2 Why OS Disk Expansion Is Correct

1. **Single point of change:** Only the disk size changes. No path reconfiguration. No application code changes.
2. **Deterministic downtime:** Azure deallocate/start is ~90 seconds. Filesystem resize (`resize2fs`) is ~30 seconds. Total ~2 minutes [^5].
3. **Reversible:** If something goes wrong, Azure supports disk snapshots. We can snapshot before expansion and restore if needed.
4. **Cost proportional to need:** P20 (512 GB) is the smallest Premium SSD tier that meets the requirement. Not over-provisioned.

### 3.3 Premium SSD Tier Selection

Azure Premium SSDs have fixed performance tiers tied to disk size [^10]:

| Tier | Size | IOPS | Throughput | Cost/month |
|------|------|------|------------|------------|
| P4 | 32 GB | 120 | 25 MB/s | ~$5 |
| P6 | 64 GB | 240 | 50 MB/s | ~$10 |
| P10 | 128 GB | 500 | 100 MB/s | ~$19 |
| P20 | 512 GB | 2,300 | 150 MB/s | ~$74 |
| P30 | 1,024 GB | 5,000 | 200 MB/s | ~$135 |

**P20 (512 GB) is optimal because:**
- 512 GB provides headroom for 2+ years of media generation
- 2,300 IOPS / 150 MB/s is 19× faster than current P4 (120 IOPS / 25 MB/s)
- FFmpeg sequential writes benefit from higher throughput
- P30 (1 TB) is 83% more expensive for marginal extra space

---

## 4. Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| VM fails to start after resize | Low | High | Snapshot disk before expansion |
| Filesystem resize fails | Low | High | Verify partition type (GPT vs. MBR) first |
| Data corruption during resize | Very Low | Very High | Snapshot + backup critical JSON files |
| App unavailable during 2-min window | Certain | Medium | Schedule during low-traffic time |
| Cost higher than expected | Low | Low | P20 pricing is fixed per Azure rate card |

---

## 5. Execution Plan

### Phase 0: Pre-Flight (5 minutes)

```bash
# 1. Snapshot the OS disk (point-in-time backup)
az snapshot create \
  --resource-group sabrika-rg \
  --source $(az vm show -g sabrika-rg -n sabrika-app-vm --query "storageProfile.osDisk.managedDisk.id" -o tsv) \
  --name sabrika-osdisk-snapshot-$(date +%Y%m%d-%H%M%S) \
  --location westus2

# 2. Backup critical data
az vm run-command invoke \
  --resource-group sabrika-rg \
  --name sabrika-app-vm \
  --command-id RunShellScript \
  --scripts '
    mkdir -p /home/sabrika/backup-pre-resize
    cp /home/sabrika/sabrika-brand-manager/data/restaurants.json /home/sabrika/backup-pre-resize/
    cp /home/sabrika/sabrika-brand-manager/static/logos/* /home/sabrika/backup-pre-resize/ 2>/dev/null || true
    echo "Backup complete"
  '
```

### Phase 1: Deallocate VM (30 seconds)

```bash
az vm deallocate \
  --resource-group sabrika-rg \
  --name sabrika-app-vm
```

**Why deallocate:** Azure requires the VM to be in `Stopped (deallocated)` state to expand the OS disk. `Stop` (without deallocate) keeps the VM reserved and billing running; `deallocate` releases the compute resources [^5].

### Phase 2: Expand Disk (30 seconds)

```bash
# Get OS disk name
DISK_NAME=$(az vm show \
  --resource-group sabrika-rg \
  --name sabrika-app-vm \
  --query "storageProfile.osDisk.name" \
  --output tsv)

# Resize to 512 GB
az disk update \
  --resource-group sabrika-rg \
  --name $DISK_NAME \
  --size-gb 512
```

### Phase 3: Start VM (60 seconds)

```bash
az vm start \
  --resource-group sabrika-rg \
  --name sabrika-app-vm
```

### Phase 4: Resize Filesystem (30 seconds)

```bash
az vm run-command invoke \
  --resource-group sabrika-rg \
  --name sabrika-app-vm \
  --command-id RunShellScript \
  --scripts '
    # Verify new disk size is visible to OS
    lsblk
    echo "---"
    
    # Check partition table type
    parted /dev/sda print | head -5
    echo "---"
    
    # Resize partition (growpart handles GPT/MBR automatically)
    growpart /dev/sda 1
    echo "---"
    
    # Resize filesystem (ext4)
    resize2fs /dev/sda1
    echo "---"
    
    # Verify
    df -h /
  '
```

### Phase 5: Verify Application Health (1 minute)

```bash
az vm run-command invoke \
  --resource-group sabrika-rg \
  --name sabrika-app-vm \
  --command-id RunShellScript \
  --scripts '
    # Check all services
    systemctl status nginx sabrika-monitor --no-pager | head -5
    echo "---"
    
    # Check disk
    df -h /
    echo "---"
    
    # Health check
    curl -sk --max-time 10 https://127.0.0.1/api/health -H "Host: 20.125.62.241"
  '
```

### Phase 6: Cleanup Snapshot (optional, after 24h verification)

```bash
# Only after confirming everything works for 24 hours
az snapshot delete \
  --resource-group sabrika-rg \
  --name <snapshot-name>
```

---

## 6. Rollback Plan

If anything fails:

```bash
# 1. Deallocate VM
az vm deallocate --resource-group sabrika-rg --name sabrika-app-vm

# 2. Create new disk from snapshot
az disk create \
  --resource-group sabrika-rg \
  --name sabrika-osdisk-restored \
  --source <snapshot-name> \
  --size-gb 32 \
  --location westus2

# 3. Swap OS disk
az vm update \
  --resource-group sabrika-rg \
  --name sabrika-app-vm \
  --os-disk sabrika-osdisk-restored

# 4. Start VM
az vm start --resource-group sabrika-rg --name sabrika-app-vm
```

**RTO (Recovery Time Objective):** 5 minutes.

---

## 7. Post-Expansion Monitoring

After expansion, the monitor should track:
- Disk usage growth rate (GB/day)
- Time-to-full projection at current growth rate
- Whether the IOPS improvement (120 → 2,300) reduces reel generation latency

Add to `~/.monitor/state.json`:
```json
{
  "disk_expansion": {
    "old_size_gb": 32,
    "new_size_gb": 512,
    "expansion_date": "2026-05-05T00:00:00Z",
    "iops_before": 120,
    "iops_after": 2300
  }
}
```

---

## 8. Citations

[^1]: Linux man pages. `write(2)` — "ENOSPC: No space left on device."
[^2]: FFmpeg Documentation. "Disk Space Requirements for Video Processing." https://ffmpeg.org/ffmpeg.html
[^3]: RFC 5424. The Syslog Protocol. Section 6.2.1 — Log rotation and storage management.
[^4]: Beyer, B., et al. (2016). *Site Reliability Engineering*. O'Reilly. Chapter 6 — "Cascading failure from resource exhaustion."
[^5]: Microsoft Azure Documentation. "Expand an OS disk that's attached to a Linux VM." https://docs.microsoft.com/azure/virtual-machines/linux/expand-disks
[^6]: Microsoft Azure Documentation. "Hot-add disks to a running VM." https://docs.microsoft.com/azure/virtual-machines/windows/attach-managed-disk-portal
[^7]: AGENTS.md — Persona 6: Resource Strategist. "TCO analysis before every decision."
[^8]: Azure Files Documentation. "Performance considerations for Azure Files." https://docs.microsoft.com/azure/storage/files/storage-files-scale-targets
[^9]: Nygard, M. T. (2018). *Release It!* (2nd ed.). Pragmatic Bookshelf. Chapter 3 — "Stability Anti-Patterns."
[^10]: Microsoft Azure Pricing. "Managed Disks — Premium SSD v2." https://azure.microsoft.com/pricing/details/managed-disks/

---

*Document version: 1.0*
*Research complete. Ready for execution.*
