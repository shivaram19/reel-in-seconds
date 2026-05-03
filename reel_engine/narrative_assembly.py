"""
Narrative Assembly Engine
=========================

Assembles mapped scenes into a coherent 6-act narrative reel.
No subtitles. Pure visual storytelling driven by the restaurant's soul.

The 6-Act Cinematic Formula:
    1. HOOK (0-3s): The scroll-stopper. Most tempting shot.
    2. PROMISE (3-8s): The tease. What's coming? Hands, spices, fire.
    3. PROCESS (8-20s): The craft. Cooking, sizzling, steam rising.
    4. PAYOFF (20-25s): The money shot. The final dish, glistening.
    5. SOCIAL (25-28s): The feeling. People sharing, laughing, belonging.
    6. CTA (28-30s): The invitation. Location, contact, "come home."

Each act is assembled from the best available scene of that type.
Transitions, pacing, and color grading are chosen based on the
restaurant's soul profile.
"""

import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from pathlib import Path

from .restaurant_soul import RestaurantSoul
from .domain_mapper import MappedScene

logger = logging.getLogger(__name__)


@dataclass
class ActSegment:
    """A single act in the narrative reel."""
    act_name: str  # hook, promise, process, payoff, social, cta
    start_time: float  # seconds in final reel
    duration: float
    mapped_scene: MappedScene
    transition_in: str  # cut, fade, zoom_in, zoom_out, etc.
    transition_out: str
    color_grade: Dict[str, any]  # FFmpeg color parameters
    speed_factor: float = 1.0  # 1.0 = normal, 1.5 = fast, 0.7 = slow
    zoom_effect: Optional[str] = None  # ken_burns_in, ken_burns_out, static


@dataclass
class NarrativeReel:
    """Complete assembled reel blueprint."""
    acts: List[ActSegment]
    total_duration: float
    soul: RestaurantSoul
    template_name: str
    music_mood: str
    color_temperature: str
    target_resolution: Tuple[int, int] = (1080, 1920)  # 9:16 vertical
    
    def get_timeline(self) -> List[Dict]:
        """Get human-readable timeline."""
        timeline = []
        for act in self.acts:
            timeline.append({
                "act": act.act_name,
                "time": f"{act.start_time:.1f}s - {act.start_time + act.duration:.1f}s",
                "duration": f"{act.duration:.1f}s",
                "scene_type": act.mapped_scene.scene.scene_type,
                "emotion": act.mapped_scene.emotional_tone,
                "transition": act.transition_in,
                "why": act.mapped_scene.why_included,
            })
        return timeline


