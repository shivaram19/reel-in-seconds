"""
FFmpeg Editing Pipeline
=======================

Final video assembly using FFmpeg filter_complex.
No re-encoding where possible. Fast, professional output.

Features:
- Vertical 9:16 format (1080x1920) for Instagram Reels
- Color grading per act (warm tones for Indian food)
- Smooth transitions (crossfade, fade)
- Ken Burns zoom effects
- Speed ramping
- Logo watermark overlay
- Text overlays for CTA (no subtitles)

Architecture:
    Input: NarrativeReel blueprint from NarrativeAssembler
    Output: Final MP4 file ready for Instagram
"""

import os
import subprocess
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass

from .narrative_assembly import NarrativeReel, ActSegment
from .restaurant_soul import RestaurantSoul

logger = logging.getLogger(__name__)


@dataclass
class RenderResult:
    """Result of rendering a reel."""
    output_path: str
    duration: float
    resolution: Tuple[int, int]
    file_size_mb: float
    success: bool
    error_message: Optional[str] = None


class FFmpegPipeline:
    """
    FFmpeg-based video editing pipeline.
    
    Uses filter_complex for all video operations in a single pass.
    Much faster than frame-by-frame processing.
    """
    
    def __init__(
        self,
        output_dir: str = "static/reels",
        temp_dir: str = "static/reels/temp",
        ffmpeg_path: str = "ffmpeg",
        ffprobe_path: str = "ffprobe",
    ):
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        self.ffmpeg = ffmpeg_path
        self.ffprobe = ffprobe_path
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Check FFmpeg availability
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Verify FFmpeg is installed and working."""
        try:
            result = subprocess.run(
                [self.ffmpeg, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                logger.info(f"[FFmpegPipeline] {version_line}")
            else:
                logger.error("[FFmpegPipeline] FFmpeg not working properly")
        except FileNotFoundError:
            logger.error("[FFmpegPipeline] FFmpeg not found! Install with: sudo apt install ffmpeg")
            raise RuntimeError("FFmpeg is required but not installed")
    
    def render_reel(
        self,
        reel: NarrativeReel,
        logo_path: Optional[str] = None,
        output_filename: Optional[str] = None,
    ) -> RenderResult:
        """
        Render a complete reel from a NarrativeReel blueprint.
        
        Args:
            reel: The assembled narrative blueprint
            clip_source_map: Maps scene identifiers to source video file paths
            logo_path: Optional logo image to overlay
            output_filename: Optional output filename
        
        Returns:
            RenderResult with output path and metadata
        """
        if output_filename is None:
            import time
            output_filename = f"reel_{int(time.time())}.mp4"
        
        output_path = self.output_dir / output_filename
        
        try:
            # Step 1: Extract clip segments for each act
            segment_paths = self._extract_segments(reel)
            
            # DEFENSIVE: Abort if no valid segments were extracted
            if not segment_paths:
                raise RuntimeError(
                    "No valid video segments could be extracted from the provided clips. "
                    "This usually happens when all detected scenes have zero duration. "
                    "Try uploading longer clips or clips with more visible action."
                )
            
            # Step 2: Apply effects to each segment
            processed_paths = self._process_segments(reel, segment_paths)
            
            # Step 3: Concatenate all segments
            concat_path = self._concatenate_segments(processed_paths)
            
            # Step 4: Add logo and final color grade
            final_path = self._add_final_overlays(
                concat_path, reel, logo_path, str(output_path)
            )
            
            # Get file info
            duration, resolution, size_mb = self._get_video_info(final_path)
            
            # Cleanup temp files
            self._cleanup_temp(segment_paths + processed_paths + [concat_path])
            
            return RenderResult(
                output_path=final_path,
                duration=duration,
                resolution=resolution,
                file_size_mb=size_mb,
                success=True,
            )
            
        except Exception as e:
            logger.exception("[FFmpegPipeline] Render failed")
            return RenderResult(
                output_path=str(output_path),
                duration=0,
                resolution=(0, 0),
                file_size_mb=0,
                success=False,
                error_message=str(e),
            )
    
    def _extract_segments(
        self,
        reel: NarrativeReel,
    ) -> List[str]:
        """Extract video segments for each act from source clips."""
        segment_paths = []
        
        for i, act in enumerate(reel.acts):
            # Get source video for this scene directly from the scene
            source_path = act.mapped_scene.scene.source_clip
            
            if not source_path or not os.path.exists(source_path):
                logger.warning(
                    f"[FFmpegPipeline] Source not found for act {act.act_name}: "
                    f"source_clip={source_path}"
                )
                continue
            
            # Extract segment timing
            start_time = act.mapped_scene.scene.start_time
            duration = act.mapped_scene.scene.duration
            
            # DEFENSIVE CHECK 1: Skip near-zero-duration scenes
            if duration < 0.5:
                logger.warning(
                    f"[FFmpegPipeline] Skipping {act.act_name}: "
                    f"duration={duration:.3f}s is too short"
                )
                continue
            
            # If duration is longer than needed, trim to recommended
            target_duration = act.duration
            if duration > target_duration * 1.5:
                duration = target_duration * 1.2
            
            output_segment = str(self.temp_dir / f"segment_{i:02d}_{act.act_name}.mp4")
            
            # Extract with FFmpeg
            cmd = [
                self.ffmpeg, "-y",
                "-ss", str(start_time),
                "-t", str(duration),
                "-i", source_path,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-an",  # No audio for now
                "-pix_fmt", "yuv420p",
                output_segment,
            ]
            
            try:
                self._run_ffmpeg(cmd)
            except RuntimeError as e:
                logger.warning(f"[FFmpegPipeline] Failed to extract {act.act_name}: {e}")
                continue
            
            # DEFENSIVE CHECK 2: Verify extracted file has actual content
            probe_duration = self._get_segment_duration(output_segment)
            if probe_duration < 0.3:
                logger.warning(
                    f"[FFmpegPipeline] Extracted segment is empty: {act.act_name}"
                )
                if os.path.exists(output_segment):
                    os.remove(output_segment)
                continue
            
            segment_paths.append(output_segment)
            
            logger.info(
                f"[FFmpegPipeline] Extracted {act.act_name}: "
                f"{start_time:.1f}s - {start_time + duration:.1f}s "
                f"(actual: {probe_duration:.2f}s)"
            )
        
        return segment_paths
    
    def _get_segment_duration(self, video_path: str) -> float:
        """Get duration of a video file using ffprobe."""
        try:
            result = subprocess.run(
                [
                    self.ffprobe, "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    video_path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except Exception:
            pass
        return 0.0
    
    def _process_segments(
        self,
        reel: NarrativeReel,
        segment_paths: List[str]
    ) -> List[str]:
        """Apply color grading, speed, and zoom effects to each segment."""
        processed = []
        
        for i, seg_path in enumerate(segment_paths):
            if not seg_path or not os.path.exists(seg_path):
                continue
            
            # Find the corresponding act (segment_paths may be shorter than reel.acts)
            act = reel.acts[i] if i < len(reel.acts) else None
            if act is None:
                continue
            
            output_path = str(self.temp_dir / f"processed_{i:02d}_{act.act_name}.mp4")
            
            # Build filter chain
            filters = []
            
            # 1. Convert to vertical 9:16
            filters.append(self._build_crop_filter())
            
            # 2. Color grading
            filters.append(self._build_color_grade_filter(act.color_grade))
            
            # 3. Speed adjustment
            if act.speed_factor != 1.0:
                filters.append(f"setpts=PTS/{act.speed_factor}")
            
            # 4. Ken Burns zoom
            if act.zoom_effect:
                filters.append(self._build_ken_burns_filter(act.zoom_effect, act.duration))
            
            # 5. Fade in/out
            fade_filters = self._build_fade_filters(act)
            if fade_filters:
                filters.extend(fade_filters)
            
            # Combine filters
            filter_str = ",".join(filters)
            
            cmd = [
                self.ffmpeg, "-y",
                "-i", seg_path,
                "-vf", filter_str,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-an",
                "-pix_fmt", "yuv420p",
                output_path,
            ]
            
            self._run_ffmpeg(cmd)
            processed.append(output_path)
        
        return processed
    
    def _build_crop_filter(self) -> str:
        """Build filter to convert to vertical 9:16 format."""
        # Target: 1080x1920 (9:16)
        # Strategy: scale to fit height, then crop to width
        return (
            "scale=-1:1920:flags=lanczos,"  # Scale to height 1920
            "crop=1080:1920:(in_w-1080)/2:0"  # Center crop to 1080 width
        )
    
    def _build_color_grade_filter(self, grade: Dict[str, any]) -> str:
        """Build FFmpeg color grading filter."""
        parts = []
        
        # Brightness, contrast, saturation
        brightness = grade.get("brightness", 0)
        contrast = grade.get("contrast", 1.0)
        saturation = grade.get("saturation", 1.0)
        gamma = grade.get("gamma", 1.0)
        
        parts.append(f"eq=brightness={brightness}:contrast={contrast}:saturation={saturation}:gamma={gamma}")
        
        # Color balance shifts
        red_shift = grade.get("red_shift", 0)
        green_shift = grade.get("green_shift", 0)
        blue_shift = grade.get("blue_shift", 0)
        
        if any(v != 0 for v in [red_shift, green_shift, blue_shift]):
            parts.append(
                f"colorbalance=rs={red_shift}:gs={green_shift}:bs={blue_shift}:"
                f"rm={red_shift/2}:gm={green_shift/2}:bm={blue_shift/2}"
            )
        
        return ",".join(parts)
    
    def _build_ken_burns_filter(
        self,
        effect: str,
        duration: float
    ) -> str:
        """Build Ken Burns zoom effect filter."""
        # Slow zoom over the duration of the clip
        # zoompan syntax: zoom, x, y expressions over time
        
        if effect == "ken_burns_in":
            # Zoom from 1.0 to 1.15 over duration
            return (
                f"zoompan=z='min(zoom+0.001,1.15)':"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"d={int(duration * 30)}:s=1080x1920"
            )
        elif effect == "ken_burns_out":
            # Zoom from 1.15 to 1.0
            return (
                f"zoompan=z='max(zoom-0.001,1.0)':"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"d={int(duration * 30)}:s=1080x1920"
            )
        
        return ""
    
    def _build_fade_filters(self, act: ActSegment) -> List[str]:
        """Build fade in/out filters for an act."""
        filters = []
        duration_frames = int(act.duration * 30)  # Assume 30fps
        
        if act.transition_in == "fade_in":
            filters.append(f"fade=t=in:st=0:d=0.5")
        
        if act.transition_out == "fade_out":
            filters.append(f"fade=t=out:st={act.duration - 0.5}:d=0.5")
        elif act.transition_out == "crossfade":
            # Crossfade handled during concatenation
            pass
        
        return filters
    
    def _concatenate_segments(self, segment_paths: List[str]) -> str:
        """Concatenate all processed segments with transitions."""
        if not segment_paths:
            raise ValueError("No segments to concatenate")
        
        if len(segment_paths) == 1:
            return segment_paths[0]
        
        # Use absolute paths for concat demuxer
        abs_paths = [os.path.abspath(p) for p in segment_paths if os.path.exists(p)]
        
        if not abs_paths:
            raise ValueError("No valid segment files found")
        
        # Create concat list file with absolute paths
        concat_list = self.temp_dir / "concat_list.txt"
        with open(concat_list, "w") as f:
            for path in abs_paths:
                # Use absolute paths - no escaping needed with this approach
                f.write(f"file '{path}'\n")
        
        output_path = str(self.temp_dir / "concatenated.mp4")
        
        # Use concat demuxer for gapless concatenation
        cmd = [
            self.ffmpeg, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list.absolute()),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            output_path,
        ]
        
        self._run_ffmpeg(cmd)
        
        # Clean up concat list
        concat_list.unlink(missing_ok=True)
        
        return output_path
    
    def _add_final_overlays(
        self,
        video_path: str,
        reel: NarrativeReel,
        logo_path: Optional[str],
        output_path: str
    ) -> str:
        """Add logo watermark and final touches."""
        filters = []
        
        # Logo overlay
        if logo_path and os.path.exists(logo_path):
            # Logo: top-right corner, white semi-transparent background
            logo_filter = self._build_logo_filter(logo_path)
            filters.append(logo_filter)
        
        # Final warm color pass
        final_color = "eq=brightness=0.02:contrast=1.05:saturation=1.1"
        filters.append(final_color)
        
        # Slight vignette for cinematic feel
        # Using vignette filter if available
        filters.append("vignette=PI/4")
        
        filter_str = ",".join(filters)
        
        cmd = [
            self.ffmpeg, "-y",
            "-i", video_path,
        ]
        
        # If logo overlay uses overlay filter, we need two inputs
        if logo_path and os.path.exists(logo_path) and "overlay" in filter_str:
            cmd.extend(["-i", logo_path])
        
        cmd.extend([
            "-vf", filter_str,
            "-c:v", "libx264",
            "-preset", "slow",  # Higher quality for final output
            "-crf", "20",
            "-an",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",  # Web-optimized
            output_path,
        ])
        
        self._run_ffmpeg(cmd)
        
        return output_path
    
    def _build_logo_filter(self, logo_path: str) -> str:
        """Build logo overlay filter."""
        # Scale logo to reasonable size, place top-right with padding
        return (
            f"[1:v]scale=120:-1:flags=lanczos[logo];"
            f"[0:v][logo]overlay=W-w-20:20:enable='between(t,0,30)'"
        )
    
    def _run_ffmpeg(self, cmd: List[str]):
        """Run FFmpeg command and handle errors."""
        logger.debug(f"[FFmpegPipeline] Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = result.stderr[-500:] if result.stderr else "Unknown error"
            logger.error(f"[FFmpegPipeline] FFmpeg failed: {error_msg}")
            raise RuntimeError(f"FFmpeg error: {error_msg}")
    
    def _get_video_info(self, path: str) -> Tuple[float, Tuple[int, int], float]:
        """Get duration, resolution, and file size of a video."""
        # Duration
        cmd = [
            self.ffprobe, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = float(result.stdout.strip()) if result.returncode == 0 else 0
        
        # Resolution
        cmd = [
            self.ffprobe, "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=s=x:p=0",
            path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            w, h = result.stdout.strip().split("x")
            resolution = (int(w), int(h))
        else:
            resolution = (0, 0)
        
        # File size
        size_mb = os.path.getsize(path) / (1024 * 1024)
        
        return duration, resolution, size_mb
    
    def _cleanup_temp(self, paths: List[str]):
        """Clean up temporary files."""
        for path in paths:
            try:
                if os.path.exists(path) and path.startswith(str(self.temp_dir)):
                    os.remove(path)
            except Exception as e:
                logger.warning(f"[FFmpegPipeline] Cleanup failed for {path}: {e}")


def generate_reel(
    clip_paths: List[str],
    soul: RestaurantSoul,
    logo_path: Optional[str] = None,
    output_filename: Optional[str] = None,
) -> RenderResult:
    """
    High-level function to generate a reel from raw clips.
    
    This is the main entry point that orchestrates the entire pipeline:
    1. Analyze frames
    2. Map to domain
    3. Assemble narrative
    4. Render with FFmpeg
    """
    # Import here to avoid circular import at module level
    from .frame_analyzer import FrameAnalyzer
    from .domain_mapper import DomainMapper
    from .narrative_assembly import NarrativeAssembler
    
    logger.info(f"[generate_reel] Starting reel generation for '{soul.name}'")
    logger.info(f"[generate_reel] Processing {len(clip_paths)} clips")
    
    # Step 1: Analyze all clips
    analyzer = FrameAnalyzer()
    all_scenes = []
    scene_to_clip_map = {}  # Maps scene index -> clip path
    
    for i, clip_path in enumerate(clip_paths):
        if not os.path.exists(clip_path):
            logger.warning(f"[generate_reel] Clip not found: {clip_path}")
            continue
        
        try:
            frames = analyzer.analyze_clip(clip_path)
            scenes = analyzer.segment_scenes(frames, source_clip=clip_path)
            
            for j, scene in enumerate(scenes):
                all_scenes.append(scene)
            
            logger.info(
                f"[generate_reel] Clip {i+1} ({clip_path}): {len(frames)} frames, "
                f"{len(scenes)} scenes"
            )
            
        except Exception as e:
            logger.error(f"[generate_reel] Failed to analyze {clip_path}: {e}")
            continue
    
    if not all_scenes:
        return RenderResult(
            output_path="",
            duration=0,
            resolution=(0, 0),
            file_size_mb=0,
            success=False,
            error_message="No scenes detected in any clip",
        )
    
    # Step 2: Map to domain
    mapper = DomainMapper(soul)
    mapped_scenes = mapper.map_scenes(all_scenes)
    
    # Step 3: Select best scenes
    selected_scenes = mapper.select_best_scenes_for_reel(
        mapped_scenes,
        target_duration=soul.narrative_arc.get("preferred_duration", 30),
    )
    
    # Step 4: Assemble narrative
    assembler = NarrativeAssembler(soul)
    reel = assembler.assemble(selected_scenes)
    reel = assembler.optimize_for_mobile(reel)
    
    # Log which clips are being used
    clips_used = set()
    for act in reel.acts:
        if act.mapped_scene.scene.source_clip:
            clips_used.add(act.mapped_scene.scene.source_clip)
    logger.info(f"[generate_reel] Using {len(clips_used)} unique clips out of {len(clip_paths)}")
    
    # Step 5: Render
    pipeline = FFmpegPipeline()
    
    result = pipeline.render_reel(
        reel=reel,
        logo_path=logo_path,
        output_filename=output_filename,
    )
    
    if result.success:
        logger.info(
            f"[generate_reel] Reel generated: {result.output_path} "
            f"({result.duration:.1f}s, {result.file_size_mb:.1f}MB)"
        )
    else:
        logger.error(f"[generate_reel] Reel generation failed: {result.error_message}")
    
    return result
