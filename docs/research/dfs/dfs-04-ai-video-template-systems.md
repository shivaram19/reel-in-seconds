# DFS-04: AI Video Generation & Template Systems — Deep-Dive

**Date:** 2026-05-02
**Scope:** Open-source and commercial AI tools for automated reel generation from clips
**Research Phase:** Depth-First Technology Evaluation
**Author:** Research Assembly for Sabrika Brand Manager

---

## 1. Evaluation Framework

We evaluate video automation tools across six dimensions:

| Dimension | Weight | Rationale |
|-----------|--------|-----------|
| **Output Quality** | 25% | Must look professional, not AI-generated-generic |
| **Template Flexibility** | 20% | Must adapt to restaurant domain |
| **Automation Level** | 20% | Raw clips → finished reel with minimal input |
| **Cost** | 15% | Student budget — minimal recurring costs |
| **Open Source** | 10% | Prefer open-source for customization |
| **Speed** | 10% | Generate reels in under 2 minutes |

---

## 2. Route A: FFmpeg + Python Scripting (Open Source)

### 2.1 Technical Architecture

```
[Raw Clips] → [Scene Detection (PySceneDetect)] → [Best Frame Extraction]
    ↓
[Template Selection] → [FFmpeg Assembly Pipeline]
    ↓
[Color Grading] → [Audio Mix] → [Text Overlays] → [Output Reel]
```

### 2.2 Core Tools

| Tool | Version | License | Role |
|------|---------|---------|------|
| **FFmpeg** | 7.0+ | LGPL/GPL | Video assembly, filters, transcoding |
| **PySceneDetect** | 0.6.4+ | BSD-3 | Automatic scene boundary detection |
| **OpenCV** | 4.9+ | Apache 2.0 | Frame analysis, blur/brightness scoring |
| **MoviePy** | 1.0+ | MIT | Pythonic video composition (optional wrapper) |
| **Pillow** | 10.0+ | HPND | Text overlay generation |

### 2.3 Scene Detection with PySceneDetect

PySceneDetect uses content-aware algorithms to find shot boundaries [^1]:

```python
from scenedetect import detect, ContentDetector, split_video_ffmpeg

# Detect scenes using content-aware algorithm
scenes = detect('raw_clip.mp4', ContentDetector(threshold=27.0))

# Split video into individual scenes
split_video_ffmpeg('raw_clip.mp4', scenes, 
    output_file_template='scene-${scene_number:03d}.mp4')
```

**Performance:** ~1-2 minutes for a 5-minute clip on CPU.

### 2.4 FFmpeg Filter Complex for Reel Assembly

```bash
# Concatenate clips with cross-fade transitions
ffmpeg -i clip1.mp4 -i clip2.mp4 -i clip3.mp4 -filter_complex "
  [0:v][1:v]xfade=transition=fade:duration=0.5:offset=2[v1];
  [v1][2:v]xfade=transition=fade:duration=0.5:offset=4[outv];
  [0:a][1:a]acrossfade=d=0.5[a1];
  [a1][2:a]acrossfade=d=0.5[outa]
" -map "[outv]" -map "[outa]" output.mp4
```

### 2.5 Available Transitions in FFmpeg

| Transition | Description | Best For |
|------------|-------------|----------|
| `fade` | Cross dissolve | Standard cuts |
| `slideleft`/`slideright` | Whip pan | Energy, movement |
| `smoothleft`/`smoothright` | Smooth directional | Cinematic feel |
| `wipeleft`/`wiperight` | Wipe reveal | Dramatic reveals |
| `circleopen`/`circleclose` | Iris effect | Focus points |
| `rectcrop` | Zoom through rectangle | Intensity build |
| `fadegrays` | Fade to gray | Emotional shift |
| `hlwind`/`hrwind` | Horizontal wind | Dynamic action |

### 2.6 Evaluation

**Score: 7.5/10**

| Dimension | Score | Notes |
|-----------|-------|-------|
| Output Quality | 7/10 | Depends heavily on input clip quality |
| Template Flexibility | 8/10 | Fully customizable via code |
| Automation Level | 6/10 | Requires significant scripting |
| Cost | 10/10 | Completely free |
| Open Source | 10/10 | Full source control |
| Speed | 6/10 | 2-5 minutes per reel |

