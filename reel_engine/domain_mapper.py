"""
Domain Relevance Mapper
=======================

Maps detected objects and scene types to restaurant domain relevance.
This is the "brain" that decides what matters for THIS specific restaurant.

Input: Scene segments with detected objects and scene types
Output: Scene segments with domain_relevance scores and narrative role assignments

The mapping is deeply personal to the restaurant's soul:
- A biryani pot is sacred for The Pakwaan
- A pizza is irrelevant
- A student eating = the whole point of the restaurant
"""

import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass

from .restaurant_soul import RestaurantSoul
from .frame_analyzer import SceneSegment, FrameAnalysis

logger = logging.getLogger(__name__)


@dataclass
class MappedScene:
    """A scene enriched with domain relevance and narrative role."""
    scene: SceneSegment
    domain_relevance: float  # 0-1, how relevant to this restaurant
    narrative_role: str  # hook, promise, process, payoff, social, cta, filler
    emotional_tone: str  # tempting, satisfying, energetic, warm, inviting
    priority_score: float  # Combined score for sequencing
    recommended_duration: float  # seconds
    recommended_transition: str  # cut, fade, zoom, etc.
    why_included: str  # Human-readable explanation


class DomainMapper:
    """
    Maps analyzed scenes to restaurant-specific relevance.
    
    This is where the restaurant's soul meets the raw footage.
    The same clip of a bowl could be:
    - High relevance for a soup restaurant
    - Medium relevance for a bakery  
    - Low relevance for a steakhouse
    """
    
    def __init__(self, soul: RestaurantSoul):
        self.soul = soul
        
        # Build quick lookup from object relevance
        self.object_relevance = soul.object_relevance
        
        # Scene type weights
        self.scene_weights = soul.scene_weights
        
        logger.info(
            f"[DomainMapper] Initialized for '{soul.name}' "
            f"with {len(self.object_relevance)} object mappings"
        )
    
    def map_scenes(self, scenes: List[SceneSegment]) -> List[MappedScene]:
        """
        Map all scenes to domain relevance and narrative roles.
        
        Returns scenes sorted by priority (best scenes first).
        Also distributes scenes across narrative roles to ensure
        all 6 acts can be filled, and ensures clip diversity.
        """
        mapped = []
        
        for scene in scenes:
            mapped_scene = self._map_single_scene(scene)
            mapped.append(mapped_scene)
        
        # Sort by priority score (descending)
        mapped.sort(key=lambda s: s.priority_score, reverse=True)
        
        # Distribute roles so all 6 acts can be filled
        mapped = self._distribute_roles(mapped)
        
        # Re-sort after role distribution
        mapped.sort(key=lambda s: s.priority_score, reverse=True)
        
        top_rel = round(mapped[0].domain_relevance, 2) if mapped else 0
        top_role = mapped[0].narrative_role if mapped else 'none'
        clips_used = len(set(s.scene.source_clip for s in mapped))
        logger.info(
            f"[DomainMapper] Mapped {len(mapped)} scenes from {clips_used} clips. "
            f"Top relevance: {top_rel} ({top_role})"
        )
        
        return mapped
    
    def _distribute_roles(self, mapped_scenes: List[MappedScene]) -> List[MappedScene]:
        """
        Ensure scenes are distributed across narrative roles.
        
        Problem: If all 8 clips produce the same scene type, they all get the same role.
        Then the selector only picks 1 scene and discards the rest.
        
        Fix: Reassign scenes to missing required roles, ensuring clip diversity.
        """
        required_roles = ["hook", "promise", "process", "payoff", "social", "cta"]
        
        # Group by current role
        by_role: Dict[str, List[MappedScene]] = {}
        for ms in mapped_scenes:
            role = ms.narrative_role
            if role not in by_role:
                by_role[role] = []
            by_role[role].append(ms)
        
        # Find missing required roles
        missing_roles = [r for r in required_roles if r not in by_role or not by_role[r]]
        
        if not missing_roles:
            return mapped_scenes
        
        # Collect excess scenes (from ANY role, including filler)
        excess_candidates = []
        for role, scenes in by_role.items():
            if len(scenes) > 1:
                # Sort by priority, keep the best, rest can be reassigned
                scenes.sort(key=lambda s: s.priority_score, reverse=True)
                for excess in scenes[1:]:
                    excess_candidates.append((role, excess))
            elif role == "filler":
                # All filler scenes are candidates for reassignment
                for s in scenes:
                    excess_candidates.append((role, s))
        
        # Sort by priority (best first)
        excess_candidates.sort(key=lambda x: x[1].priority_score, reverse=True)
        
        # Track which clips we've used for reassignment
        reassigned_clips = set()
        
        for role, excess in excess_candidates:
            if not missing_roles:
                break
            
            # Skip if we already reassigned a scene from this clip
            if excess.scene.source_clip in reassigned_clips:
                continue
            
            target_role = missing_roles.pop(0)
            
            # Update the scene's role
            excess.narrative_role = target_role
            excess.emotional_tone = self._determine_emotional_tone(excess.scene, target_role)
            excess.recommended_duration = self._recommend_duration(target_role, excess.scene)
            excess.recommended_transition = self._recommend_transition(target_role)
            excess.why_included = self._generate_explanation(excess.scene, target_role, excess.domain_relevance)
            excess.priority_score = self._compute_priority_score(
                excess.domain_relevance, excess.scene.quality_score, target_role
            )
            
            reassigned_clips.add(excess.scene.source_clip)
            logger.info(
                f"[DomainMapper] Reassigned scene from '{role}' to '{target_role}' "
                f"(clip: {excess.scene.source_clip})"
            )
        
        return mapped_scenes
    
    def _map_single_scene(self, scene: SceneSegment) -> MappedScene:
        """Map a single scene to domain relevance and narrative role."""
        
        # 1. Compute object-based relevance
        obj_relevance = self._compute_object_relevance(scene)
        
        # 2. Compute scene-type relevance
        scene_type_relevance = self.scene_weights.get(scene.scene_type, 0.3)
        
        # 3. Combine for domain relevance
        domain_relevance = (
            obj_relevance * 0.6 +
            scene_type_relevance * 0.3 +
            scene.quality_score * 0.1
        )
        domain_relevance = round(min(1.0, max(0.0, domain_relevance)), 3)
        
        # 4. Assign narrative role
        narrative_role = self._assign_narrative_role(scene, domain_relevance)
        
        # 5. Determine emotional tone
        emotional_tone = self._determine_emotional_tone(scene, narrative_role)
        
        # 6. Compute priority score (for sequencing)
        priority_score = self._compute_priority_score(
            domain_relevance, scene.quality_score, narrative_role
        )
        
        # 7. Determine recommended duration and transition
        recommended_duration = self._recommend_duration(narrative_role, scene)
        recommended_transition = self._recommend_transition(narrative_role)
        
        # 8. Generate human-readable explanation
        why_included = self._generate_explanation(scene, narrative_role, obj_relevance)
        
        return MappedScene(
            scene=scene,
            domain_relevance=domain_relevance,
            narrative_role=narrative_role,
            emotional_tone=emotional_tone,
            priority_score=priority_score,
            recommended_duration=recommended_duration,
            recommended_transition=recommended_transition,
            why_included=why_included,
        )
    
    def _compute_object_relevance(self, scene: SceneSegment) -> float:
        """
        Compute object-based relevance score.
        
        For each detected object, look up its relevance to this restaurant.
        Weight by confidence and area (larger objects = more important).
        """
        if not scene.dominant_objects:
            return 0.2  # Default low relevance if no objects detected
        
        total_score = 0.0
        total_weight = 0.0
        
        for obj_name, confidence in scene.dominant_objects.items():
            # Get relevance for this object (default 0.3 if unknown)
            relevance = self.object_relevance.get(obj_name, 0.3)
            
            # Weight by confidence
            weight = confidence
            
            total_score += relevance * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.2
        
        avg_relevance = total_score / total_weight
        return round(avg_relevance, 3)
    
    def _assign_narrative_role(
        self,
        scene: SceneSegment,
        domain_relevance: float
    ) -> str:
        """
        Assign a narrative role to this scene.
        
        The 6-act structure:
        - hook: The scroll-stopper (most tempting shot)
        - promise: What you're about to see (teaser)
        - process: The making (cooking, preparation)
        - payoff: The final dish (money shot)
        - social: People enjoying (dining, sharing)
        - cta: Call to action (location, contact)
        
        Plus:
        - filler: Low relevance, use only if needed
        """
        scene_type = scene.scene_type
        
        # High domain relevance scenes get primary roles
        if domain_relevance >= 0.8:
            if scene_type == "food_closeup":
                return "payoff"
            elif scene_type == "cooking":
                return "process"
            elif scene_type == "plating":
                return "promise"
            elif scene_type == "dining":
                return "social"
            elif scene_type == "serving":
                return "social"
        
        # Medium-high relevance
        if domain_relevance >= 0.5:
            if scene_type == "food_closeup":
                return "hook"
            elif scene_type == "cooking":
                return "process"
            elif scene_type == "plating":
                return "promise"
            elif scene_type == "dining":
                return "social"
            elif scene_type == "serving":
                return "social"
            elif scene_type == "kitchen_prep":
                return "process"
            elif scene_type == "atmosphere":
                return "cta"  # Show ambiance for CTA
        
        # Low relevance
        if domain_relevance < 0.3:
            return "filler"
        
        # Default based on scene type
        role_map = {
            "cooking": "process",
            "plating": "promise",
            "food_closeup": "payoff",
            "dining": "social",
            "serving": "social",
            "kitchen_prep": "process",
            "atmosphere": "cta",
            "exterior": "cta",
            "unknown": "filler",
        }
        
        return role_map.get(scene_type, "filler")
    
    def _determine_emotional_tone(
        self,
        scene: SceneSegment,
        narrative_role: str
    ) -> str:
        """Determine the emotional tone of a scene."""
        tone_map = {
            "hook": "tempting",
            "promise": "intriguing",
            "process": "satisfying",
            "payoff": "mouthwatering",
            "social": "warm",
            "cta": "inviting",
            "filler": "neutral",
        }
        
        base_tone = tone_map.get(narrative_role, "neutral")
        
        # Adjust based on scene type
        if scene.scene_type == "cooking" and scene.quality_score > 0.7:
            base_tone = "energetic"
        elif scene.scene_type == "food_closeup" and scene.quality_score > 0.8:
            base_tone = "mouthwatering"
        elif scene.scene_type == "dining":
            base_tone = "warm"
        
        return base_tone
    
    def _compute_priority_score(
        self,
        domain_relevance: float,
        quality_score: float,
        narrative_role: str
    ) -> float:
        """
        Compute priority score for sequencing.
        
        Higher priority = use this scene, and use it prominently.
        """
        # Narrative role weights (some roles are more important)
        role_weights = {
            "hook": 1.5,
            "payoff": 1.4,
            "process": 1.2,
            "promise": 1.1,
            "social": 1.0,
            "cta": 0.8,
            "filler": 0.3,
        }
        
        role_weight = role_weights.get(narrative_role, 0.5)
        
        # Combine: domain relevance matters most, then quality, then role
        priority = (
            domain_relevance * 0.5 +
            quality_score * 0.3 +
            role_weight * 0.2
        )
        
        return round(priority, 3)
    
    def _recommend_duration(
        self,
        narrative_role: str,
        scene: SceneSegment
    ) -> float:
        """Recommend duration in seconds for this scene."""
        # Base duration by role
        duration_map = {
            "hook": 3.0,
            "promise": 2.0,
            "process": 4.0,
            "payoff": 3.0,
            "social": 3.0,
            "cta": 2.5,
            "filler": 1.5,
        }
        
        base = duration_map.get(narrative_role, 2.0)
        
        # Adjust by scene quality
        if scene.quality_score > 0.8:
            base *= 1.2  # Great scene deserves more time
        elif scene.quality_score < 0.4:
            base *= 0.7  # Poor scene gets less time
        
        # Cap at reasonable limits
        return round(min(base, 6.0), 1)
    
    def _recommend_transition(self, narrative_role: str) -> str:
        """Recommend transition type for this scene."""
        transition_map = {
            "hook": "cut",  # Immediate impact
            "promise": "fade",  # Smooth anticipation
            "process": "cut",  # Keep energy
            "payoff": "fade",  # Let the beauty sink in
            "social": "cut",  # Natural flow
            "cta": "fade",  # Gentle landing
            "filler": "cut",  # Quick, don't linger
        }
        
        return transition_map.get(narrative_role, "cut")
    
    def _generate_explanation(
        self,
        scene: SceneSegment,
        narrative_role: str,
        obj_relevance: float
    ) -> str:
        """Generate human-readable explanation for why this scene is included."""
        obj_list = ", ".join(
            f"{name}({conf:.0%})"
            for name, conf in list(scene.dominant_objects.items())[:3]
        )
        
        explanations = {
            "hook": f"This {scene.scene_type} scene with {obj_list} will stop the scroll. It's the first taste of what The Pakwaan offers.",
            "promise": f"Showing {scene.scene_type} with {obj_list} builds anticipation — the viewer wants to see the final dish.",
            "process": f"The {scene.scene_type} footage with {obj_list} shows the craft and care behind every dish.",
            "payoff": f"This beautiful {scene.scene_type} shot with {obj_list} is the money shot — the reason people visit The Pakwaan.",
            "social": f"The {scene.scene_type} scene with {obj_list} shows community and joy — students sharing a meal away from home.",
            "cta": f"This {scene.scene_type} scene with {obj_list} invites viewers to visit The Pakwaan in Almaty.",
            "filler": f"This {scene.scene_type} scene provides transition space. Can be trimmed if reel is too long.",
        }
        
        return explanations.get(narrative_role, f"Scene type: {scene.scene_type}")
    
    def select_best_scenes_for_reel(
        self,
        mapped_scenes: List[MappedScene],
        target_duration: float = 30.0,
        min_scenes: int = 4,
        max_scenes: int = 8
    ) -> List[MappedScene]:
        """
        Select the best subset of scenes to fit target duration.
        
        Ensures:
        - At least one scene per narrative role (if available)
        - Total duration close to target
        - No filler scenes unless necessary
        """
        # First, ensure we have scenes for key roles
        required_roles = ["hook", "process", "payoff", "social", "cta"]
        selected = []
        used_roles = set()
        
        # Sort by priority
        sorted_scenes = sorted(mapped_scenes, key=lambda s: s.priority_score, reverse=True)
        
        # Pick one scene per required role
        for role in required_roles:
            for scene in sorted_scenes:
                if scene.narrative_role == role and scene not in selected:
                    selected.append(scene)
                    used_roles.add(role)
                    break
        
        # Fill remaining slots with highest priority scenes
        current_duration = sum(s.recommended_duration for s in selected)
        
        for scene in sorted_scenes:
            if scene in selected:
                continue
            if len(selected) >= max_scenes:
                break
            if current_duration + scene.recommended_duration > target_duration * 1.2:
                break
            
            # Skip filler unless we need more scenes
            if scene.narrative_role == "filler" and len(selected) >= min_scenes:
                continue
            
            selected.append(scene)
            current_duration += scene.recommended_duration
        
        # Sort selected scenes by narrative order (not priority)
        role_order = {"hook": 0, "promise": 1, "process": 2, "payoff": 3, "social": 4, "cta": 5, "filler": 6}
        selected.sort(key=lambda s: role_order.get(s.narrative_role, 99))
        
        logger.info(
            f"[DomainMapper] Selected {len(selected)} scenes for {current_duration:.1f}s reel. "
            f"Roles: {[s.narrative_role for s in selected]}"
        )
        
        return selected
