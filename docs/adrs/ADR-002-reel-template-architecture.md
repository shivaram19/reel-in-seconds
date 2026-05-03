# ADR-002: Reel Template Architecture for Sabrika Brand Manager

**Date:** 2026-05-02
**Status:** Proposed
**Deciders:** Research Assembly (BFS + DFS + Bidirectional Analysis)
**Scope:** Professional automated reel generation from raw clips for Hyderabadi/Andhra restaurants

---

## 1. Context

The user (Sabrika's brother) has elevated requirements beyond basic video assembly:

> "It's not about restaurant, it's about bringing out a reel that's professional when clips are dropped in... concentrate on how to edit as per the clips... editing that must be professional."

**Domain:** Hyderabadi/Andhra Indian restaurants in Almaty, Kazakhstan
**Input:** Raw phone/camera clips (unedited, variable quality)
**Output:** Professional Instagram Reels (1080×1920, 9:16)
**Constraint:** Must feel intentional, human, culturally authentic — not AI-generic

---

## 2. Decision Drivers

| Driver | Priority | Rationale |
|--------|----------|-----------|
| **Professional Quality** | Critical | Reels represent the restaurant brand |
| **Cultural Authenticity** | High | Hyderabadi cuisine has specific visual language |
| **Automation** | High | Medical student operator, no editing time |
| **Template Flexibility** | High | Must adapt to different events/moods |
| **Cost** | High | Zero recurring SaaS costs |
| **Speed** | Medium | Under 2 minutes generation time acceptable |

---

## 3. Considered Options

### Option A: Manual Editing + Canva/CapCut Templates
- Use CapCut/Filmora templates manually
- **Rejected:** Requires Sabrika to learn editing, violates automation goal

### Option B: Commercial AI Reel Generators (Opus Clip, Koro, InVideo)
- SaaS tools with AI assembly
- **Rejected:** Recurring costs ($15-99/mo), not restaurant-domain-specific, proprietary [^1][^2]

### Option C: MoviePy Python Scripting
- Pythonic video composition
- **Rejected:** 10-50x slower than FFmpeg, memory issues with long clips [^3]

### Option D: Remotion (React-Based)
- Programmatic React video generation
- **Rejected:** Requires Node.js/React stack, slower rendering, overkill for this use case [^3]

### Option E: FFmpeg + PySceneDetect + Template Engine (RECOMMENDED)
- Open-source CLI pipeline with scene detection
- **Accepted:** Fast, free, fully customizable, proven at scale

---

## 4. Decision

> **Adopt a 3-Layer FFmpeg-Based Reel Engine with Template System**

### 4.1 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SABRIKA REEL ENGINE                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  LAYER 1: ANALYSIS (Understand the clips)                           │
│  ├── PySceneDetect → Scene boundaries & shot types                  │
│  ├── OpenCV → Blur/brightness scoring, motion analysis              │
│  └── Audio Analysis → Beat detection, silence removal               │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  LAYER 2: TEMPLATE (Apply cinematic structure)                      │
│  ├── Template Selector → Heritage / Street / Chef's Table / Family  │
│  ├── Act Mapping → Hook→Promise→Process→Payoff→Social→CTA          │
│  ├── Clip Assignment → Best clips matched to each act               │
│  ├── Transition Rules → Cross-fade, whip pan, match cut             │
│  ├── Color Grade LUT → Spice Warm / Steam Cool / Heritage           │
│  └── Text Overlay → Branded titles, dish names, contact info        │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  LAYER 3: RENDER (FFmpeg assembly)                                  │
│  ├── Filter Complex → Concatenate, transitions, color grade         │
│  ├── Audio Mix → Music bed + ambient + SFX                          │
│  ├── Logo Watermark → Restaurant logo overlay                       │
│  └── Output → 1080×1920 MP4 (H.264, AAC)                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Template Library (Phase 1)

| Template | Duration | Color LUT | Music Style | Best For |
|----------|----------|-----------|-------------|----------|
| **Heritage Dum** | 30s | Spice Warm (deep reds, golds, saffron) | Indian classical (sitar, tabla) | Dum biryani, traditional dishes |
| **Street Heat** | 20s | Vibrant (high saturation, punchy) | Electronic/Trap with desi samples | Chaat, street food, energetic |
| **Chef's Table** | 45s | Filmic (slight desat, warm shadows) | Ambient, minimal | Fine dining, chef stories |
| **Family Feast** | 25s | Natural (warm, inviting) | Upbeat folk/pop | Group dining, celebrations |
| **Midnight Biryani** | 20s | Moody (low-key, warm highlights) | Bass-heavy, atmospheric | Late night, cravings |

### 4.3 The 6-Act Structure (Per Template)

Each template implements the cinematic formula derived from cross-domain research:

```
Act 1 (0-3s):   HOOK       → Best frame / motion hook / audio sting
Act 2 (3-8s):   PROMISE    → Ingredient reveal / setting scene
Act 3 (8-20s):  PROCESS    → Cooking craft (the heart of the reel)
Act 4 (20-25s): PAYOFF     → The reveal, plating, first bite
Act 5 (25-28s): SOCIAL     → Happy diners, reactions, atmosphere
Act 6 (28-30s): CTA        → Logo, name, location, phone
```

### 4.4 Technology Stack

| Component | Technology | Version | License |
|-----------|-----------|---------|---------|
| **Video Assembly** | FFmpeg | 7.0+ | LGPL/GPL |
| **Scene Detection** | PySceneDetect | 0.6.4+ | BSD-3 |
| **Frame Analysis** | OpenCV (Python) | 4.9+ | Apache 2.0 |
| **Audio Analysis** | librosa | 0.10+ | ISC |
| **Text Overlays** | Pillow | 10.0+ | HPND |
| **Beat Detection** | librosa.beat | built-in | ISC |
| **Backend** | Python Flask | 3.0+ | BSD-3 |
| **Frontend** | HTML/CSS/JS | — | — |

---

## 5. Consequences

### 5.1 Positive

- **Professional output:** Cinematic 6-act structure with intentional pacing
- **Cultural authenticity:** Templates designed for Hyderabadi/Andhra visual language
- **Full automation:** Drop clips → select template → get reel
- **Zero recurring cost:** All open-source components
- **Extensible:** New templates can be added as JSON/Python configs
- **Fast:** FFmpeg assembly in 10-60 seconds depending on clip count

### 5.2 Negative

- **Requires FFmpeg expertise:** Complex filter graphs need careful debugging
- **No GUI timeline:** Templates are code-defined, not visual
- **Clip quality dependent:** Garbage in, garbage out — bad clips = bad reels
- **Audio licensing:** Background music must be royalty-free or licensed

### 5.3 Mitigations

| Negative | Mitigation |
|----------|-----------|
| FFmpeg complexity | Build reusable filter graph templates; extensive logging |
| No GUI timeline | Template preview via frame extraction before full render |
| Clip quality | Add clip validation (min resolution, max blur score) |
| Audio licensing | Curate 20+ royalty-free Indian music tracks; generate AI music fallback |

---

## 6. Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] FFmpeg pipeline for basic clip concatenation
- [ ] PySceneDetect integration for scene boundaries
- [ ] Blur/brightness scoring for best frame extraction
- [ ] Single template: "Heritage Dum" (hard-coded)

### Phase 2: Templates (Week 2)
- [ ] Template JSON schema definition
- [ ] 5 initial templates implemented
- [ ] Cross-fade and whip-pan transitions
- [ ] Color grade LUT application

### Phase 3: Audio (Week 3)
- [ ] Background music mixing
- [ ] Beat detection for sync cuts
- [ ] Ambient audio layer (kitchen sounds)
- [ ] Text-to-speech for optional voiceover

### Phase 4: Polish (Week 4)
- [ ] Logo watermark overlay
- [ ] Branded text animations
- [ ] Thumbnail auto-generation
- [ ] Web UI for template selection and clip upload

### Phase 5: AI Enhancement (Month 2)
- [ ] Smart clip reordering based on content
- [ ] Auto-music selection based on template mood
- [ ] AI-generated B-roll from still photos
- [ ] Dynamic duration based on clip quality

---

## 7. References

[^1]: Reelbase. "7 Best AI Video Generators for TikTok & Reels (2026)." March 2026. https://reelbase.io/blog/best-ai-video-generators-for-tiktok-reels

[^2]: Koro. "AI Reel Generators for E-commerce: 2026 Guide." February 2026. https://getkoro.app/blog/koro-ai-reel-generator-stunning-reels

[^3]: img.ly. "Best Open Source Video Editor SDKs: 2026 Roundup." November 2025. https://img.ly/blog/best-open-source-video-editor-sdks-2025-roundup/

[^4]: PySceneDetect Documentation. https://pyscenedetect.readthedocs.io/

[^5]: PremiumBeat. "A Guide to Using B-Roll Effectively in Your Video Edit." 2021. https://www.premiumbeat.com/blog/b-roll-video-edit-guide/
