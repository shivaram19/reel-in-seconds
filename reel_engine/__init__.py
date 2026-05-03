"""
Sabrika Brand Manager - Reel Editing Engine
===========================================

Frame-by-frame, domain-aware video editing engine for restaurant reels.

Pipeline (New V2):
    1. Clip Ingestion (upload raw phone clips)
    2. Frame Analysis (YOLOv8 + OpenCV per frame)
    3. Domain Mapping (restaurant relevance scoring)
    4. Scene Understanding (classify cooking/plating/dining/atmosphere)
    5. Narrative Assembly (6-act structure with restaurant soul)
    6. FFmpeg Output (filter_complex with color grading + transitions)

No subtitles. Pure visual storytelling.
"""

# V2 Engine (new frame-by-frame analysis)
from .restaurant_soul import RestaurantSoul, get_pakwaan_soul, get_soul
from .frame_analyzer import FrameAnalyzer
from .domain_mapper import DomainMapper
from .narrative_assembly import NarrativeAssembler
from .ffmpeg_pipeline import FFmpegPipeline, generate_reel as generate_reel_v2

# V1 Engine (original pipeline - kept for compatibility)
from .render_pipeline import generate_reel

__all__ = [
    # V2
    "RestaurantSoul",
    "get_pakwaan_soul",
    "get_soul",
    "FrameAnalyzer",
    "DomainMapper",
    "NarrativeAssembler",
    "FFmpegPipeline",
    "generate_reel_v2",
    # V1
    "generate_reel",
]
