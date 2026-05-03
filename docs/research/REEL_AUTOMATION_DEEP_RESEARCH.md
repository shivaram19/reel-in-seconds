# Deep Research: Sabrika Reel Automation Platform
## Raw Clips → Strategic Restaurant Reels (Almaty-Focused)

**Research Date:** 2026-05-02  
**Scope:** Open-source pipeline for converting raw restaurant video clips into branded Instagram Reels  
**Domain:** Restaurants in Almaty, Kazakhstan  
**Methodology:** Breadth-First Search across tool categories + Bi-Directional Cross-Pollination Mapping

---

## 1. EXECUTIVE SUMMARY

The goal is a **fully automated pipeline** where a human uploads raw video clips from a restaurant visit, adds context (restaurant profile, event description), selects or discovers a trending song, and the system outputs:

1. A **strategic Instagram Reel** (9:16 vertical, 15-90 seconds)
2. A **click-worthy thumbnail** for the reel
3. Branded **text overlays** (restaurant name, offer, hook)
4. Optional **subtitles** for accessibility

All using **100% open-source tools** — no Adobe, no Canva Pro, no paid video editors.

---

## 2. THE COMPLETE PIPELINE (BFS — Breadth-First)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SABRIKA REEL AUTOMATION PIPELINE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STAGE 1          STAGE 2          STAGE 3          STAGE 4                │
│  INGESTION   →   ANALYSIS    →   ASSEMBLY   →   ENRICHMENT                 │
│                                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐                 │
│  │ Raw     │    │ Scene   │    │ Clip    │    │ Text    │                 │
│  │ Clips   │───▶│ Detect  │───▶│ Select  │───▶│ Overlay │                 │
│  │ Upload  │    │ Whisper │    │ Reorder │    │ Titles  │                 │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘                 │
│       │              │              │              │                        │
│       ▼              ▼              ▼              ▼                        │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐                 │
│  │ Trending│    │ Audio   │    │ Vertical│    │ Subtitle│                 │
│  │ Songs   │    │ Transc  │    │ Crop    │    │ Gen     │                 │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘                 │
│                                                                             │
│  STAGE 5          STAGE 6          STAGE 7          STAGE 8                │
│  BRANDING    →   RENDER    →   THUMBNAIL  →   PUBLISH                     │
│                                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐                 │
│  │ Color   │    │ FFmpeg  │    │ AI/     │    │ Download│                 │
│  │ Grade   │    │ Render  │    │ PIL Gen │    │ Reel    │                 │
│  │ Logo    │    │ 9:16 MP4│    │ Thumb   │    │ + Thumb │                 │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. STAGE-BY-STAGE: TOOLS, MAPPINGS & CROSS-POLLINATION

---

### STAGE 1: INGESTION — Raw Clip Upload & Trending Song Discovery

#### 1A. Clip Upload
| Tool | Type | Role | Status |
|------|------|------|--------|
| **Flask Upload Endpoint** | Python/Web | Receive MP4/MOV from phone/camera | ✅ Already in app |
| **python-multipart** | Python lib | Handle multipart file uploads | Install if needed |
| **Werkzeug FileStorage** | Python lib | Secure file handling | ✅ Already in Flask |

#### 1B. Trending Song Discovery (CRITICAL OPEN QUESTION)
**Problem:** Instagram/TikTok trending songs are proprietary and region-locked. No open API gives real-time trending audio.

| Approach | Tool/Source | Open? | Reliability | Notes |
|----------|-------------|-------|-------------|-------|
| **TikTok Creative Center** | `https://ads.tiktok.com/business/en-US/solutions/tiktok-for-business/creative-center` | Free web UI | High | Manual browse, no API |
| **Spotify Charts** | `https://spotifycharts.com/regional` + Spotify Web API | API (rate-limited) | Medium | Shows popular, not necessarily "trending on Reels" |
| **YouTube Trending Music** | YouTube Data API v3 | API (quota-limited) | Medium | Global/regional trending |
| **Instagram Professional Dashboard** | Manual only | No API | High | Best source but manual |
| **SoundCloud Charts** | SoundCloud API | API | Low-Medium | Underground trends |
| **AudioFingerprint (DIY)** | Dejavu / Chromaprint | Fully OSS | Medium | Fingerprint audio from viral clips you scrape |
| **Manual Curation DB** | SQLite/JSON | Fully OSS | High | Build your own DB of songs that worked for Almaty restaurants |

