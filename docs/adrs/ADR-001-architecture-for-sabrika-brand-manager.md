# ADR-001: Architecture for Sabrika Brand Manager

**Date:** 2026-05-02
**Status:** Proposed
**Deciders:** Research Assembly (BFS + DFS + Bidirectional Analysis)
**Scope:** Instagram content automation system for 2 restaurants, operated by a medical student

---

## 1. Context

Sabrika is a final-year MBBS student at GVK Medical College, Almaty, Kazakhstan. She manages Instagram content for **two restaurants part-time**. Current workload:
- **2 Instagram Stories/day** per restaurant (4 total)
- **1 Instagram Post/day** per restaurant (2 total), or weekly event variants
- Content must be **completely organic** in appearance
- She needs a **simple UI** — enter restaurant, context, event/offer → get publishable image

**Constraints:**
- Zero to minimal recurring costs
- Must work from Kazakhstan (international API availability)
- Operator is non-technical (medical background)
- Must not risk Instagram account bans (restaurants depend on social presence)
- System must be maintainable with near-zero ongoing effort

---

## 2. Decision Drivers

| Driver | Priority | Rationale |
|--------|----------|-----------|
| Account Safety | Critical | Restaurant Instagram bans = lost revenue |
| Cost | High | Student budget; no SaaS subscriptions |
| Simplicity | High | Must work without technical debugging |
| Speed | Medium | Generate images in <5 seconds |
| Visual Quality | Medium | Must look professional and on-brand |
| Scalability | Low | Fixed at 2 restaurants; unlikely to grow beyond 5 |

---

## 3. Considered Options

### Option A: All-in-One SaaS (Buffer, Later, Hootsuite)
- Buffer Free: 3 channels, 10 scheduled posts/channel [^1]
- Later Free: 1 social set, 5 posts/month [^1]
- Hootsuite: $149/mo minimum [^2]

**Rejected:** Buffer/Later free tiers too restrictive. Paid tiers violate cost constraint. No image generation included.

### Option B: Self-Hosted Social Manager (Mixpost / TryPost / Postiz)
- Mixpost: Laravel + Vue, MIT license, mature [^3]
- TryPost: Laravel 13 + Vue 3, FSL license, AI-ready [^4]
- Postiz: Apache 2.0, 15+ platforms, immature [^5]

**Partially Accepted:** Mixpost is the best open-source scheduler. However, it solves "when to post" not "what to post." Image generation still needed separately. Will be evaluated for Phase 2 scheduling layer.

### Option C: Unofficial API (instagrapi) + Custom UI
- instagrapi: MIT license, 5,100+ stars, reverse-engineered [^6]
- Full mobile API feature parity
- Account ban risk: Medium-High

**Rejected as primary:** Ban risk unacceptable for restaurant accounts. Accepted as **fallback** if official API proves insufficient.

### Option D: Official API (Graph API) + Custom Generator + Simple UI
- Instagram Graph API: Official, safe, free [^7]
- Pillow: Template-based image generation, zero cost [^8]
- Optional: ComfyUI for AI backgrounds (monthly batch) [^9]
- Custom Flask/FastAPI UI: Tailored to exact workflow

**ACCEPTED as primary architecture.**

---

## 4. Decision

> **Adopt a Hybrid Architecture: Official API + Template Generation + Optional AI Enhancement**

### 4.1 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SABRIKA BRAND MANAGER                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │   Web UI     │───→│   Backend    │───→│   Image      │         │
│  │  (Simple     │    │  (Flask/     │    │  Generator   │         │
│  │   Forms)     │←───│   FastAPI)   │←───│  (Pillow)    │         │
│  └──────────────┘    └──────┬───────┘    └──────────────┘         │
│                             │                                       │
│                             ↓                                       │
│                    ┌─────────────────┐                             │
│                    │  Content Store  │                             │
│                    │  (JSON/SQLite)  │                             │
│                    └─────────────────┘                             │
│                             │                                       │
│              ┌──────────────┼──────────────┐                      │
│              ↓              ↓              ↓                      │
│       ┌──────────┐   ┌──────────┐   ┌──────────┐                │
│       │  Graph   │   │  Manual  │   │  Archive │                │
│       │   API    │   │ Download │   │  (Logs)  │                │
│       │(Primary) │   │(Fallback)│   │          │                │
│       └────┬─────┘   └────┬─────┘   └──────────┘                │
│            │              │                                        │
│            ↓              ↓                                        │
│       ┌─────────────────────────┐                                │
│       │      INSTAGRAM          │                                │
│       │  (Stories + Posts)      │                                │
│       └─────────────────────────┘                                │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│  OPTIONAL MODULES (Phase 2)                                          │
│  ├── ComfyUI Background Generator (monthly batch)                   │
│  ├── Local LLM Caption Generator (Llama 3.2 / Qwen 2.5)             │
│  ├── Mixpost Scheduler (self-hosted)                                │
│  └── Real-ESRGAN Photo Enhancement (for real restaurant photos)     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Component Decisions

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Backend** | Python Flask | Lightweight, single-file deploy, vast ecosystem |
| **Image Gen** | Pillow (PIL) | Zero dependencies, sub-second generation, deterministic |
| **AI Backgrounds** | ComfyUI + SDXL (optional) | Monthly batch of 20 backgrounds per restaurant |
| **Database** | JSON files or SQLite | No DB server needed for 2 restaurants |
| **UI** | HTML + Jinja2 templates | Simple forms, no JavaScript framework needed |
| **Publishing** | Instagram Graph API | Official, safe, free |
| **Captions** | Local LLM (Llama 3.2 3B) | Free, offline, privacy-preserving |
| **Hosting** | Railway / Render / DigitalOcean | $5-10/mo, one-click deploy |

