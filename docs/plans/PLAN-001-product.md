# PLAN-001: Product Roadmap — The Pakwaan Instagram Automation

**Status:** Draft
**Horizon:** Now → 2 weeks
**Goal:** Ship a working product with landing page

---

## Current Product State

### What Works

| Feature | Endpoint | Status |
|---------|----------|--------|
| Restaurant CRUD | `/api/restaurants` | ✅ |
| Image generation (Stories) | `/api/generate` (type=story) | ✅ |
| Image generation (Posts) | `/api/generate` (type=post) | ✅ |
| Logo upload | `/api/upload-logo` | ✅ |
| V1 reel generation | `/api/reels` | ✅ |
| V2 reel generation (frame analysis) | `/api/reels/v2` | ✅ |
| Health check | `/api/health` | ✅ |
| Raw video upload | `/api/upload` | ✅ |

### What's Missing

| Feature | Why It Matters | Priority |
|---------|---------------|----------|
| Landing page | First impression. Discoverability. HIX embed. | P0 |
| Scheduled posting | Sabrika shouldn't manually post every day | P1 |
| Content calendar | Plan posts in advance | P2 |
| Analytics | Know which content performs best | P2 |
| Mobile-friendly UI | Sabrika manages from phone | P1 |
| Direct Instagram API posting | Remove manual download/upload step | P2 |

---

## Landing Page Design

### Design Language

Inspiration: `pbakaus/impeccable` and `nexu-io/open-design`

Key principles from Impeccable:
- No overused fonts (not Inter for everything)
- No purple-to-blue gradients
- No cards nested in cards
- No gray text on colored backgrounds
- Tinted neutrals, not pure black/gray
- Purposeful motion, not bounce/elastic easing

### Sections

1. **Hero** — The Pakwaan's story. Not "AI-powered tool." But "Authentic Indian flavors, served to Almaty's medical community."
2. **How It Works** — Upload clips → AI finds the best moments → Branded reel ready in minutes.
3. **Gallery** — Sample generated Stories and reels.
4. **For The Pakwaan** — Specific to this restaurant. Cuisine, location, audience.
5. **Try It** — Embedded form or link to the app.
6. **Footer** — Contact, location, hours.

### Technical Approach

- Static HTML + CSS (no build step)
- Served by nginx alongside the Flask app
- Path: `/` or `/landing`
- Assets in `static/landing/`
- Responsive (mobile-first)

---

## Scheduled Posting

### Research Needed

1. **Instagram Basic Display API** vs **Instagram Graph API**
   - Basic Display: Read-only. Can't post.
   - Graph API: Requires Facebook Business account, Instagram Business/Creator account.
   - The Pakwaan likely has a personal Instagram account, not Business.

2. **Alternative: Meta Business Suite**
   - Web-based scheduler. Free.
   - Manual but reliable.
   - Doesn't require API integration.

3. **Alternative: Third-party schedulers**
   - Buffer, Later, Hootsuite
   - Paid. $15–50/month.

### Decision Pending

If The Pakwaan's Instagram is a personal account, API posting is impossible. Options:
- A) Manual download from our tool + upload to Meta Business Suite
- B) Convert to Business account (may lose some features)
- C) Build a reminder system ("Your reel is ready. Tap to download and post.")

**Research task:** Determine The Pakwaan's Instagram account type.

---

## Content Calendar

Simple JSON-based calendar:
```json
{
  "2026-05-10": {"type": "story", "theme": "Sunday Special", "status": "pending"},
  "2026-05-12": {"type": "reel", "theme": "Cooking Process", "status": "generating"},
  "2026-05-15": {"type": "post", "theme": "Customer Review", "status": "done"}
}
```

Frontend: Simple calendar grid. Backend: CRUD endpoints.

---

## Mobile UI

Current frontend is vanilla HTML. It works on mobile but isn't optimized.

Quick wins:
- Viewport meta tag
- Touch-friendly buttons (min 44px)
- Bottom navigation bar
- Swipe gestures for gallery

---

## Tasks (In Order)

1. **Research The Pakwaan's Instagram account type** (5 min — ask user)
2. **Build landing page HTML/CSS** (4 hours)
3. **Add landing page route to nginx** (30 min)
4. **Generate sample content for gallery** (2 hours — run existing endpoints)
5. **Test landing page on mobile** (1 hour)
6. **Deploy to VM** (via CI/CD)
7. **Research HIX embed constraints** (see PLAN-003)
8. **Adapt landing page for HIX** (varies)

---

## Success Criteria

- [ ] Landing page loads at `https://20.125.62.241/`
- [ ] Landing page tells The Pakwaan's story
- [ ] Landing page shows sample generated content
- [ ] Landing page works on mobile
- [ ] Landing page can be embedded in HIX field