**RECOMMENDATION FOR ALMATY:**
- **Short-term:** Build a curated SQLite DB of trending songs. Your sister (or a human) adds 5-10 songs/week manually from TikTok Creative Center + Instagram Reels tab.
- **Medium-term:** Scrape TikTok Creative Center trending sounds page using Playwright/Selenium (respect robots.txt, cache aggressively).
- **Long-term:** Use Shazam Kit API (free tier: 50 requests/day) to fingerprint audio from top-performing restaurant reels in Almaty.

**Cross-Pollination:** Trending song DB → feeds into Stage 4 (audio track selection) and Stage 7 (thumbnail mood matching).

---

### STAGE 2: ANALYSIS — Dissecting Raw Clips

#### 2A. Scene Detection (Finding Best Moments)
| Tool | Language | Method | Speed | Open Source? |
|------|----------|--------|-------|--------------|
| **PySceneDetect** | Python | Content-aware threshold + histogram diff | Fast | ✅ MIT |
| **OpenCV Scene Detection** | Python | Frame differencing manually | Medium | ✅ Apache 2.0 |
| **TransNetV2** | Python (PyTorch) | Deep learning scene detection | Slow (GPU) | ✅ Apache 2.0 |
| **Whisper Timestamps** | Python | Speech segments as scene boundaries | Medium | ✅ MIT |

**Best for Restaurants:** **PySceneDetect** is the sweet spot. It detects when the camera cuts (chef plating, food close-up, dining room pan) without needing a GPU. TransNetV2 is overkill for this use case.

```bash
pip install scenedetect[opencv]
scenedetect -i input.mp4 detect-content list-scenes
```

#### 2B. Audio Transcription (For Subtitles & Hook Detection)
| Tool | Model Size | Speed | Accuracy | Languages | Open Source? |
|------|-----------|-------|----------|-----------|--------------|
| **OpenAI Whisper** | tiny/base/small/medium/large | Medium | Excellent | 99 languages | ✅ MIT |
| **faster-whisper** (CTranslate2) | same models | 4x faster | Same | 99 languages | ✅ MIT |
| **whisper.cpp** | quantized models | Very fast (CPU) | Slightly lower | 99 languages | ✅ MIT |
| **Wav2Vec 2.0** | various | Fast | Good | Multilingual | ✅ Apache 2.0 |

**Best for Almaty Restaurants:** **faster-whisper** with `small` model. Handles Russian/Kazakh/English mix common in Almaty. `small` is the accuracy/speed sweet spot.

```bash
pip install faster-whisper
```

#### 2C. Visual Analysis (Optional — "Best Frame" Extraction)
| Tool | Purpose | Open Source? |
|------|---------|--------------|
| **OpenCV** | Blur detection, brightness, contrast analysis | ✅ |
| **CLIP (OpenAI)** | Text-to-image similarity ("find the frame that looks most like delicious biryani") | ✅ MIT |
| **YOLO / MobileNet** | Object detection (detect food, people, plates) | ✅ |

**Cross-Pollination:**
- Scene boundaries (PySceneDetect) → feed into Clip Selection (Stage 3)
- Whisper transcription → feed into Subtitle Generation (Stage 4) + Hook text extraction
- Visual quality scores (OpenCV) → feed into Best Frame for Thumbnail (Stage 7)

---

### STAGE 3: ASSEMBLY — Building the Reel Sequence

#### 3A. Video Editing / Assembly Engine
| Tool | Type | Learning Curve | Performance | Best For |
|------|------|---------------|-------------|----------|
| **FFmpeg** | CLI/C | High | Excellent | Everything. The universal video tool. |
| **MoviePy** | Python | Medium | Medium | Prototyping, Python-native pipelines |
| **ffmpeg-python** | Python wrapper | Low | Excellent | Calling FFmpeg from Python cleanly |
| **Remotion** | React/Node | Medium | Good | Programmatic templates, web-based |
| **Shotcut / MLT** | C++ library | High | Good | Desktop NLE, not great for automation |
| **GStreamer** | C/Pipeline | Very High | Excellent | Real-time streaming, overkill here |

**RECOMMENDATION:** **FFmpeg directly** for the render pipeline (fastest, most control) + **ffmpeg-python** for Python integration + **MoviePy** only for rapid prototyping.

