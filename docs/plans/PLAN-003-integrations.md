# PLAN-003: Integration Roadmap — PicoCloth + HIX Field

**Status:** Draft — Research Required
**Horizon:** Now → 2 weeks (HIX), 2 weeks → 2 months (PicoCloth)
**Goal:** The product integrates with the user's existing infrastructure.

---

## Integration 1: HIX Field Subscription

### What We Know

- User has a "HIX field subscription"
- User wants to "embed this in there"
- User wants to "make sure the fields come out so good"

### What We Don't Know

- What is HIX? (SaaS platform? Form builder? CMS?)
- What are "fields" in HIX context? (Form fields? Content fields?)
- Does HIX support iframe embedding?
- Does HIX support custom HTML/CSS/JS?
- What are the sandboxing constraints?

### Research Tasks

| Task | Method | Time |
|------|--------|------|
| Identify HIX platform | Search web for "HIX field subscription" | 15 min |
| Read HIX documentation | Find embed/iframe/integration docs | 30 min |
| Test iframe embedding | Create minimal HTML page, embed in HIX | 1 hour |
| Document constraints | CSS limits, JS sandbox, CSP headers | 30 min |

### Hypotheses

**Hypothesis A: HIX is a form builder (like Typeform, JotForm)**
- Integration: Embed landing page as iframe in form
- Constraint: iframe may be sandboxed, no external JS
- Test: Create iframe snippet, try embedding

**Hypothesis B: HIX is a website builder (like Wix, Squarespace)**
- Integration: Custom HTML block with iframe or direct embed
- Constraint: CSS may conflict with HIX theme
- Test: Embed as custom HTML block

**Hypothesis C: HIX is a healthcare/EMR platform**
- Integration: Patient-facing portal with embedded content
- Constraint: Strict CSP, HIPAA considerations
- Test: Check if external domains are whitelisted

### Action Required

**User must provide:**
1. URL of HIX platform or login page
2. Screenshot of where they want to embed the landing page
3. Whether HIX allows custom HTML/iframe

---

## Integration 2: PicoCloth

### What We Know

- User has PicoCloth infrastructure at `~/.picocloth/`
- User has nodes: `node-a` through `node-e`
- User mentioned "project.resume" related to PicoCloth
- PicoCloth appears to be a distributed orchestration system

### What We Don't Know

- What does PicoCloth do? (Container orchestration? VM management? Process scheduling?)
- What runs on node-a through node-e?
- How does PicoCloth communicate? (HTTP? RPC? Shared filesystem?)
- What is `project.resume`? (A resume generator? A project state restoration tool?)

### Research Tasks

| Task | Method | Time |
|------|--------|------|
| Explore PicoCloth directory structure | `ls -la ~/.picocloth/` | 5 min |
| Read PicoCloth config files | Find README, config, or documentation | 15 min |
| Check node status | SSH to nodes, see what's running | 15 min |
| Understand project.resume | Read code, run it, see output | 15 min |
| Document architecture | Draw diagram of PicoCloth topology | 30 min |

### Hypotheses

**Hypothesis A: PicoCloth is a lightweight container orchestrator**
- Like Docker Compose but distributed across VMs
- Nodes run containers, central coordinator manages them
- Integration: Deploy Sabrika Brand Manager as a PicoCloth service

**Hypothesis B: PicoCloth is a distributed compute grid**
- Nodes process tasks in parallel
- Reel generation could be distributed across nodes
- Integration: Offload FFmpeg encoding to PicoCloth nodes

**Hypothesis C: PicoCloth is a development environment manager**
- Each node is a different dev/staging/prod environment
- Integration: Use PicoCloth for multi-environment management instead of systemd

### Action Required

**User must provide:**
1. Access to PicoCloth nodes (or run commands on this VM)
2. Explanation of what PicoCloth does
3. Whether they want Sabrika Brand Manager managed by PicoCloth

---

## Integration 3: Instagram API (Deferred)

### What We Know

- Instagram Graph API allows posting to Business/Creator accounts
- Requires Facebook Business account
- The Pakwaan likely has a personal Instagram account

### Decision Pending

If The Pakwaan converts to Business account:
- Implement Instagram Graph API posting
- Build content scheduler
- Track post performance

If The Pakwaan stays personal:
- Build reminder system ("Your content is ready")
- Integrate with Meta Business Suite (manual scheduler)
- Do not build API posting (impossible for personal accounts)

---

## Tasks (In Order)

1. **User provides HIX details** (waiting on user)
2. **Research HIX platform** (15 min web search)
3. **Test HIX embed with minimal page** (1 hour)
4. **User provides PicoCloth access/details** (waiting on user)
5. **Explore PicoCloth on this VM** (15 min)
6. **Document PicoCloth architecture** (30 min)
7. **Design integration approach** (1 hour)
8. **Build adapters** (varies)

---

## Success Criteria

- [ ] HIX platform identified and documented
- [ ] Landing page successfully embeds in HIX
- [ ] PicoCloth architecture documented
- [ ] Decision made: integrate with PicoCloth or keep systemd
- [ ] Instagram account type confirmed (personal vs business)
- [ ] Posting strategy defined (API vs manual vs scheduler)
