# Roadmap: Where We're Heading

**Date:** 2026-05-05
**Status:** Cutting research complete. Ready for execution.
**Method:** AGENTS.md-driven decomposition → Task registry → Plan documents

---

## The Core Insight

After introspection, the destination is not a platform, a mind, or a research artifact. It is three layers, each with its own needs:

| Layer | What It Is | Current State | Gap |
|-------|-----------|---------------|-----|
| **Product** | Instagram automation for The Pakwaan | Backend works (V2 reel engine, image generator). No landing page. No user-facing polish. | Landing page, HIX embed, scheduled posting |
| **Process** | Self-improving development ecosystem | CI/CD works. Monitor works. Consciousness exists but is external to runtime. | Runtime consciousness, PicoCloth orchestration |
| **Integrations** | Where the product lives and operates | PicoCloth exists but un-investigated. HIX mentioned but un-researched. | Research both, build adapters |

---

## The Cutting Research

"Cutting research" means: cut through assumptions, cut to what matters, cut the rest.

### What We Cut (Intentionally Removed)

1. **Multi-tenant architecture** — Cut. The user manages one restaurant. JSON files are correct.
2. **Platform scale assumptions** — Cut. D8s_v5 is oversized but that's fine. Don't architect for 100 users.
3. **PostgreSQL migration** — Cut. JSON persistence is sufficient for one restaurant.
4. **Job queue (Celery/RQ)** — Cut. Reel generation is synchronous for one user. Queue adds complexity with no benefit.
5. **Disk expansion to 512 GB** — Cut (deferred). 91% is tight but not critical yet. Clean up first, expand only if needed.

### What We Keep (Validated by User Intent)

1. **V2 reel engine** — Keep. User explicitly tested and validated this.
2. **Self-healing monitor** — Keep. User wants 24/7 uptime.
3. **CI/CD pipeline** — Keep. User wants develop-here, deploy-there.
4. **Landing page** — Keep. User explicitly asked for this.
5. **PicoCloth integration** — Keep. User mentioned it multiple times.
6. **HIX field integration** — Keep. User explicitly wants to embed there.
7. **Daily consciousness** — Keep. User explicitly asked for "new file every day."

---

## Three Horizons

### Horizon 1: Now → 2 Weeks (Ship the Product)

**Goal:** The Pakwaan has a working Instagram automation tool with a landing page.

| Task | Deliverable | Owner |
|------|-------------|-------|
| Research HIX field constraints | `docs/plans/PLAN-003-integrations.md` | Agent |
| Research PicoCluth architecture | `docs/plans/PLAN-003-integrations.md` | Agent |
| Build landing page (impeccable/open-design style) | `templates/landing.html` + `static/landing/` | Agent |
| Deploy landing page to VM | Live at `https://20.125.62.241/` | CI/CD |
| Test landing page in HIX field | Validation report | User + Agent |
| Clean up disk (aggressive, no expansion) | > 10 GB free | Agent |

### Horizon 2: 2 Weeks → 2 Months (Make It Reliable)

**Goal:** The system runs without human intervention. The development process learns from itself.

| Task | Deliverable | Owner |
|------|-------------|-------|
| Runtime consciousness | `~/.monitor/consciousness.json` | Agent |
| Predictive failure detection | Monitor alerts before crash | Agent |
| Instagram API integration (if possible) | Direct posting via Graph API | Agent |
| Scheduled content generation | Cron-based or scheduler | Agent |
| User testing with The Pakwaan | Feedback annotations | User |

### Horizon 3: 2 Months → 6 Months (Make It Intelligent)

**Goal:** The system understands The Pakwaan's brand and improves content quality over time.

| Task | Deliverable | Owner |
|------|-------------|-------|
| Content performance tracking | Which posts perform best? | Agent |
| A/B testing framework | Test variations of Stories | Agent |
| PicoCloth orchestration | Distributed generation across nodes | Agent + User |
| Brand voice training | Fine-tuned copy for The Pakwaan | Agent |
| Multi-restaurant support (if user wants) | Auth + tenant isolation | Agent |

---

## The Real Constraint

Not technology. Not cost. **Time and attention.**

Sabrika is a final-year MBBS student. She has exams, clinical rotations, and a life outside Instagram management. The tool must save her time, not consume it.

**Every feature must answer:** "Does this reduce Sabrika's weekly Instagram workload?"

If the answer is no, cut it.

---

## Next Action

Read `docs/plans/PLAN-001-product.md`, `PLAN-002-process.md`, and `PLAN-003-integrations.md`.

Pick the first task. Execute.