---

## 5. Consequences

### 5.1 Positive

- **Account Safety:** Graph API is sanctioned by Meta. Near-zero ban risk.
- **Cost:** All core software is free and open-source. Hosting only cost.
- **Simplicity:** She enters text → sees preview → downloads or publishes.
- **Speed:** Images generate in <2 seconds. No waiting.
- **Brand Consistency:** Templates enforce colors, fonts, logo placement.
- **Maintainability:** Flask + Pillow are stable, well-documented, immortal.

### 5.2 Negative

- **Setup Effort:** Requires initial development (this repository).
- **Graph API Limitations:** Stories cannot have interactive stickers via API. She must add these manually in the app (2 minutes per story).
- **No Native Scheduling:** Phase 1 requires her to click "publish" or download and upload manually. Phase 2 adds Mixpost for true scheduling.
- **Template Variety:** Requires creating 5-10 template designs to avoid repetition.

### 5.3 Mitigations

| Negative | Mitigation |
|----------|-----------|
| Manual sticker addition | Send her a notification 5 min before scheduled post time |
| Template repetition | Pre-build 10 templates; randomize selection |
| No native scheduling | Phase 2 integrates Mixpost or uses Graph API `published_until` |

---

## 6. Alternatives Not Chosen

| Alternative | Why Rejected |
|-------------|--------------|
| instagrapi as primary | Account ban risk unacceptable for business accounts |
| Mixpost as primary | Solves scheduling but not image generation; overkill for 2 restaurants |
| ComfyUI as primary | Too slow for daily use; overkill for simple text-on-image content |
| DALL-E / Midjourney API | Recurring cost; violates zero-cost constraint |
| Buffer paid plans | $5-15/mo per channel; scales poorly |

---

## 7. Validation

This architecture satisfies all decision drivers:

| Driver | Requirement | How Addressed |
|--------|-------------|---------------|
| Account Safety | Zero ban risk | Instagram Graph API is official |
| Cost | <$10/month | All software free; hosting only cost |
| Simplicity | No debugging | Flask + Pillow are rock-stable |
| Speed | <5 sec generation | Pillow renders in <1 sec |
| Visual Quality | Professional | Template-based with brand enforcement |
| Scalability | 2-5 restaurants | JSON/SQLite handles this trivially |

---

## 8. Implementation Phases

### Phase 1: MVP (Week 1-2)
- [ ] Flask app with restaurant CRUD
- [ ] 5 story templates + 5 post templates (Pillow)
- [ ] Image generation endpoint
- [ ] Download generated images
- [ ] Manual upload to Instagram

### Phase 2: Publishing (Week 3-4)
- [ ] Instagram Graph API integration
- [ ] OAuth flow for both restaurants
- [ ] Direct publish from UI
- [ ] Basic scheduling (`published_until`)

### Phase 3: Enhancement (Month 2)
- [ ] ComfyUI background generation (monthly batch)
- [ ] Local LLM caption generation
- [ ] Template variety expansion (10+ designs)
- [ ] Mobile-responsive PWA UI

### Phase 4: Scale (Future)
- [ ] Mixpost integration for advanced scheduling
- [ ] Photo enhancement pipeline (Real-ESRGAN)
- [ ] Analytics dashboard (Graph API insights)
- [ ] WhatsApp/Facebook cross-posting

---

## 9. References

[^1]: EvergreenFeed. "12 Best Free Social Media Scheduler Tools for 2025." November 2025. https://www.evergreenfeed.com/blog/free-social-media-scheduler/

[^2]: Microposter. "12 Best Free Social Media Management Tools for 2025." December 2025. https://microposter.so/blog/best-free-social-media-management-tools

[^3]: inovector. "Mixpost — Schedule, publish, and manage your social media content on your server." GitHub, 2022. https://github.com/inovector/mixpost

[^4]: trypost-it. "TryPost — Open-source social media scheduling." GitHub, 2026. https://github.com/trypost-it/trypost

[^5]: Postiz. "Open-source social media scheduler." Product Hunt #1, 2024.

[^6]: subzeroid. "instagrapi — Unofficial Instagram Private API for Python." GitHub, 2024. https://github.com/subzeroid/instagrapi

[^7]: Meta Developers. "Instagram Graph API — Content Publishing." https://developers.facebook.com/docs/instagram-api/guides/content-publishing/

[^8]: Python Pillow. "Pillow — Python Imaging Library (Fork)." https://python-pillow.org/

[^9]: comfyanonymous. "ComfyUI — A powerful and modular stable diffusion GUI." GitHub, 2024. https://github.com/comfyanonymous/ComfyUI
