"""
Audio Processor — Subtitle Generation with faster-whisper

Generates SRT subtitle files from video audio using faster-whisper.
Also handles audio extraction and trending song mixing.

Citations:
    - faster-whisper is 4x faster than original OpenAI Whisper at same accuracy
      [pypi.org/project/faster-whisper/, SYSTRAN, 2025-10-31]
    - GPU benchmark (RTX 3070 Ti, 13min audio): faster-whisper fp16 batch=8 = 17s
      vs original Whisper = 2m23s [faster-whisper official benchmark]
    - CPU benchmark (i7-12700K): faster-whisper int8 batch=8 = 51s
      vs whisper.cpp = 1m45s [faster-whisper official benchmark]
    - Whisper Large-v3: 2.7% WER on LibriSpeech clean
      [novascribe.ai/how-accurate-is-whisper, 2026-04-15]
    - Whisper supports 99+ languages (critical for Almaty Russian/Kazakh/English mix)
      [Radford et al. 2022, arXiv:2212.04356]
    - Whisper small model (244M params): 6x real-time on GPU, WER ~6-9%
      [openwhispr.com/blog/how-whisper-ai-works, 2026-02-17]
    - Whisper hallucinates on music+speech mixed audio
      [novascribe.ai/how-accurate-is-whisper, 2026-04-15]
      -> Extract audio BEFORE adding trending song track
    - FFmpeg can extract audio and burn subtitles in <2 seconds
      [williamhuster.com/automatically-subtitle-videos/, 2023-08-12]
"""

import os
import uuid
from typing import Optional, Dict

# Import faster-whisper lazily to avoid startup cost
_faster_whisper = None

def _get_whisper_model(model_size: str = "small"):
    """Lazy-load faster-whisper model."""
    global _faster_whisper
    if _faster_whisper is None:
        from faster_whisper import WhisperModel
        # Use CPU with int8 for compatibility (no GPU required)
        _faster_whisper = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _faster_whisper


def extract_audio(video_path: str, output_wav: Optional[str] = None) -> str:
    """
    Extract audio from video to WAV using FFmpeg.
    
    FFmpeg extraction is the standard preprocessing step for Whisper.
    [digitalocean.com/community/tutorials/how-to-generate-and-add-subtitles, 2024]
    """
    import subprocess
    
    if output_wav is None:
        output_wav = video_path.rsplit(".", 1)[0] + "_audio.wav"
    
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        output_wav
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return output_wav
    except Exception as e:
        print(f"[audio] Extraction error: {e}")
    
    return ""


def generate_subtitles(
    video_path: str,
    output_srt: Optional[str] = None,
    model_size: str = "small",
    language: Optional[str] = None
) -> str:
    """
    Generate SRT subtitles from video audio using faster-whisper.
    
    Returns path to SRT file.
    
    For Almaty restaurants, auto-detect language (Russian/Kazakh/English mix).
    Whisper handles code-switching well in the small model.
    """
    if output_srt is None:
        output_srt = video_path.rsplit(".", 1)[0] + ".srt"
    
    # Extract audio first
    audio_path = extract_audio(video_path)
    if not audio_path or not os.path.exists(audio_path):
        print("[audio] Failed to extract audio, skipping subtitles")
        return ""
    
    try:
        model = _get_whisper_model(model_size)
        
        segments, info = model.transcribe(
            audio_path,
            language=language,
            task="transcribe",
            vad_filter=True,  # Skip silent sections (reduces hallucination)
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        detected_language = info.language
        print(f"[audio] Detected language: {detected_language}")
        
        # Write SRT file
        with open(output_srt, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments):
                start = segment.start
                end = segment.end
                text = segment.text.strip()
                
                f.write(f"{i + 1}\n")
                f.write(f"{_format_srt_time(start)} --> {_format_srt_time(end)}\n")
                f.write(f"{text}\n\n")
        
        # Clean up audio file
        try:
            os.remove(audio_path)
        except Exception:
            pass
        
        return output_srt
    
    except Exception as e:
        print(f"[audio] Transcription error: {e}")
        # Clean up audio file
        try:
            os.remove(audio_path)
        except Exception:
            pass
        return ""


def _format_srt_time(seconds: float) -> str:
    """Format seconds as SRT timecode: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def extract_hook_phrase(srt_path: str, max_words: int = 6) -> str:
    """
    Extract the most "hook-like" phrase from subtitles.
    
    Strategy: Find the first non-trivial segment with emotional words.
    This is a simple heuristic; more advanced NLP could be added later.
    """
    if not srt_path or not os.path.exists(srt_path):
        return ""
    
    emotional_words = {
        "amazing", "incredible", "delicious", "must", "try", "best",
        "unreal", "fire", "insane", "perfect", "fresh", "authentic",
        "tasty", "yummy", "wow", "love", "favorite", "popular",
        "special", "secret", "hidden", "gem", "only", "limited"
    }
    
    best_phrase = ""
    best_score = -1
    
    try:
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Parse simple SRT
        blocks = content.strip().split("\n\n")
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) >= 3:
                text = " ".join(lines[2:]).strip()
                words = text.lower().split()
                score = sum(1 for w in words if w.strip(".,!?;:") in emotional_words)
                # Prefer shorter, earlier phrases
                position_penalty = blocks.index(block) * 0.1
                score -= position_penalty
                if score > best_score and len(words) <= max_words * 2:
                    best_score = score
                    best_phrase = text
    except Exception as e:
        print(f"[audio] Hook extraction error: {e}")
    
    # If no emotional words found, return first short phrase
    if not best_phrase:
        try:
            with open(srt_path, "r", encoding="utf-8") as f:
                content = f.read()
            blocks = content.strip().split("\n\n")
            for block in blocks:
                lines = block.strip().split("\n")
                if len(lines) >= 3:
                    text = " ".join(lines[2:]).strip()
                    if len(text.split()) <= max_words * 2:
                        return text
        except Exception:
            pass
    
    return best_phrase
