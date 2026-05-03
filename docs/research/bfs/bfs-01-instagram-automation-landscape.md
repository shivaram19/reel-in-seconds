# BFS-01: Instagram Automation for Restaurants — Landscape Mapping

**Date:** 2026-05-02
**Scope:** Open-source tools for automating Instagram Stories and Posts for small restaurant businesses
**Research Phase:** Breadth-First Landscape Scan
**Author:** Research Assembly for Sabrika Brand Manager

---

## 1. Problem Definition

A medical student (final-year MBBS, GVK Medical College, Almaty) manages social media for **two restaurants part-time**. Requirements:
- **2 Instagram Stories/day** per restaurant (organic, branded visuals)
- **1 Instagram Post/day** per restaurant (or weekly event posts)
- Must be **completely organic** in appearance — not robotic
- She interacts via a **simple UI** — enters context, restaurant name, event/offers
- System generates ready-to-publish images

**Constraint:** Must assemble from **open-source components** where possible. Zero or minimal recurring SaaS costs.

---

## 2. BFS Methodology

We scan across **four quadrants** simultaneously:

| Quadrant | Question | Key Search Terms |
|----------|----------|------------------|
| Q1: Publishing Layer | How do we get images onto Instagram? | "open source Instagram API", "instagrapi", "Instagram Graph API" |
| Q2: Content Generation | How do we create the images? | "open source AI image generation", "Stable Diffusion", "ComfyUI", "template generation" |
| Q3: Scheduling & Orchestration | How do we schedule and manage? | "open source social media scheduler", "Mixpost", "Postiz", "TryPost" |
| Q4: Interface Layer | What does she interact with? | "open source content management UI", "restaurant marketing automation" |

---

## 3. Quadrant Q1: Publishing Layer (Instagram → World)

### 3.1 Official Route: Instagram Graph API
- **Source:** Meta Developers Platform [^1]
- **License:** Proprietary API, free within rate limits
- **Capabilities:** Publish posts, stories, reels for **Business/Creator accounts only**
- **Rate Limit:** 200 calls/user/hour
- **Key Limitation:** Requires Facebook App Review (weeks), OAuth-only, no personal accounts

**Verdict for this use case:** Official and safe, but requires Business account conversion and app review. Best for long-term stability.

### 3.2 Unofficial Route: `instagrapi` (Python)
- **Source:** https://github.com/subzeroid/instagrapi [^2]
- **License:** MIT
- **Stars:** ~5,100+
- **Capabilities:** Upload photos, videos, stories, reels, albums; 2FA support; challenge resolver; story link stickers; insights
- **Last Validated:** 25 Dec 2024 (reverse-engineered via Charles Proxy)
- **Key Risk:** Uses private API — account ban risk if used aggressively; requires Instagram username/password

**Verdict for this use case:** Best unofficial library. Actively maintained. Use with **dedicated automation accounts** or accept risk on primary accounts. Not for production at scale without proxy rotation.

### 3.3 Alternative: `Ensta` (Python)
- **Source:** https://github.com/diezo/Ensta [^3]
- **License:** MIT
- **Capabilities:** Mobile + Web API; upload story with link stickers; direct messages; bio link management
- **Maturity:** Smaller community than instagrapi, but actively maintained

**Verdict:** Good fallback if instagrapi breaks. Less battle-tested.

### 3.4 Alternative: `instagram-private-api` (Node.js/Python)
- **Source:** https://github.com/ping/instagram_private_api [^4]
- **Status:** Legacy project, less active
- **Verdict:** Not recommended for new builds.

---

## 4. Quadrant Q2: Content Generation (Image Creation)

### 4.1 AI Image Generation: Stable Diffusion + ComfyUI
- **Source:** https://github.com/comfyanonymous/ComfyUI [^5]
- **License:** GPL-3.0
- **Stars:** 50,000+
- **Capabilities:** Node-based GUI for Stable Diffusion; supports SDXL, Flux, SD3.5; ControlNet for pose/depth; text-to-image and image-to-image
- **Hardware:** Requires GPU (NVIDIA preferred, 6GB+ VRAM); CPU mode available but slow
- **Deployment:** Local, cloud (RunPod, Vast.ai), or API-wrapped

**Verdict for this use case:** Best for **artistic/AI-generated** backgrounds. Overkill for simple branded text-on-gradient stories. Requires significant compute.

### 4.2 Template-Based Generation: Pillow + HTML/CSS
- **Source:** Python Pillow (PIL Fork) [^6]
- **License:** HPND (open source)
- **Capabilities:** Programmatic image generation; text rendering; gradients; shapes; overlays
- **Approach:** Python script renders 1080×1920 (story) and 1080×1080 (post) from templates + dynamic text
- **Pros:** Zero dependencies, instant, deterministic, brand-consistent
- **Cons:** Not "AI-generated" art — more like Canva-style branded graphics

**Verdict for this use case:** **Best fit for restaurant stories/posts.** Fast, free, on-brand, and outputs are predictable and professional.

### 4.3 Advanced Template Automation: CHILI GraFx (Open Core)
- **Source:** CHILI Publish [^7]
- **License:** Commercial with API (not fully open source)
- **Use Case:** FoodGenius (Germany) uses this to auto-generate weekly menus, social posts, WhatsApp updates from POS data [^7]
- **Verdict:** Proven in hospitality, but not open source. Reference architecture only.

### 4.4 Canva-Alternative Open Source: GIMP, Inkscape, Figma
- **GIMP:** Photo manipulation, not automation-friendly [^8]
- **Inkscape:** Vector graphics, scriptable via Python extensions [^8]
- **Figma:** Browser-based, has API but not open source [^8]
- **Verdict:** Not suitable for automated batch generation.

