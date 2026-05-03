# BFS-04: Frame-by-Frame Analysis & Domain Mapping for Restaurant Reels

## Research Date: 2026-05-02
## Focus: OpenCV + YOLOv8 + Temporal Analysis for Restaurant Content Understanding

---

## 1. Scene Detection Landscape (2024-2026)

### PySceneDetect (Castellano, 2024)
- **Standard tool** used by: SoulX-FlashHead, DataCube, CineTrans, X-Streamer
- ContentDetector algorithm detects shot boundaries based on frame differences
- Threshold=26 is common default (DataCube)
- Splits videos into 5-50 second coherent clips
- Exclusively CPU-based — efficient for preprocessing
- Exports: CSV, EDL, XML/OTIO, HTML visualization

### TransNetV2 (Soucek & Lokoc, 2024)
- Shot segmentation accuracy: **87%** vs PySceneDetect's **65.5%**
- Better at gradual transitions (dissolves, wipes)
- Single-frame-prediction for hard cuts
- All-frame-prediction for gradual changes
- Best practice: PySceneDetect first → TransNetV2 refinement

### Key Insight for Restaurant Reels
- Hard cuts dominate phone-shot restaurant footage
- PySceneDetect is sufficient for our use case
- Gradual transitions are rare in raw phone clips

---

## 2. Frame-by-Frame Object Detection

### YOLOv8 (Ultralytics, 2024)
- Anchor-free design, superior feature representation
- Real-time: >25 FPS on NVIDIA T4, fast on CPU too
- mAP@0.5 >92% on food datasets
- COCO pretrained: 80 classes including person, bowl, cup, bottle, spoon, fork, knife, dining table, chair, oven, microwave, refrigerator, sink, sandwich, cake, donut, pizza, hot dog

### Food-Specific Detection (2025)
- Custom YOLOv8 training on food datasets (Rajesh Kumar et al.)
- 6 categories: egg, chicken, carrot, apple, bread, burger
- Roboflow for annotation/augmentation
- 5% precision improvement over SSD, 7% recall improvement over YOLOv3

### Temporal Consistency (OSCAR, ACM SIGACCESS 2025)
- **Problem**: Per-frame detection is noisy — objects flicker in/out
- **Solution**: Time-causal modeling + object status tracking
- Averaging similarity scores across 5 frames per segment
- 20% accuracy improvement with temporal modeling
- Short-term memory buffers maintain scene continuity

### Key Insight for Restaurant Reels
- Don't trust single-frame detections
- Smooth object presence across 0.5-1 second windows
- Track object persistence to determine scene type

---

## 3. Quality & Aesthetic Metrics

### Motion Analysis (DataCube approach)
- **Optical flow** (RAFT) every 0.5 seconds
- Motion strength score — filter out static clips (score < 10)
- High motion = energy, action, cooking dynamism
- Low motion = atmosphere, ambiance, still life

### Blur Detection (OSCAR approach)
- Laplacian variance filter per frame
- Select clearest frame per segment
- Critical for "best frame" extraction for thumbnails/covers

### Aesthetic Quality
- **NIQE** (Natural Image Quality Evaluator) — no-reference quality
- **MUSIQ** — learned aesthetic quality estimator
- Filter out poorly lit, grainy, unstable footage

### Key Insight for Restaurant Reels
- Not all frames are equal — extract the "hero frame" per scene
- Blur detection = sharpness of steam, texture detail, glistening oil
- Motion score = pace indicator (high for action, low for mood)

---

## 4. Domain Relevance Mapping

### Restaurant Object Taxonomy

**Tier 1: Core Food Objects (Highest Relevance)**
- bowl, cup, spoon, fork, knife, bottle, wine glass
- pizza, sandwich, cake, donut, hot dog
- Person + hand action (cooking, serving, eating)

**Tier 2: Restaurant Environment (High Relevance)**
- dining table, chair, couch, potted plant
- oven, microwave, refrigerator, sink
- book (menu), clock, vase

**Tier 3: Ambiance Elements (Medium Relevance)**
- tv, laptop, cell phone, remote
- umbrella (outdoor seating)
- dog, cat (pet-friendly)

**Tier 4: Distractors (Low/Negative Relevance)**
- car, truck, bus, bicycle, motorcycle
- traffic light, stop sign, parking meter
- backpack, umbrella (if not relevant)

### Scene Type Classification

| Scene Type | Key Objects | Motion Pattern | Restaurant Relevance |
|------------|-------------|----------------|---------------------|
| Cooking | oven, bowl, spoon, person hands | High, rhythmic | Very High |
| Plating | bowl, spoon, person hands | Medium, precise | Very High |
| Food Close-up | bowl, cup, pizza, cake | Low, static | Very High |
| Dining | dining table, chair, person | Medium, social | High |
| Atmosphere | chair, potted plant, tv | Low, ambient | Medium |
| Kitchen Prep | refrigerator, sink, oven | Medium, busy | High |
| Exterior | car, traffic light | Variable | Low |