Key FFmpeg commands for Reel assembly:
```bash
# Concatenate clips with crossfade
ffmpeg -i clip1.mp4 -i clip2.mp4 -i clip3.mp4 \
  -filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=5[va]; \
                   [va][2:v]xfade=transition=fade:duration=0.5:offset=10[vout]; \
                   [0:a][1:a]acrossfade=d=0.5[aa]; [aa][2:a]acrossfade=d=0.5[aout]" \
  -map "[vout]" -map "[aout]" -c:v libx264 -crf 23 -preset fast output.mp4

# Add audio track (trending song)
ffmpeg -i video.mp4 -i song.mp3 -c:v copy -map 0:v:0 -map 1:a:0 \
  -shortest -c:a aac -b:a 192k final.mp4

# Vertical crop to 9:16 (1080x1920)
ffmpeg -i input.mp4 -vf "crop=ih*9/16:ih,scale=1080:1920" -c:a copy output.mp4
```

#### 3B. Clip Selection Logic (The "Strategy")
This is where AI meets business logic:

| Input | Processing | Output |
|-------|-----------|--------|
| 10 raw clips (30-60s each) | PySceneDetect finds cut points | List of scenes with timestamps |
| Scene metadata (duration, visual quality) | Score each scene: duration × brightness × stability | Ranked scene list |
| Restaurant context (event type) | Rule engine: "Grand Opening" → more wide shots; "Food Review" → more close-ups | Selected clip segments |
| Target reel length (30s) | Greedy selection: pick highest-scoring scenes until ~30s | Final segment list |

**Cross-Pollination:** Scene scores + restaurant brand colors → feed into Thumbnail generation (Stage 7) to ensure visual consistency.

---

### STAGE 4: ENRICHMENT — Text Overlays, Subtitles & Branding

#### 4A. Text Overlay on Video
| Tool | Method | Quality | Dynamic? | Open Source? |
|------|--------|---------|----------|--------------|
| **FFmpeg drawtext** | Filter: `drawtext=text='BIRYANI HOUSE':fontsize=80` | Good | Yes (fontfile, colors) | ✅ |
| **PIL → Image → Overlay** | Render text as PNG, overlay with FFmpeg | Excellent | Full control | ✅ |
| **MoviePy TextClip** | Python API for text | Good | Yes | ✅ |
| **ImageMagick** | `convert` text to image | Excellent | Full control | ✅ |
| **Pango/Cairo** | Programmatic text rendering | Excellent | Full control | ✅ |

**RECOMMENDATION for Restaurant Branding:** Use **PIL** to render branded text as transparent PNGs, then overlay with FFmpeg. This gives full control over:
- Restaurant brand fonts
- Brand colors (from restaurants.json)
- Drop shadows, strokes, gradients
- Multi-line wrapping

```python
# PIL text → transparent PNG → FFmpeg overlay
from PIL import Image, ImageDraw, ImageFont

def render_title(text, font_path, font_size, color, stroke_color, stroke_width, output_path):
    font = ImageFont.truetype(font_path, font_size)
    bbox = font.getbbox(text)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    img = Image.new('RGBA', (w + stroke_width*4, h + stroke_width*4), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    # Draw stroke
    for dx in range(-stroke_width, stroke_width+1):
        for dy in range(-stroke_width, stroke_width+1):
            draw.text((w//2+dx, h//2+dy), text, font=font, fill=stroke_color, anchor='mm')
    # Draw fill
    draw.text((w//2, h//2), text, font=font, fill=color, anchor='mm')
    img.save(output_path)
```

#### 4B. Subtitle Generation
| Tool | Integration | Speed | Accuracy | Open Source? |
|------|------------|-------|----------|--------------|
| **faster-whisper → SRT** | Direct | Fast | Excellent | ✅ |
| **ffmpeg burn subtitles** | `subtitles=subtitle.srt` filter | Fast | N/A (rendering) | ✅ |
| **pysrt** | Python SRT manipulation | N/A | N/A | ✅ |
| **webvtt-py** | Python VTT manipulation | N/A | N/A | ✅ |

**Cross-Pollination:** Subtitle text → can be analyzed for "hook words" ("delicious", "amazing", "must try") → feed into Thumbnail text (Stage 7).

---

### STAGE 5: BRANDING — Restaurant Colors, Logo, Vibe