---

## 5. Quadrant Q3: Scheduling & Orchestration

### 5.1 Mixpost
- **Source:** https://github.com/inovector/mixpost [^9]
- **License:** MIT
- **Stack:** Laravel + Vue.js
- **Capabilities:** Multi-platform (Instagram, Facebook, X, LinkedIn, TikTok, etc.); content calendar; team workspaces; media library; analytics; queue management
- **Deployment:** Self-hosted (Docker available)
- **Instagram Support:** Uses official APIs where possible

**Verdict for this use case:** **Best open-source social media manager.** Mature, actively maintained, professional UI. Requires server for self-hosting.

### 5.2 Postiz
- **Source:** Postiz (open-source scheduler) [^10]
- **License:** Apache 2.0
- **Capabilities:** 15+ platforms including Reddit, Discord, Mastodon; AI image generation (DALL-E integration); Product Hunt #1 (2024)
- **Maturity:** Very new, rapid iteration, less stable

**Verdict:** Feature-rich but immature. Watch for production use.

### 5.3 TryPost
- **Source:** https://github.com/trypost-it/trypost [^11]
- **License:** Functional Source License (FSL) — free for self-host, cannot resell as SaaS
- **Stack:** Laravel 13 + Vue 3 + PostgreSQL + Redis
- **Capabilities:** Visual calendar; post composer; media library; team roles; REST API; MCP server for AI; unlimited accounts
- **Platforms:** Instagram, Facebook, X, LinkedIn, TikTok, YouTube, Pinterest, Threads, Bluesky, Mastodon

**Verdict:** Modern stack, AI-ready via MCP. Good alternative to Mixpost if Laravel 13 + AI integration is desired.

### 5.4 Socioboard 5.0
- **Source:** https://github.com/socioboard/Socioboard-5.0 [^12]
- **License:** Open source
- **Status:** Trusted by 20,000+ users, but older stack, less active recent development
- **Verdict:** Legacy option. Prefer Mixpost or TryPost for new builds.

---

## 6. Quadrant Q4: Interface Layer (What She Uses)

### 6.1 Web UI: Custom Flask/FastAPI + HTML
- **Approach:** Simple form → backend generates image → preview → download/post
- **Pros:** Fully customizable, lightweight, zero learning curve for her
- **Cons:** Requires building from scratch

### 6.2 No-Code/Low-Code: n8n + Mixpost API
- **Source:** n8n.io (fair-code, self-hostable)
- **Approach:** Form submission → n8n workflow → Mixpost/TryPost API → scheduled post
- **Verdict:** Over-engineered for 2 restaurants. Better to build minimal custom UI.

### 6.3 Mobile-First: React/Vue PWA
- **Approach:** Progressive Web App she can use on phone between classes
- **Pros:** Native-like experience, works offline for drafts
- **Cons:** More development effort

---

## 7. Cross-Cutting Concerns

| Concern | Finding |
|---------|---------|
| **Cost** | All core components (instagrapi, Pillow, Mixpost/TryPost) are free. Hosting is the only cost (~$5-10/mo on DigitalOcean/Railway). |
| **Account Safety** | Instagram Graph API is safest. instagrapi carries ban risk. Mitigate by posting during local business hours, not spamming. |
| **Image Quality** | Pillow templates = consistent branding. ComfyUI = artistic variety. Hybrid approach possible. |
| **Scalability** | Current scope: 2 restaurants × 3 posts/day = 6 images/day. Any solution handles this trivially. |
| **Maintenance** | Mixpost/TryPost require server updates. instagrapi may break with Instagram changes. Pillow templates are immortal. |

---

## 8. References

[^1]: Meta Developers. "Instagram Graph API." https://developers.facebook.com/docs/instagram-api/

[^2]: subzeroid. "instagrapi — Unofficial Instagram Private API for Python." GitHub, 2024. https://github.com/subzeroid/instagrapi

[^3]: diezo. "Ensta — Fast & Reliable Python Package for Instagram API." GitHub, 2023. https://github.com/diezo/Ensta

[^4]: ping. "instagram_private_api — A Python library to access Instagram's private API." GitHub, 2017. https://github.com/ping/instagram_private_api

[^5]: comfyanonymous. "ComfyUI — A powerful and modular stable diffusion GUI." GitHub, 2024. https://github.com/comfyanonymous/ComfyUI

[^6]: Python Pillow. "Pillow — Python Imaging Library (Fork)." https://python-pillow.org/

[^7]: CHILI Publish. "FoodGenius: Bringing Automated Marketing to Hospitality with CHILI GraFx." Case Study, 2026. https://www.chili-publish.com/customer-foodgenius-bringing-automated-marketing-to-hospitality-with-chili-grafx/

[^8]: Orshot. "10 Best Free Canva Alternatives for 2026." 2025. https://orshot.com/blog/free-canva-alternatives

[^9]: inovector. "Mixpost — Schedule, publish, and manage your social media content on your server." GitHub, 2022. https://github.com/inovector/mixpost

[^10]: Postiz. "Open-source social media scheduling." Product Hunt #1, 2024.

[^11]: trypost-it. "TryPost — Open-source social media scheduling for modern creators and teams." GitHub, 2026. https://github.com/trypost-it/trypost

[^12]: socioboard. "Socioboard-5.0 — World's first open source Social Technology Enabler." GitHub, 2016. https://github.com/socioboard/Socioboard-5.0