### Key Insight for Restaurant Reels
- Domain mapping is the **brain** — without it, it's just generic video editing
- Weight objects by restaurant type (biryani pot matters more for Indian restaurant than pizza)
- Scene type determines narrative placement (cooking → process, plating → payoff)

---

## 5. FFmpeg Filter Complex for Restaurant Reels

### Color Grading
- `curves` — Adobe Photoshop-style curves (shadows, midtones, highlights)
- `colorbalance` — red-cyan, green-magenta, blue-yellow shifts
- `colorcontrast` — RGB component contrast
- `haldclut` — apply cinematic LUTs
- `eq` — brightness, contrast, saturation, gamma

### Transitions
- `fade` — fade in/out (t=in|out, st=start_time, d=duration)
- `blend` — cross-dissolve, wipes, checkerboard
- `xfade` — extended fade with more transition types (2024+)

### Vertical Format (9:16 for Instagram Reels)
- `crop` or `scale` + `pad` to 1080x1920
- Center crop or smart crop based on object location

### Text Overlays (for CTA, not subtitles)
- `drawtext` — dynamic text with box background
- Position: center, bottom-third, top
- Font: bold, readable at small sizes

### Key Insight for Restaurant Reels
- FFmpeg filter_complex is 10-50x faster than MoviePy
- No re-encoding penalty when using stream copy where possible
- Pre-compute all filter strings, then execute in one pass

---

## 6. Beat-Sync Cut Detection (Research Gap)

### Audio Analysis
- **librosa** for tempo detection and beat tracking
- Onset strength for percussive events
- Tempo mapping: slow (60-80 BPM) for heritage, fast (120-140 BPM) for street

### Visual-Audio Alignment
- Cut on beat for high-energy templates
- Cut on phrase boundaries for emotional templates
- Avoid cutting during sustained notes

### Key Insight
- Beat-sync is the difference between "amateur" and "professional"
- But: only cut on beat if the visual action supports it
- Never sacrifice narrative for rhythm

---

## 7. Architecture Decision

### Chosen Stack
1. **PySceneDetect** — Scene boundary detection (fast, proven)
2. **YOLOv8 (COCO)** — Frame-by-frame object detection (no custom training needed)
3. **OpenCV** — Frame extraction, blur detection, optical flow
4. **FFmpeg** — Final assembly with filter_complex
5. **Custom Domain Mapper** — Restaurant-specific object relevance scoring
6. **Custom Narrative Engine** — 6-act structure with restaurant soul awareness

### Not Using (Yet)
- TransNetV2 — Overkill for phone-shot footage with hard cuts
- Custom YOLOv8 food model — COCO covers enough restaurant objects
- VLM semantic profiling (Qwen2.5-VL) — Powerful but slow; can add later
- CLIP/SigLIP alignment — Interesting but not needed without subtitles

---

## 8. The Pakwaan Restaurant Soul Profile

### Identity
- **Name**: The Pakwaan
- **Location**: Almaty, Kazakhstan
- **Cuisine**: Indian (Rajasthani, South Indian, Gujarati, Jain, Pure Vegetarian)
- **Vibe**: "Authentic Indian vegetarian food... atmosphere feels like India"

### Signature Dishes
- Veg Biryani, Rajasthani Gatta Biryani, Paneer Biryani
- Rajasthani Thali, Daal Baati Churma
- Idli Sambhar, Medu Vada, Dosa varieties
- Palak Paneer, Kadhai Paneer, Shahi Paneer
- Gulab Jamun, Jalebi, Ghevar, Mohan Thal

### Audience
- **Primary**: Indian students at GVK Medical College, Almaty (homesick, craving authentic food)
- **Secondary**: Local Kazakh residents curious about Indian cuisine
- **Tertiary**: Vegetarian/Jain community in Almaty

### Owner's Intention
- Bring a piece of India to Almaty
- Make students feel at home
- Serve authentic, pure vegetarian Indian food
- Preserve Rajasthani and South Indian culinary traditions

### Domain-Specific Object Relevance
- **Highest**: biryani pot, handi, tawa, dosa griddle, paneer cubes, steam rising
- **High**: thali plates, copper vessels, clay bowls, chapati/naan being flipped
- **Medium**: dining area, Indian decor, warm lighting, students eating
- **Low**: cars, streets, non-Indian elements

---

## References

1. Castellano, B. (2024). PySceneDetect. https://github.com/Breakthrough/PySceneDetect
2. Soucek & Lokoc (2024). TransNetV2. https://github.com/soCzech/TransNetV2
3. Rajesh Kumar S. et al. (2025). Food Object Detection Using Custom-Trained YOLOv8. ETASR.
4. OSCAR (2025). Object Status Recognition for Recipe Progress Tracking. ACM SIGACCESS.
5. DataCube (2025). Video Retrieval via Natural Language Semantic Profiling. arXiv.
6. CineTrans (2025). Learning Cinematic Transitions via Masked Diffusion. arXiv.
7. X-Streamer (2025). Unified Human World Modeling. arXiv.
8. FFmpeg Filters Documentation (2026). https://ffmpeg.org/ffmpeg-filters.html