This is where the existing **Sabrika Brand Manager** data feeds in:

| Data Source | Field | Usage in Reel |
|-------------|-------|---------------|
| `restaurants.json` | `color1`, `color2` | Text overlay gradient, border glow, transition color |
| `restaurants.json` | `name` | Title card, end screen |
| `restaurants.json` | `tagline` | Subtitle under title |
| `restaurants.json` | `location` | Geo-tag overlay ("📍 Almaty, Kazakhstan") |
| `restaurants.json` | `instagram` | "Follow @handle" end card |
| `restaurants.json` | `phone` | "Call to order" end card |

**Branding Elements to Auto-Generate:**
1. **Opening Title Card** (2s): Restaurant name in brand colors
2. **Hook Text** (3s): "This biryani changed my life 🔥" — extracted from context
3. **Offer Banner** (floating): "20% OFF Family Pack" — from input
4. **Location Stamp** (bottom): "📍 Almaty" — from restaurant data
5. **End Card** (3s): Logo + Instagram + Phone + "Follow for more"

---

### STAGE 6: RENDER — Final Video Output

**FFmpeg Render Profile for Instagram Reels:**
```bash
ffmpeg -i assembled.mp4 -i audio_track.mp3 \
  -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,format=yuv420p" \
  -c:v libx264 -profile:v high -level:v 4.0 -pix_fmt yuv420p \
  -crf 23 -preset fast -r 30 \
  -c:a aac -b:a 192k -ar 48000 \
  -movflags +faststart -t 90 \
  -shortest final_reel.mp4
```

**Specs:**
- Resolution: 1080×1920 (9:16)
- Frame rate: 30fps
- Codec: H.264 (libx264)
- Audio: AAC, 192kbps, 48kHz
- Max duration: 90 seconds
- Color space: yuv420p (Instagram compatible)

---

### STAGE 7: THUMBNAIL — The "Click" Factor

#### 7A. Thumbnail Generation Strategies
| Strategy | Tool | Quality | Open Source? |
|----------|------|---------|--------------|
| **Best Frame Extraction** | OpenCV + quality scoring | Medium | ✅ |
| **AI-Generated Thumbnail** | Stable Diffusion (AUTOMATIC1111/ComfyUI) | High | ✅ |
| **PIL Composite** | Restaurant brand + best frame + text | High | ✅ |
| **FFmpeg Thumbnail** | `select='eq(pict_type,I)'` + scale | Medium | ✅ |

**RECOMMENDATION:** **PIL Composite** approach for restaurants. It's fast, brand-consistent, and doesn't require a GPU:

1. Extract the highest-quality frame from the reel (OpenCV: sharpest, best-lit frame)
2. Apply a brand-color gradient overlay (semi-transparent)
3. Add large, bold text: "UNREAL BIRYANI 🔥" or hook text
4. Add restaurant name + location
5. Add a subtle border glow in brand color

```python
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def generate_thumbnail(frame_path, restaurant, hook_text, output_path):
    img = Image.open(frame_path).convert('RGB')
    img = img.resize((1080, 1920))
    
    # Darken for text readability
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 120))
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    
    draw = ImageDraw.Draw(img)
    
    # Hook text (large, bold)
    font_large = ImageFont.truetype("DejaVuSans-Bold.ttf", 120)
    draw.text((540, 800), hook_text, fill=(255,255,255), font=font_large, anchor='mm',
              stroke_width=4, stroke_fill=(0,0,0))
    
    # Restaurant name
    font_name = ImageFont.truetype("DejaVuSans-Bold.ttf", 70)
    draw.text((540, 1600), restaurant['name'], fill=_hex_to_rgb(restaurant['color1']),
              font=font_name, anchor='mm', stroke_width=3, stroke_fill=(0,0,0))
    
    img.save(output_path, quality=95)
```

**Cross-Pollination:** Thumbnail hook text ← comes from Whisper transcript "most exciting phrase" OR user-provided context. Thumbnail colors ← come from restaurants.json brand colors.

---

### STAGE 8: PUBLISH — Output & Download

Already handled by the existing Flask app pattern:
- Save to `static/generated/reels/`
- Serve via `/static/generated/reels/<filename>`
- Provide download endpoint

---

## 4. BI-DIRECTIONAL CROSS-POLLINATION MAPPING

This shows how data flows **both ways** between stages:

```
                    ┌─────────────────┐
                    │  restaurants.json│
                    │  (Brand DNA)     │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
    ┌─────────┐        ┌─────────┐        ┌─────────┐
    │ Text    │◄──────►│ Thumb-  │◄──────►│ Render  │
    │ Overlay │        │ nail    │        │ Color   │
    └─────────┘        └─────────┘        └─────────┘
         ▲                   ▲                   ▲
         │                   │                   │
    ┌────┴───────────────────┴───────────────────┴────┐
    │              RAW CLIP ANALYSIS                  │
    │  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
    │  │ Scene   │  │ Audio   │  │ Visual  │        │
    │  │ Detect  │  │ Whisper │  │ Quality │        │
    │  └────┬────┘  └────┬────┘  └────┬────┘        │
    │       │            │            │              │
    │       └────────────┼────────────┘              │
    │                    │                           │
    │              ┌─────┴─────┐                     │
    │              │  BEST     │                     │
    │              │  FRAME    │─────────────────────┘
    │              │  (Thumb)  │
    │              └───────────┘
    └─────────────────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Trending Song  │
                    │  DB (Manual +   │
                    │  Scraped)       │
                    └─────────────────┘
```

**Key Bidirectional Flows:**

1. **Restaurant Brand Colors ↔ EVERYTHING**
   - Text overlay colors ← `color1`, `color2`
   - Thumbnail gradient ← `color1` blended with frame
   - Transition flash color ← `color2`
   - End card background ← `color1`

2. **Whisper Transcription ↔ Text Overlay + Thumbnail**
   - Forward: Transcript → extract "hook phrase" → overlay text
   - Forward: Transcript → SRT subtitle file → burn into video
   - Backward: Most emotional/loud segment → determine WHERE to place hook text

3. **Scene Detection ↔ Clip Selection ↔ Thumbnail**
   - Forward: Scene boundaries → candidate segments
   - Forward: Best visual scene → thumbnail frame source
   - Backward: User-selected thumbnail frame → prioritize that scene in reel

4. **Trending Song ↔ Reel Length + Mood**
   - Forward: Song BPM → determine cut speed (fast cuts for high BPM)
   - Forward: Song duration → cap reel length
   - Backward: Reel mood (upscale dining vs street food) → filter song choices

---

## 5. ALMATY / KAZAKHSTAN SPECIFIC CONSIDERATIONS

### 5.1 Language Context
| Language | Usage | Tool Support |
|----------|-------|--------------|
| **Russian** | Primary business language | Whisper: excellent |
| **Kazakh** | National language, growing on social media | Whisper: good |
| **English** | Tourist-facing restaurants | Whisper: excellent |
| **Mixed** | Common in Almaty (code-switching) | Whisper: handles mixed audio |

**Implication:** Subtitle generation must support mixed Russian-Kazakh-English audio. Whisper `small` model handles this well.

### 5.2 Cultural Content Preferences
| Content Type | Expected Engagement | Raw Clip Strategy |
|--------------|--------------------|--------------------|
| **Food close-ups** (plating, steam, sizzle) | Very High | Always prioritize |
| **Chef/cook face** | High | Include if charismatic |
| **Dining atmosphere** (crowded, lively) | High | Shows popularity |
| **Customer reactions** | Very High | "First bite" moments |
| **Location/landmark shots** | Medium | Establish Almaty context |

### 5.3 Trending Audio for Kazakhstan
- **Russian pop** (Morgenshtern, Basta, Scriptonit) performs well
- **Kazakh folk remixes** are trending on TikTok
- **Global viral sounds** (English) work for tourist-facing restaurants
- **Recommendation:** Maintain separate trending song lists per restaurant type (local vs tourist)

### 5.4 Competition Analysis
Almaty restaurant Instagram is **underserved** compared to Western markets:
- Most restaurants post static photos, not reels
- Very few use professional video editing
- **Opportunity:** First-mover advantage for automated reels

---

## 6. REQUIRED TOOL INSTALLATION (Current Environment Status)