class NarrativeAssembler:
    """
    Assembles scenes into a 6-act narrative reel.
    
    This is the director's chair — deciding what goes where,
    how long it stays, and what feeling it creates.
    """
    
    # Act timing templates (in seconds)
    ACT_TEMPLATES = {
        "heritage": {
            # Slow, majestic, respectful — for traditional cuisine
            "hook": (0, 3.0),
            "promise": (3.0, 5.0),
            "process": (8.0, 10.0),
            "payoff": (18.0, 5.0),
            "social": (23.0, 4.0),
            "cta": (27.0, 3.0),
        },
        "energetic": {
            # Fast, punchy, exciting — for street food / busy scenes
            "hook": (0, 2.5),
            "promise": (2.5, 3.5),
            "process": (6.0, 8.0),
            "payoff": (14.0, 4.0),
            "social": (18.0, 3.0),
            "cta": (21.0, 2.5),
        },
        "warm": {
            # Balanced, homey, inviting — for family/casual dining
            "hook": (0, 3.0),
            "promise": (3.0, 4.5),
            "process": (7.5, 8.5),
            "payoff": (16.0, 4.5),
            "social": (20.5, 4.0),
            "cta": (24.5, 3.0),
        },
    }
    
    def __init__(self, soul: RestaurantSoul):
        self.soul = soul
        self.template = self._select_template()
        logger.info(
            f"[NarrativeAssembler] Initialized with '{self.template}' template "
            f"for '{soul.name}'"
        )
    
    def _select_template(self) -> str:
        """Select timing template based on restaurant soul."""
        pacing = self.soul.narrative_arc.get("pacing", "moderate")
        
        if pacing == "slow":
            return "heritage"
        elif pacing == "fast":
            return "energetic"
        else:
            return "warm"
    
    def assemble(
        self,
        mapped_scenes: List[MappedScene],
        target_duration: float = 30.0
    ) -> NarrativeReel:
        """
        Assemble scenes into a 6-act narrative reel.
        
        The assembly process:
        1. Map scenes to narrative roles
        2. Select best scene for each act
        3. Compute precise timing for each act
        4. Assign transitions and color grading
        5. Build the final reel blueprint
        """
        
        # Group scenes by narrative role
        scenes_by_role = self._group_by_role(mapped_scenes)
        
        # Build each act
        acts = []
        current_time = 0.0
        
        act_sequence = ["hook", "promise", "process", "payoff", "social", "cta"]
        
        used_scenes = set()  # Track scenes already assigned to an act
        
        for act_name in act_sequence:
            # Find best scene for this act
            available_scenes = scenes_by_role.get(act_name, [])
            
            # Filter out already-used scenes, preferring unused ones
            unused = [s for s in available_scenes if id(s) not in used_scenes]
            if unused:
                available_scenes = unused
            elif available_scenes:
                # All scenes for this role are used; that's okay if we have substitutes
                pass
            
            if not available_scenes:
                # Try to borrow from related roles
                available_scenes = self._find_substitute_scenes(
                    act_name, scenes_by_role
                )
                # Filter out already-used scenes from substitutes too
                available_scenes = [s for s in available_scenes if id(s) not in used_scenes]
            
            if not available_scenes:
                logger.warning(
                    f"[NarrativeAssembler] No scene available for act '{act_name}'"
                )
                continue
            
            # Select the best scene for this act
            best_scene = self._select_best_scene_for_act(act_name, available_scenes)
            used_scenes.add(id(best_scene))
            
            # Compute timing
            act_start, act_duration = self._compute_act_timing(
                act_name, current_time, target_duration
            )
            
            # Determine transitions
            transition_in = self._get_transition_in(act_name, acts)
            transition_out = self._get_transition_out(act_name)
            
            # Determine color grading
            color_grade = self._get_color_grade(act_name)
            
            # Determine speed and zoom
            speed_factor = self._get_speed_factor(act_name)
            zoom_effect = self._get_zoom_effect(act_name, best_scene)
            
            act_segment = ActSegment(
                act_name=act_name,
                start_time=act_start,
                duration=act_duration,
                mapped_scene=best_scene,
                transition_in=transition_in,
                transition_out=transition_out,
                color_grade=color_grade,
                speed_factor=speed_factor,
                zoom_effect=zoom_effect,
            )
            
            acts.append(act_segment)
            current_time = act_start + act_duration
        
        # Build final reel
        reel = NarrativeReel(
            acts=acts,
            total_duration=current_time,
            soul=self.soul,
            template_name=self.template,
            music_mood=self._select_music_mood(),
            color_temperature=self.soul.narrative_arc.get("color_temperature", "warm"),
        )
        
        logger.info(
            f"[NarrativeAssembler] Assembled reel: {reel.total_duration:.1f}s, "
            f"{len(reel.acts)} acts, template='{reel.template_name}'"
        )
        
        return reel
    
    def _group_by_role(
        self,
        mapped_scenes: List[MappedScene]
    ) -> Dict[str, List[MappedScene]]:
        """Group scenes by their narrative role."""
        groups = {}
        for scene in mapped_scenes:
            role = scene.narrative_role
            if role not in groups:
                groups[role] = []
            groups[role].append(scene)
        
        # Sort each group by priority
        for role in groups:
            groups[role].sort(key=lambda s: s.priority_score, reverse=True)
        
        return groups
    
    def _find_substitute_scenes(
        self,
        act_name: str,
        scenes_by_role: Dict[str, List[MappedScene]]
    ) -> List[MappedScene]:
        """Find substitute scenes when exact role is unavailable."""
        substitutes = {
            "hook": ["payoff", "promise", "food_closeup"],
            "promise": ["process", "hook", "plating"],
            "process": ["promise", "kitchen_prep", "plating"],
            "payoff": ["hook", "food_closeup", "plating"],
            "social": ["dining", "serving", "atmosphere"],
            "cta": ["atmosphere", "exterior", "social"],
        }
        
        for sub_role in substitutes.get(act_name, []):
            if sub_role in scenes_by_role and scenes_by_role[sub_role]:
                return scenes_by_role[sub_role]
        
        # Return any available scene as last resort
        all_scenes = []
        for scenes in scenes_by_role.values():
            all_scenes.extend(scenes)
        
        return sorted(all_scenes, key=lambda s: s.priority_score, reverse=True)[:3]
    
    def _select_best_scene_for_act(
        self,
        act_name: str,
        scenes: List[MappedScene]
    ) -> MappedScene:
        """Select the best scene for a specific act."""
        # For hook: highest visual impact (blur score + food closeup)
        if act_name == "hook":
            return max(scenes, key=lambda s: (
                s.domain_relevance * 0.5 +
                s.scene.quality_score * 0.5
            ))
        
        # For payoff: highest quality + food relevance
        if act_name == "payoff":
            return max(scenes, key=lambda s: (
                s.domain_relevance * 0.6 +
                s.scene.quality_score * 0.4
            ))
        
        # For process: highest motion + cooking relevance
        if act_name == "process":
            return max(scenes, key=lambda s: (
                s.domain_relevance * 0.4 +
                s.scene.quality_score * 0.3 +
                (s.scene.best_frame.motion_score / 10 if s.scene.best_frame else 0) * 0.3
            ))
        
        # Default: highest priority score
        return max(scenes, key=lambda s: s.priority_score)
    
    def _compute_act_timing(
        self,
        act_name: str,
        current_time: float,
        target_duration: float
    ) -> Tuple[float, float]:
        """Compute start time and duration for an act."""
        template = self.ACT_TEMPLATES.get(self.template, self.ACT_TEMPLATES["warm"])
        
        if act_name in template:
            _, duration = template[act_name]
        else:
            duration = 3.0
        
        # Adjust if we're running over time
        remaining = target_duration - current_time
        if remaining < duration:
            duration = max(remaining, 1.5)
        
        return current_time, duration
    
    def _get_transition_in(
        self,
        act_name: str,
        previous_acts: List[ActSegment]
    ) -> str:
        """Determine transition into this act."""
        if not previous_acts:
            return "fade_in"  # First act fades in
        
        transition_style = self.soul.narrative_arc.get("transition_style", "soft_fade")
        
        if transition_style == "hard_cut":
            return "cut"
        elif transition_style == "soft_fade":
            return "crossfade"
        else:
            # Default: varies by act
            transitions = {
                "hook": "fade_in",
                "promise": "crossfade",
                "process": "cut",
                "payoff": "crossfade",
                "social": "cut",
                "cta": "fade_in",
            }
            return transitions.get(act_name, "cut")
    
    def _get_transition_out(self, act_name: str) -> str:
        """Determine transition out of this act."""
        transitions = {
            "hook": "crossfade",
            "promise": "cut",
            "process": "crossfade",
            "payoff": "cut",
            "social": "crossfade",
            "cta": "fade_out",
        }
        return transitions.get(act_name, "cut")
    
    def _get_color_grade(self, act_name: str) -> Dict[str, any]:
        """Determine color grading parameters for an act."""
        color_temp = self.soul.narrative_arc.get("color_temperature", "warm")
        
        # Base warm grade for Indian food
        base_grade = {
            "brightness": 0.0,
            "contrast": 1.1,
            "saturation": 1.2,
            "gamma": 1.0,
            "red_shift": 0.05,  # Warm red
            "green_shift": 0.02,
            "blue_shift": -0.05,  # Reduce blue for warmth
        }
        
        # Act-specific adjustments
        act_adjustments = {
            "hook": {
                "contrast": 1.2,
                "saturation": 1.3,
                "brightness": 0.05,
            },
            "promise": {
                "contrast": 1.15,
                "saturation": 1.25,
            },
            "process": {
                "contrast": 1.1,
                "saturation": 1.15,
                "red_shift": 0.08,  # Extra warm for cooking
            },
            "payoff": {
                "contrast": 1.15,
                "saturation": 1.3,
                "brightness": 0.08,
                "red_shift": 0.06,
            },
            "social": {
                "contrast": 1.05,
                "saturation": 1.1,
                "brightness": 0.03,
            },
            "cta": {
                "contrast": 1.1,
                "saturation": 1.2,
                "brightness": 0.05,
            },
        }
        
        grade = base_grade.copy()
        if act_name in act_adjustments:
            grade.update(act_adjustments[act_name])
        
        return grade
    
    def _get_speed_factor(self, act_name: str) -> float:
        """Determine playback speed for an act."""
        speed_map = {
            "hook": 1.0,
            "promise": 0.9,  # Slightly slow for anticipation
            "process": 1.1,  # Slightly fast for energy
            "payoff": 0.85,  # Slow for savoring
            "social": 1.0,
            "cta": 1.0,
        }
        return speed_map.get(act_name, 1.0)
    
    def _get_zoom_effect(
        self,
        act_name: str,
        scene: MappedScene
    ) -> Optional[str]:
        """Determine zoom effect for an act."""
        # Only apply zoom to high-quality static shots
        if scene.scene.quality_score < 0.6:
            return None
        
        if scene.scene.best_frame and scene.scene.best_frame.motion_score > 5:
            return None  # Too much motion for zoom
        
        zoom_map = {
            "hook": "ken_burns_in",  # Slow zoom in to draw attention
            "payoff": "ken_burns_in",  # Zoom into the dish
            "promise": None,
            "process": None,  # Keep motion natural
            "social": None,
            "cta": None,
        }
        
        return zoom_map.get(act_name)
    
    def _select_music_mood(self) -> str:
        """Select music mood based on restaurant soul."""
        sounds = self.soul.signature_sounds
        
        if "tabla" in str(sounds).lower() or "classical" in str(sounds).lower():
            return "indian_classical"
        elif "sitar" in str(sounds).lower():
            return "sitar_ambient"
        else:
            return "warm_ambient"
    
    def optimize_for_mobile(
        self,
        reel: NarrativeReel,
        max_duration: float = 30.0
    ) -> NarrativeReel:
        """
        Optimize reel for mobile viewing (Instagram Reels).
        
        - Ensure vertical 9:16 format
        - Front-load the hook (first 3 seconds are everything)
        - Keep text minimal (no subtitles)
        - Ensure visual clarity on small screens
        """
        # Trim if over duration
        while reel.total_duration > max_duration and len(reel.acts) > 3:
            # Remove lowest priority act (usually filler or CTA can be shorter)
            removable = [a for a in reel.acts if a.act_name not in ["hook", "payoff"]]
            if removable:
                to_remove = min(removable, key=lambda a: a.mapped_scene.priority_score)
                reel.acts.remove(to_remove)
                reel.total_duration = sum(a.duration for a in reel.acts)
            else:
                break
        
        # Ensure hook is strong
        if reel.acts and reel.acts[0].act_name == "hook":
            hook = reel.acts[0]
            if hook.duration < 2.5:
                hook.duration = 2.5  # Minimum hook duration
        
        return reel
