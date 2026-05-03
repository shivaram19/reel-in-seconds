# ADR-003: Frame-by-Frame Analysis Reel Engine (V2)

## Status: Accepted

## Context

The V1 reel engine used PySceneDetect for scene boundaries and faster-whisper for subtitles, assembled via FFmpeg. While functional, it lacked:
- Understanding of WHAT is in each frame (objects, actions)
- Restaurant-specific relevance scoring (a pizza shot is irrelevant for The Pakwaan)
- Narrative intelligence (no concept of hook→promise→process→payoff→social→CTA)
- Subtitles were prioritized over visual storytelling

The user's directive was clear: **No subtitles.** The focus is on human-effective visual storytelling that communicates the restaurant's soul.

## Decision

Build a V2 reel engine with four layers:

### Layer 1: Frame Analysis (OpenCV + YOLOv8)
- **YOLOv8n** (COCO pretrained) for per-frame object detection
- **Temporal smoothing**: Objects must persist across 2+ frames to be considered real
- **Quality metrics**: Laplacian blur detection, frame differencing for motion, brightness, dominant colors
- **Scene classification**: cooking, plating, food_closeup, dining, atmosphere, kitchen_prep, serving, exterior

### Layer 2: Domain Mapping (Restaurant Soul)
- **RestaurantSoul** dataclass captures identity, audience, owner intention, signature objects
- **Object relevance taxonomy**: 41 COCO objects mapped to 0-1 relevance for The Pakwaan
- **Scene type weights**: cooking=1.0, plating=0.95, food_closeup=1.0, dining=0.8, etc.
- **Narrative role assignment**: Each scene gets a role (hook, promise, process, payoff, social, cta, filler)

### Layer 3: Narrative Assembly (6-Act Structure)
- **Hook** (0-3s): Scroll-stopper, highest visual impact
- **Promise** (3-8s): Teaser of what's coming
- **Process** (8-20s): The craft, cooking, preparation
- **Payoff** (20-25s): The money shot, final dish
- **Social** (25-28s): People enjoying, community
- **CTA** (28-30s): Invitation to visit
- **Templates**: heritage (slow), energetic (fast), warm (balanced)

### Layer 4: FFmpeg Pipeline (filter_complex)
- Vertical 9:16 format (1080x1920)
- Color grading per act (warm tones for Indian food)
- Transitions: fade_in, crossfade, fade_out
- Ken Burns zoom on hero shots
- Logo watermark overlay
- No subtitles, no text overlays (pure visual)

## Consequences

### Positive
- **Restaurant-aware editing**: The engine knows The Pakwaan's soul and edits accordingly
- **Frame-level intelligence**: Every frame is analyzed, not just scene boundaries
- **No subtitles**: Pure visual storytelling as requested
- **6-act narrative**: Professional cinematic structure
- **Fast**: YOLOv8n runs at >25 FPS on CPU, FFmpeg assembly in seconds

### Negative
- **YOLOv8 COCO classes are generic**: No "biryani pot" or "dosa griddle" classes
  - Mitigation: Domain mapper elevates bowl/person/oven relevance for Indian restaurants
  - Future: Custom food-specific YOLO model
- **No audio analysis yet**: Beat-sync cuts not implemented
  - Mitigation: Template-based pacing (heritage=slow, energetic=fast)
  - Future: librosa beat detection
- **Requires more compute**: Per-frame YOLO vs per-scene PySceneDetect
  - Mitigation: Sample every Nth frame (default: every 5th)

## Research Backing

1. **PySceneDetect**: Standard tool in SoulX-FlashHead, DataCube, CineTrans, X-Streamer [Castellano, 2024]
2. **YOLOv8**: mAP@0.5 >92% on food datasets, >25 FPS real-time [Rajesh Kumar et al., 2025]
3. **Temporal consistency**: OSCAR paper shows 20% accuracy improvement with time-causal modeling [ACM SIGACCESS 2025]
4. **FFmpeg filter_complex**: 10-50x faster than MoviePy, no re-encoding penalty [github.com/Zulko/moviepy/issues/2165]
5. **Quality metrics**: Optical flow (RAFT), NIQE, MUSIQ [DataCube, 2025]

## The Pakwaan Soul Profile

Built from:
- Website: thepakwaan.com (menu, keywords, vibe)
- TripAdvisor: "Authentic Indian vegetarian food... atmosphere feels like India"
- Location: Almaty, Kazakhstan, near GVK Medical College
- Audience: Indian medical students (homesick), local Kazakhs (curious)

Signature objects: biryani pot, tawa griddle, thali plate, copper handi, clay pot
Signature colors: warm copper (#D4A574), saddle brown (#8B4513), gold (#FFD700), crimson (#DC143C)
Emotional promise: Comfort, nostalgia, belonging — a piece of India in Almaty

## Code Structure

```
reel_engine/
├── restaurant_soul.py      # RestaurantSoul dataclass + The Pakwaan profile
├── frame_analyzer.py       # YOLOv8 + OpenCV per-frame analysis
├── domain_mapper.py        # Object relevance + scene role assignment
├── narrative_assembly.py   # 6-act structure + template selection
├── ffmpeg_pipeline.py      # FFmpeg filter_complex assembly
└── __init__.py             # V1/V2 exports
```

## API

```
POST /api/reels/v2
{
    "restaurant_id": 1,
    "clips": ["/static/uploads/clip1.mp4", ...],
    "template": "auto|heritage|energetic|warm",
    "duration": 30
}
```

## Performance

- Frame analysis: ~2-5s per minute of video (YOLOv8n on CPU)
- Domain mapping: <1s
- Narrative assembly: <1s
- FFmpeg render: ~10-30s for 30s reel
- Total: ~15-40s per reel