| Tool | Status | Install Command |
|------|--------|-----------------|
| **FFmpeg** | ❌ Missing | `sudo apt-get update && sudo apt-get install -y ffmpeg` |
| **MoviePy** | ❌ Missing | `pip install moviepy` |
| **OpenCV (cv2)** | ❌ Missing | `pip install opencv-python-headless` |
| **faster-whisper** | ❌ Missing | `pip install faster-whisper` |
| **PySceneDetect** | ❌ Missing | `pip install scenedetect[opencv]` |
| **librosa** | ❌ Missing | `pip install librosa` |
| **pydub** | ❌ Missing | `pip install pydub` |
| **PIL/Pillow** | ✅ Installed | Already available |
| **numpy** | ✅ Installed | Already available |
| **Flask** | ✅ Installed | Already available |

### One-Line Install
```bash
sudo apt-get update && sudo apt-get install -y ffmpeg \
&& pip install moviepy opencv-python-headless faster-whisper \
scenedetect[opencv] librosa pydub
```

---

## 7. RECOMMENDED ARCHITECTURE FOR SABRIKA v2

```
sabrika-brand-manager/
├── app.py                          # Existing Flask app (extended)
├── data/
│   └── restaurants.json            # Existing
├── docs/
│   └── research/
│       └── REEL_AUTOMATION_DEEP_RESEARCH.md   # This file
├── static/
│   ├── generated/
│   │   ├── stories/                # Existing image stories
│   │   ├── posts/                  # Existing image posts
│   │   └── reels/                  # NEW: generated video reels
│   ├── thumbnails/                 # NEW: reel thumbnails
│   └── songs/                      # NEW: trending song library
├── templates/
│   ├── index.html                  # Existing (add Reel tab)
│   ├── gallery.html                # Existing (add Reel filter)
│   └── reel_editor.html            # NEW: reel creation UI
├── reel_engine/                    # NEW MODULE
│   ├── __init__.py
│   ├── clip_analyzer.py            # PySceneDetect + OpenCV analysis
│   ├── audio_processor.py          # Whisper + audio mixing
│   ├── video_assembler.py          # FFmpeg assembly pipeline
│   ├── text_overlay.py             # PIL branded text renderer
│   ├── thumbnail_generator.py      # PIL thumbnail composer
│   ├── trending_songs.py           # Song DB + discovery
│   └── render_pipeline.py          # Orchestrates the full flow
└── requirements.txt                # Updated with video deps
```

---

## 8. ALTERNATIVES & BACKUP TOOLS (Breadth-First Complete)

| Stage | Primary | Backup 1 | Backup 2 |
|-------|---------|----------|----------|
| Scene Detection | PySceneDetect | OpenCV diff | TransNetV2 |
| Transcription | faster-whisper | whisper.cpp | Wav2Vec 2.0 |
| Video Assembly | FFmpeg | MoviePy | Remotion |
| Text Overlay | PIL → FFmpeg | MoviePy TextClip | ImageMagick |
| Audio Mixing | FFmpeg | pydub | SoX |
| Subtitles | faster-whisper → SRT | whisper-timestamped | wav2vec2 + CTC |
| Thumbnail | PIL Composite | Stable Diffusion | FFmpeg thumbnail |
| Song Discovery | Manual DB | TikTok scraper | Spotify Charts API |

---

## 9. ESTIMATED PROCESSING TIMES (Per Reel)

| Step | Duration (1-min raw clips) | GPU Required? |
|------|---------------------------|---------------|
| Upload + Storage | <1s | No |
| Scene Detection | 5-10s | No |
| Whisper Transcription | 10-30s | Optional (CPU works) |
| Clip Selection | <1s | No |
| Video Assembly (FFmpeg) | 15-45s | No |
| Text Overlay Render | 5-10s | No |
| Audio Mix | 5-10s | No |
| Thumbnail Generation | 2-5s | No |
| **TOTAL** | **~45s - 2min** | **No GPU needed** |

---

## 10. NEXT STEPS

1. **Install dependencies** (Section 6 one-liner)
2. **Build trending song DB** (SQLite: `id, title, artist, source_url, bpm, mood, region`)
3. **Create `reel_engine/` module** with `clip_analyzer.py` first
4. **Prototype the FFmpeg pipeline** with 2-3 test clips
5. **Add "Reels" tab** to existing Flask UI
6. **Test with real Almaty restaurant footage**

---

*Research compiled by Sabrika Brand Manager AI Agent*  
*Sources: GitHub, SourceForge, DigitalOcean, Shotstack, IMG.LY, VideoTap, Mixpeek, community documentation*  
*All tools listed are open-source and free for commercial use*
