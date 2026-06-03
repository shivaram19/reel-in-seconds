# PLAN-002: Process Roadmap — Self-Improving Development Ecosystem

**Status:** Draft
**Horizon:** 2 weeks → 2 months
**Goal:** The development process learns from itself. The system runs without human intervention.

---

## Current Process State

### What Works

| Component | How It Works | Status |
|-----------|-------------|--------|
| GitHub repository | `shivaram19/reel-in-seconds` | ✅ |
| CI/CD pipeline | Test → security scan → auto-deploy | ✅ |
| Dev environment | Port 5001, manual start/stop | ✅ (inactive) |
| Staging environment | Port 5002, manual start/stop | ✅ (inactive) |
| Production environment | Port 5000, nginx + SSL | ✅ (active) |
| Self-healing monitor | Probes /api/health, restarts on failure | ✅ |
| Mission monitor | Semantic health checks | ✅ (manual run) |
| Test suite | pytest for API endpoints | ✅ |

### What's Missing

| Component | Why It Matters | Priority |
|-----------|---------------|----------|
| Runtime consciousness | System reads its own history and learns | P1 |
| Predictive failure detection | Alert before crash, not after | P1 |
| Automatic rollback | Failed deploy reverts automatically | P2 |
| Builder consciousness (agent) | Daily log of decisions and evolution | P1 |
| Feedback loop integration | RL hub reads sessions, updates skills | P2 |
| Load testing | Know capacity limits before users do | P2 |

---

## Runtime Consciousness

### The Problem

The consciousness log lives in `.kimi/skills/sre-devops/consciousness/` — a directory the running VM never reads. The monitor restarts Flask but doesn't know *why* it crashed yesterday.

### The Solution

Two consciousness streams:

**Stream 1: Builder Consciousness (External)**
- Location: `.kimi/skills/sre-devops/consciousness/`
- Audience: Future agent sessions (humans or AI)
- Content: Architecture decisions, mistake patterns, evolution of thinking
- Format: Markdown, human-readable

**Stream 2: Runtime Consciousness (Internal)**
- Location: `~/.monitor/consciousness.json` on Azure VM
- Audience: The running monitor daemon
- Content: Failure patterns, recovery times, resource correlations
- Format: JSON, machine-readable

### Implementation

```json
// ~/.monitor/consciousness.json
{
  "version": 1,
  "learned_patterns": [
    {
      "pattern_id": "oom-after-reel-gen",
      "trigger": "memory_used_pct > 90 AND last_action == 'reel_generation'",
      "confidence": 0.85,
      "occurrences": 3,
      "first_seen": "2026-05-03T11:00:00Z",
      "last_seen": "2026-05-05T14:00:00Z",
      "action": "preemptively_restart_before_next_reel"
    }
  ],
  "deployment_history": [
    {
      "commit_hash": "503b706",
      "deployed_at": "2026-05-05T13:19:00Z",
      "health_after_1h": "healthy",
      "errors_in_first_hour": 0
    }
  ]
}
```

The monitor reads this file before making restart decisions. If it sees a pattern like "last 3 OOMs happened during reel generation," it can preemptively restart Flask before the next reel job starts.

---

## Predictive Failure Detection

### Current Behavior (Reactive)

```
Probe fails → Wait 30s → Probe fails again → Restart
```

### Desired Behavior (Predictive)

```
Memory trending up for 5 min → Predict OOM in 2 min → Preemptive restart
Disk trending up for 10 min → Predict full disk in 1 hour → Alert + cleanup
Error rate spiking → Predict crash in 5 min → Restart now
```

### Implementation

Simple linear regression on time-series data from `state.json`:

```python
def predict_oom_in_minutes(memory_history):
    """Given last 10 memory readings, predict minutes until 100%."""
    # Fit line: memory_pct = slope * time + intercept
    # Solve for time when memory_pct = 100
    pass
```

No ML needed. Simple math is sufficient for single-variable prediction.

---

## Automatic Rollback

### Current Behavior

Failed deploy = manual intervention. Human must SSH in and fix.

### Desired Behavior

```
Deploy → Health check fails for 5 min → Automatically revert to previous commit
```

### Implementation

1. Before deploy, snapshot current commit hash
2. Deploy new code
3. Run health checks for 5 minutes
4. If health fails, checkout previous commit and restart
5. Log rollback event

---

## Builder Consciousness (Agent)

### Current State

One log file: `2026-05-03.md`. Good start. Not enough.

### Desired State

- Daily log, every day, no exceptions
- Tag each entry with: decision, mistake, correction, evolution
- Cross-reference with RL hub feedback
- Quarterly summary: "What did I learn this quarter?"

### Format

```markdown
# Consciousness Log: YYYY-MM-DD

## Decisions
- [D1] Chose X over Y because...

## Mistakes
- [M1] Assumed Z. Falsified by...

## Corrections
- [C1] Fixed M1 by...

## Evolution
- How did today's thinking differ from yesterday's?

## RL Hub Feedback
- Link to feedback annotation: ...
```

---

## Tasks (In Order)

1. **Implement runtime consciousness JSON** (2 hours)
2. **Add pattern learning to monitor** (4 hours)
3. **Add predictive failure detection** (4 hours)
4. **Add automatic rollback** (4 hours)
5. **Create daily consciousness habit** (ongoing)
6. **Integrate with RL hub** (8 hours)
7. **Load test the system** (4 hours)

---

## Success Criteria

- [ ] Monitor reads runtime consciousness before making decisions
- [ ] System predicts OOM 2 minutes before it happens
- [ ] Failed deploy automatically rolls back within 5 minutes
- [ ] Daily consciousness log exists for every day of development
- [ ] RL hub can read consciousness logs and propose skill updates
- [ ] Load test confirms system can handle 10 concurrent users
