"""
Frame Analysis Engine
=====================

Frame-by-frame object detection using YOLOv8 + OpenCV.
Temporal smoothing for consistent object tracking.
Quality metrics: blur detection, motion analysis, composition scoring.

Pipeline:
    1. Extract frames from video clip
    2. Run YOLOv8 detection per frame
    3. Temporal smoothing (object persistence across frames)
    4. Scene classification based on dominant objects
    5. Quality scoring per frame
    6. Extract best frames per scene
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

# Lazy-load YOLO to avoid import overhead
_yolo_model = None

def get_yolo_model():
    """Lazy initialization of YOLOv8 model."""
    global _yolo_model
    if _yolo_model is None:
        try:
            from ultralytics import YOLO
            logger.info("[FrameAnalyzer] Loading YOLOv8n model...")
            _yolo_model = YOLO("yolov8n.pt")
            logger.info("[FrameAnalyzer] YOLOv8n loaded successfully")
        except Exception as e:
            logger.error(f"[FrameAnalyzer] Failed to load YOLO: {e}")
            raise
    return _yolo_model


@dataclass
class DetectedObject:
    """A single detected object in a frame."""
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[float, float]
    area: float


@dataclass
class FrameAnalysis:
    """Analysis result for a single frame."""
    frame_index: int
    timestamp: float
    objects: List[DetectedObject]
    blur_score: float  # Higher = sharper
    motion_score: float  # Optical flow magnitude
    brightness: float
    dominant_colors: List[Tuple[int, int, int]]
    scene_type: str = "unknown"
    quality_score: float = 0.0
    is_keyframe: bool = False


@dataclass
class SceneSegment:
    """A coherent scene within a clip."""
    start_frame: int
    end_frame: int
    start_time: float
    end_time: float
    duration: float
    dominant_objects: Dict[str, float]  # object_name -> avg_confidence
    scene_type: str
    source_clip: str = ""  # Path to the source video file
    best_frame: Optional[FrameAnalysis] = None
    quality_score: float = 0.0
    domain_relevance: float = 0.0


class FrameAnalyzer:
    """
    Analyzes video clips frame-by-frame for object detection,
    scene classification, and quality scoring.
    """
    
    def __init__(
        self,
        sample_every_n_frames: int = 2,  # Analyze every Nth frame for speed
        confidence_threshold: float = 0.25,
        temporal_window: int = 5,  # Frames for temporal smoothing
    ):
        self.sample_every_n = sample_every_n_frames
        self.conf_thresh = confidence_threshold
        self.temporal_window = temporal_window
        self.yolo = None
        
    def _init_model(self):
        if self.yolo is None:
            self.yolo = get_yolo_model()
    
    def analyze_clip(
        self,
        video_path: str,
        max_frames: Optional[int] = None
    ) -> List[FrameAnalysis]:
        """
        Analyze a video clip frame by frame.
        
        Returns a list of FrameAnalysis objects, one per analyzed frame.
        """
        self._init_model()
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(
            f"[FrameAnalyzer] Analyzing {video_path}: "
            f"{total_frames} frames @ {fps:.1f} FPS, "
            f"sampling every {self.sample_every_n} frames"
        )
        
        results = []
        prev_gray = None
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_idx % self.sample_every_n != 0:
                frame_idx += 1
                continue
            
            if max_frames and len(results) >= max_frames:
                break
            
            timestamp = frame_idx / fps
            
            # Run YOLO detection
            detections = self._detect_objects(frame)
            
            # Compute blur score (Laplacian variance)
            blur_score = self._compute_blur(frame)
            
            # Compute motion score (optical flow)
            motion_score = self._compute_motion(frame, prev_gray)
            
            # Compute brightness
            brightness = self._compute_brightness(frame)
            
            # Extract dominant colors
            dominant_colors = self._extract_dominant_colors(frame)
            
            analysis = FrameAnalysis(
                frame_index=frame_idx,
                timestamp=timestamp,
                objects=detections,
                blur_score=blur_score,
                motion_score=motion_score,
                brightness=brightness,
                dominant_colors=dominant_colors,
            )
            
            # Classify scene type
            analysis.scene_type = self._classify_scene(analysis)
            
            # Compute overall quality score
            analysis.quality_score = self._compute_quality_score(analysis)
            
            results.append(analysis)
            
            # Update previous frame for optical flow
            prev_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame_idx += 1
        
        cap.release()
        
        # Temporal smoothing
        results = self._temporal_smooth(results)
        
        logger.info(f"[FrameAnalyzer] Analyzed {len(results)} frames from {video_path}")
        return results
    
    def _detect_objects(self, frame: np.ndarray) -> List[DetectedObject]:
        """Run YOLOv8 detection on a single frame."""
        results_yolo = self.yolo(frame, verbose=False)
        detections = []
        
        for result in results_yolo:
            if result.boxes is None:
                continue
            for box in result.boxes:
                conf = float(box.conf[0])
                if conf < self.conf_thresh:
                    continue
                
                cls_id = int(box.cls[0])
                cls_name = result.names[cls_id]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                area = (x2 - x1) * (y2 - y1)
                
                detections.append(DetectedObject(
                    class_name=cls_name,
                    confidence=conf,
                    bbox=(x1, y1, x2, y2),
                    center=(center_x, center_y),
                    area=area,
                ))
        
        return detections
    
    def _compute_blur(self, frame: np.ndarray) -> float:
        """Compute blur score using Laplacian variance. Higher = sharper."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())
    
    def _compute_motion(
        self,
        frame: np.ndarray,
        prev_gray: Optional[np.ndarray]
    ) -> float:
        """Compute motion score using frame differencing (simpler than optical flow)."""
        if prev_gray is None:
            return 0.0
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Compute absolute difference between frames
        diff = cv2.absdiff(prev_gray, gray)
        
        # Threshold to ignore noise
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        
        # Motion score = percentage of pixels that changed
        motion_score = np.sum(thresh > 0) / thresh.size * 100
        
        return float(motion_score)
    
    def _compute_brightness(self, frame: np.ndarray) -> float:
        """Compute average brightness."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return float(gray.mean())
    
    def _extract_dominant_colors(
        self,
        frame: np.ndarray,
        k: int = 3
    ) -> List[Tuple[int, int, int]]:
        """Extract K dominant colors using K-means."""
        # Resize for speed
        small = cv2.resize(frame, (64, 64))
        pixels = small.reshape(-1, 3).astype(np.float32)
        
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(
            pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
        )
        
        # Sort by cluster size
        counts = np.bincount(labels.flatten())
        sorted_indices = np.argsort(-counts)
        
        colors = []
        for idx in sorted_indices:
            b, g, r = centers[idx]
            colors.append((int(r), int(g), int(b)))
        
        return colors
    
    def _classify_scene(self, analysis: FrameAnalysis) -> str:
        """
        Classify scene type based on detected objects.
        Returns one of: cooking, plating, food_closeup, dining, atmosphere,
        kitchen_prep, serving, exterior, unknown
        """
        obj_names = [o.class_name for o in analysis.objects]
        obj_counts = defaultdict(int)
        for name in obj_names:
            obj_counts[name] += 1
        
        # Cooking: oven + person + bowl/spoon + high motion
        if ("oven" in obj_counts or "microwave" in obj_counts) and \
           "person" in obj_counts and \
           analysis.motion_score > 5:
            return "cooking"
        
        # Plating: bowl/cup + person + moderate motion + careful positioning
        if ("bowl" in obj_counts or "cup" in obj_counts) and \
           "person" in obj_counts and \
           1 < analysis.motion_score < 8:
            return "plating"
        
        # Serving: person + dining table + bowl/cup
        if "person" in obj_counts and "dining table" in obj_counts and \
           ("bowl" in obj_counts or "cup" in obj_counts):
            return "serving"
        
        # Food close-up: bowl/cup/cake/pizza + no person + low motion
        food_objs = ["bowl", "cup", "cake", "pizza", "sandwich", "donut"]
        has_food = any(o in obj_counts for o in food_objs)
        if has_food and "person" not in obj_counts and analysis.motion_score < 3:
            return "food_closeup"
        
        # Dining: dining table + chair + person
        if "dining table" in obj_counts and "person" in obj_counts:
            return "dining"
        
        # Kitchen prep: refrigerator/sink + person + bowl
        if ("refrigerator" in obj_counts or "sink" in obj_counts) and \
           "person" in obj_counts:
            return "kitchen_prep"
        
        # Atmosphere: chair/couch/potted plant, low motion, no cooking
        ambient_objs = ["chair", "couch", "potted plant", "tv", "clock", "vase"]
        has_ambient = any(o in obj_counts for o in ambient_objs)
        if has_ambient and analysis.motion_score < 2:
            return "atmosphere"
        
        # Exterior: car/truck/bus
        exterior_objs = ["car", "truck", "bus", "bicycle", "motorcycle"]
        if any(o in obj_counts for o in exterior_objs):
            return "exterior"
        
        # Fallback: person present without specific context = dining/social
        if "person" in obj_counts:
            return "dining"
        
        # Generic fallback: any objects = atmosphere, nothing = unknown
        if obj_counts:
            return "atmosphere"
        
        return "unknown"
    
    def _compute_quality_score(self, analysis: FrameAnalysis) -> float:
        """
        Compute overall quality score for a frame.
        Combines sharpness, motion, brightness, and composition.
        """
        # Normalize blur score (typical range 0-1000)
        sharpness = min(analysis.blur_score / 500, 1.0)
        
        # Motion: some motion is good (action), too much is bad (shaky)
        motion = 1.0 - abs(analysis.motion_score - 5) / 10
        motion = max(0, min(1, motion))
        
        # Brightness: prefer well-lit but not overexposed (100-200 range)
        brightness = 1.0 - abs(analysis.brightness - 150) / 150
        brightness = max(0, min(1, brightness))
        
        # Composition bonus: objects near center
        center_bonus = 0.0
        for obj in analysis.objects:
            cx, cy = obj.center
            # Normalize to 0-1
            nx = cx / 1920 if cx > 1 else cx  # Assume 1920 width if pixel values
            ny = cy / 1080 if cy > 1 else cy
            dist_from_center = ((nx - 0.5) ** 2 + (ny - 0.5) ** 2) ** 0.5
            center_bonus += (1 - dist_from_center) * obj.confidence
        
        if analysis.objects:
            center_bonus /= len(analysis.objects)
        
        # Weighted combination
        score = (
            sharpness * 0.35 +
            motion * 0.20 +
            brightness * 0.25 +
            center_bonus * 0.20
        )
        
        return round(score, 3)
    
    def _temporal_smooth(
        self,
        frames: List[FrameAnalysis]
    ) -> List[FrameAnalysis]:
        """
        Smooth object detections across temporal window.
        Objects that appear in only 1 frame are likely noise.
        Objects that persist across multiple frames are real.
        """
        if len(frames) < 3:
            return frames
        
        # Track object presence across frames
        object_presence = defaultdict(list)
        for i, frame in enumerate(frames):
            for obj in frame.objects:
                object_presence[obj.class_name].append(i)
        
        # Filter objects that don't persist
        persistent_objects = set()
        for obj_name, indices in object_presence.items():
            if len(indices) >= 2:  # Appears in at least 2 sampled frames
                persistent_objects.add(obj_name)
        
        # Update frames to only include persistent objects
        for frame in frames:
            frame.objects = [
                o for o in frame.objects
                if o.class_name in persistent_objects or o.confidence > 0.6
            ]
            
            # Re-classify scene with filtered objects
            frame.scene_type = self._classify_scene(frame)
        
        return frames
    
    def segment_scenes(
        self,
        frames: List[FrameAnalysis],
        source_clip: str = "",
        scene_type_change_threshold: float = 0.5
    ) -> List[SceneSegment]:
        """
        Segment frames into coherent scenes based on scene type changes.
        
        Uses sliding-window smoothing to prevent rapid flickering,
        then merges adjacent scenes of the same type.
        Drops scenes shorter than MIN_SCENE_DURATION seconds.
        """
        if not frames:
            return []
        
        MIN_SCENE_DURATION = 1.0  # seconds
        
        # Step 1: Smooth scene types with sliding window
        # This prevents a single outlier frame from creating a new scene
        smoothed_types = []
        window_size = min(3, len(frames))
        for i in range(len(frames)):
            start = max(0, i - window_size // 2)
            end = min(len(frames), start + window_size)
            types = [frames[j].scene_type for j in range(start, end)]
            # Most common type in window wins
            from collections import Counter
            smoothed_types.append(Counter(types).most_common(1)[0][0])
        
        # Step 2: Build segments from smoothed types
        raw_segments = []
        current_start = 0
        current_type = smoothed_types[0]
        
        for i in range(1, len(smoothed_types)):
            if smoothed_types[i] != current_type:
                raw_segments.append((current_start, i, current_type))
                current_start = i
                current_type = smoothed_types[i]
        
        # Don't forget the last segment
        if current_start < len(smoothed_types):
            raw_segments.append((current_start, len(smoothed_types), current_type))
        
        # Step 3: Create SceneSegments, skip very short ones
        scenes = []
        for start_idx, end_idx, scene_type in raw_segments:
            scene_frames = frames[start_idx:end_idx]
            scene = self._create_scene_segment(scene_frames, source_clip=source_clip)
            
            # Keep scenes that are long enough OR have high quality
            if scene.duration >= MIN_SCENE_DURATION or scene.quality_score > 0.7:
                scenes.append(scene)
        
        # Step 4: If we filtered out everything, keep the best scene
        if not scenes and frames:
            best_start = 0
            best_end = len(frames)
            scenes.append(self._create_scene_segment(frames[best_start:best_end]))
        
        return scenes
    
    def _create_scene_segment(
        self,
        frames: List[FrameAnalysis],
        source_clip: str = ""
    ) -> SceneSegment:
        """Create a SceneSegment from a list of frames."""
        if not frames:
            return SceneSegment(
                start_frame=0, end_frame=0,
                start_time=0, end_time=0, duration=0,
                dominant_objects={}, scene_type="unknown",
                source_clip=source_clip
            )
        
        # Aggregate object confidences
        obj_confidences = defaultdict(list)
        for frame in frames:
            for obj in frame.objects:
                obj_confidences[obj.class_name].append(obj.confidence)
        
        dominant_objects = {
            name: round(sum(confs) / len(confs), 3)
            for name, confs in obj_confidences.items()
        }
        
        # Find best frame (highest quality score)
        best_frame = max(frames, key=lambda f: f.quality_score)
        
        # Compute scene quality (average of frame qualities)
        avg_quality = sum(f.quality_score for f in frames) / len(frames)
        
        return SceneSegment(
            start_frame=frames[0].frame_index,
            end_frame=frames[-1].frame_index,
            start_time=frames[0].timestamp,
            end_time=frames[-1].timestamp,
            duration=frames[-1].timestamp - frames[0].timestamp,
            dominant_objects=dominant_objects,
            scene_type=frames[0].scene_type,
            source_clip=source_clip,
            best_frame=best_frame,
            quality_score=round(avg_quality, 3),
        )