---

## 3. Route B: MoviePy + Templates (Pythonic)

### 3.1 Technical Architecture

MoviePy provides a Pythonic interface over FFmpeg [^2]:

```python
from moviepy.editor import *

# Load clips
clips = [VideoFileClip(f"clip{i}.mp4") for i in range(3)]

# Apply effects
processed = []
for clip in clips:
    # Slow motion for action shots
    if is_action_shot(clip):
        clip = clip.fx(vfx.speedx, 0.5)
    # Color grade
    clip = clip.fx(vfx.colorx, 1.1)
    processed.append(clip)

# Concatenate with transitions
final = concatenate_videoclips(processed, method="compose")

# Add text overlay
txt = TextClip("Biryani House", fontsize=70, color='white',
               font='DejaVu-Sans-Bold')
txt = txt.set_position('center').set_duration(3)

# Composite
video = CompositeVideoClip([final, txt])
video.write_videofile("output.mp4", fps=30)
```

### 3.2 Critical Limitation

> "MoviePy is designed for scripting and backend automation. It works best for creating short automated clips or experimental workflows." [^2]

**Performance Issue:** MoviePy re-encodes everything, making it **10-50x slower** than direct FFmpeg [^3]. For a 30-second reel: MoviePy = 3-5 minutes, FFmpeg = 10-30 seconds.

### 3.3 Evaluation

**Score: 5.5/10**

| Dimension | Score | Notes |
|-----------|-------|-------|
| Output Quality | 7/10 | Good with proper filters |
| Template Flexibility | 8/10 | Python flexibility |
| Automation Level | 6/10 | Scripting required |
| Cost | 10/10 | Free |
| Open Source | 10/10 | MIT license |
| Speed | 2/10 | Very slow for production |

---

## 4. Route C: Remotion (React-Based Programmatic Video)

### 4.1 Technical Architecture

Remotion is a unique open-source framework that uses **React components to generate video** [^2]:

```tsx
// ReelTemplate.tsx
export const ReelTemplate: React.FC = () => {
  return (
    <AbsoluteFill>
      <Sequence from={0} durationInFrames={90}>
        <Video src={staticFile("hook_clip.mp4")} />
      </Sequence>
      <Sequence from={90} durationInFrames={180}>
        <Video src={staticFile("process_clip.mp4")} />
        <TextOverlay text="6 Hours of Slow Cooking" />
      </Sequence>
      <Sequence from={270} durationInFrames={120}>
        <Video src={staticFile("payoff_clip.mp4")} />
        <ColorGrade lut="spice_warm.cube" />
      </Sequence>
    </AbsoluteFill>
  );
};
```

### 4.2 Strengths

- **Type-safe templates** — React components enforce structure
- **Preview capability** — Browser-based preview before render
- **Parameterization** — Pass props to customize templates
- **Open source** — MIT license

### 4.3 Weaknesses

- **Requires Node.js** — Not Python-native
- **Learning curve** — Need React knowledge
- **Rendering overhead** — Headless Chrome for video generation

### 4.4 Evaluation

**Score: 6.5/10**

| Dimension | Score | Notes |
|-----------|-------|-------|
| Output Quality | 8/10 | Professional with good components |
| Template Flexibility | 9/10 | React is extremely flexible |
| Automation Level | 5/10 | Requires React/TypeScript skills |
| Cost | 10/10 | Free, open-source |
| Open Source | 10/10 | MIT license |
| Speed | 4/10 | Headless Chrome rendering is slow |

---

## 5. Route D: Commercial AI Tools (Reference Architecture)

### 5.1 Opus Clip

- **Input:** Long-form video
- **Output:** Viral short clips with AI-selected hooks
- **Features:** Virality score, animated captions, AI B-roll
- **Cost:** $15-29/month
- **Verdict:** Best for repurposing existing long content, not for raw clip assembly [^4]

### 5.2 Koro AI

- **Input:** Product URL or images
- **Output:** UGC-style video ads with AI avatars
- **Features:** "Auto-Pilot" framework, trending audio scan
- **Cost:** ~$5-10 per video
- **Verdict:** Designed for e-commerce product ads, not restaurant storytelling [^5]

### 5.3 InVideo AI (2026)

- **Input:** Text prompt or script
- **Output:** Fully produced video with AI avatars, continuity engine
- **Features:** AI color grading, relighting, iStock integration
- **Cost:** ~$9/month
- **Verdict:** General-purpose, not restaurant-specific [^6]

---

## 6. Recommended Hybrid Architecture

### 6.1 The "Sabrika Reel Engine" Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                    SABRIKA REEL ENGINE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  INPUT LAYER                                                     │
│  ├── Raw video clips (phone/camera footage)                     │
│  ├── Restaurant profile (colors, logo, tagline)                 │
│  ├── Template selection (Heritage / Street / Cinematic)         │
│  └── Music preference (Traditional / Electronic / Ambient)      │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  PROCESSING LAYER                                                │
│  ├── PySceneDetect → Scene boundaries & best frames             │
│  ├── OpenCV → Blur/brightness scoring, face detection           │
│  ├── Template Engine → Act mapping (Hook→Promise→Process→Payoff)│
│  ├── FFmpeg Filter Complex → Assembly, transitions, color grade │
│  ├── Pillow → Branded text overlays, logo watermark             │
│  └── Audio Mix → Music bed + ambient + SFX mixing               │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  OUTPUT LAYER                                                    │
│  ├── 1080×1920 MP4 (Instagram Reel)                             │
│  ├── 1080×1080 MP4 (Instagram Post)                             │
│  └── Thumbnail PNG (auto-generated from best frame)             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Template Library (Initial)

| Template Name | Cuisine Style | Mood | Duration | Key Features |
|--------------|---------------|------|----------|-------------|
| **Heritage Dum** | Hyderabadi/Andhra | Warm, traditional, respectful | 30s | Slow pans, steam emphasis, saffron tones, classical music |
| **Street Heat** | Indian Street Food | Fast, energetic, vibrant | 20s | Quick cuts, saturated colors, electronic/trap music |
| **Chef's Table** | Fine Dining | Intimate, crafted, premium | 45s | Close-ups, shallow depth, ambient kitchen sounds |
| **Family Feast** | Casual Dining | Welcoming, communal, joyful | 25s | Group shots, warm lighting, upbeat folk music |
| **Midnight Biryani** | Late Night | Moody, atmospheric, craving | 20s | Low light, steam, slow-motion, bass-heavy music |

### 6.3 Technical Implementation Priority

| Phase | Feature | Effort | Impact |
|-------|---------|--------|--------|
| **1** | Basic FFmpeg assembly with hard cuts | Low | Medium |
| **2** | PySceneDetect integration + best frame extraction | Medium | High |
| **3** | Cross-fade transitions + color grading | Medium | High |
| **4** | Template system (5 templates) | High | Very High |
| **5** | Audio mixing (music + ambient + SFX) | Medium | High |
| **6** | Beat-matched cutting | High | Medium |
| **7** | AI-generated B-roll from stills | High | Medium |

---

## 7. References

[^1]: PySceneDetect Documentation. "Automating Scene-Based Video Splitting." https://pyscenedetect.readthedocs.io/

[^2]: img.ly. "Best Open Source Video Editor SDKs: 2026 Roundup." November 2025. https://img.ly/blog/best-open-source-video-editor-sdks-2025-roundup/

[^3]: CSDN Blog. "FFmpeg+MoviePy Short Video Automation Pipeline." February 2026. https://blog.csdn.net/zero1/article/details/155044681

[^4]: Reelbase. "7 Best AI Video Generators for TikTok & Reels (2026)." March 2026. https://reelbase.io/blog/best-ai-video-generators-for-tiktok-reels

[^5]: Koro. "AI Reel Generators for E-commerce: 2026 Guide." February 2026. https://getkoro.app/blog/koro-ai-reel-generator-stunning-reels

[^6]: PixTeller. "AI Video Generators Ranked: 7 Best Platforms for 2026." February 2026. https://pixteller.com/blog/ai-video-generators-ranked-7-best-platforms-for-2026-555
