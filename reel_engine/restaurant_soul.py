"""
Restaurant Soul Engine
======================

Captures the essence of a restaurant — its identity, intention, audience,
and the visual language that communicates its soul.

This is the "owner's perspective" — what the restaurant wants to say.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import json
import os


@dataclass
class RestaurantSoul:
    """
    Deep profile of a restaurant's identity and visual language.
    
    This object represents the restaurant owner's perspective:
    - What is our story?
    - Who are we cooking for?
    - What emotions do we want to evoke?
    - What visual objects define us?
    """
    
    # Identity
    name: str
    location: str
    cuisine_primary: str
    cuisine_secondary: List[str]
    tagline: str
    vibe_description: str
    
    # Audience
    primary_audience: str
    secondary_audience: str
    audience_age_range: Tuple[int, int]
    audience_motivations: List[str]
    
    # Owner's Intention (the "soul")
    owner_intention: str
    core_message: str
    emotional_promise: str
    
    # Signature Elements
    signature_dishes: List[str]
    signature_objects: List[str]  # Visual objects that define this restaurant
    signature_colors: List[str]  # Hex colors
    signature_sounds: List[str]  # Audio mood descriptors
    
    # Domain Taxonomy — Object Relevance Scoring
    # Format: {object_name: relevance_score_0_to_1}
    object_relevance: Dict[str, float] = field(default_factory=dict)
    
    # Scene Type Preferences
    # Which scene types matter most for this restaurant's story
    scene_weights: Dict[str, float] = field(default_factory=dict)
    
    # Narrative Arc Preferences
    # How the story should flow for this specific restaurant
    narrative_arc: Dict[str, any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "location": self.location,
            "cuisine_primary": self.cuisine_primary,
            "cuisine_secondary": self.cuisine_secondary,
            "tagline": self.tagline,
            "vibe_description": self.vibe_description,
            "primary_audience": self.primary_audience,
            "secondary_audience": self.secondary_audience,
            "audience_age_range": self.audience_age_range,
            "audience_motivations": self.audience_motivations,
            "owner_intention": self.owner_intention,
            "core_message": self.core_message,
            "emotional_promise": self.emotional_promise,
            "signature_dishes": self.signature_dishes,
            "signature_objects": self.signature_objects,
            "signature_colors": self.signature_colors,
            "signature_sounds": self.signature_sounds,
            "object_relevance": self.object_relevance,
            "scene_weights": self.scene_weights,
            "narrative_arc": self.narrative_arc,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "RestaurantSoul":
        return cls(**data)
    
    def save(self, path: str):
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: str) -> "RestaurantSoul":
        with open(path, 'r') as f:
            return cls.from_dict(json.load(f))


def get_pakwaan_soul() -> RestaurantSoul:
    """
    The Pakwaan, Almaty — Restaurant Soul Profile
    
    Built from:
    - Website: thepakwaan.com (menu, keywords, vibe)
    - TripAdvisor reviews (customer sentiment)
    - Location context (GVK Medical College, Almaty)
    - Cuisine research (Rajasthani, South Indian, Gujarati, Jain)
    """
    
    return RestaurantSoul(
        # === IDENTITY ===
        name="The Pakwaan",
        location="Almaty, Kazakhstan",
        cuisine_primary="Indian",
        cuisine_secondary=[
            "Rajasthani",
            "South Indian", 
            "Gujarati",
            "Jain",
            "Pure Vegetarian"
        ],
        tagline="A Taste of India in Almaty",
        vibe_description=(
            "Warm, authentic Indian vegetarian dining. The atmosphere feels like India "
            "— rich spice aromas, traditional decor, copper vessels, and the comfort of "
            "home-style cooking. A sanctuary for homesick students and curious locals alike."
        ),
        
        # === AUDIENCE ===
        primary_audience=(
            "Indian medical students at GVK Medical College, Almaty — "
            "homesick, craving authentic vegetarian food, missing home flavors"
        ),
        secondary_audience=(
            "Local Kazakh residents and international students in Almaty "
            "curious about Indian cuisine, vegetarians seeking pure veg options"
        ),
        audience_age_range=(18, 35),
        audience_motivations=[
            "Craving authentic Indian home food",
            "Seeking pure vegetarian/Jain options in Almaty",
            "Missing family meals and traditional flavors",
            "Looking for affordable, hearty student meals",
            "Wanting to share cultural food experience with friends",
        ],
        
        # === OWNER'S INTENTION (THE SOUL) ===
        owner_intention=(
            "To bring a piece of India to Almaty. Every dish is cooked with the same "
            "love and tradition as back home. We want students to walk in and feel "
            "like they've stepped into their grandmother's kitchen — the warmth, the "
            "aromas, the familiar faces. We preserve Rajasthani and South Indian "
            "culinary heritage because our customers deserve authenticity, not compromise."
        ),
        core_message=(
            "At The Pakwaan, you're not just eating — you're coming home. "
            "Authentic Indian vegetarian cuisine, made with tradition, served with love."
        ),
        emotional_promise=(
            "Comfort, nostalgia, belonging. The feeling of a warm thali on a cold Almaty day. "
            "The joy of sharing biryani with friends who feel like family. The pride of "
            "introducing Kazakh friends to the richness of Indian vegetarian cuisine."
        ),
        
        # === SIGNATURE ELEMENTS ===
        signature_dishes=[
            "Veg Biryani",
            "Rajasthani Gatta Biryani",
            "Paneer Biryani",
            "Rajasthani Thali",
            "Daal Baati Churma",
            "Idli Sambhar",
            "Medu Vada",
            "Masala Dosa",
            "Palak Paneer",
            "Kadhai Paneer",
            "Shahi Paneer",
            "Gulab Jamun",
            "Jalebi",
            "Ghevar",
            "Mohan Thal",
        ],
        signature_objects=[
            "copper handi",
            "clay pot",
            "biryani pot",
            "tawa griddle",
            "dosa griddle",
            "thali plate",
            "brass vessel",
            "wooden spatula",
            "rolling pin",
            "naan bread",
            "chapati",
            "paneer cubes",
            "steam rising",
            "ghee being poured",
            "masala dabba",
            "tandoor oven",
        ],
        signature_colors=[
            "#D4A574",  # Warm copper
            "#8B4513",  # Saddle brown (earth)
            "#FFD700",  # Gold (saffron)
            "#DC143C",  # Crimson (deep red)
            "#FF8C00",  # Dark orange (turmeric)
            "#228B22",  # Forest green (coriander/mint)
            "#F5F5DC",  # Beige (cream/curd)
        ],
        signature_sounds=[
            "gentle classical sitar",
            "soft tabla rhythm",
            "sizzling tawa",
            "gentle chatter of students",
            "warm ambient noise",
        ],
        
        # === DOMAIN TAXONOMY — Object Relevance ===
        # YOLO COCO class names mapped to relevance for The Pakwaan
        object_relevance={
            # TIER 1: Core Food & Cooking (highest relevance)
            "bowl": 1.0,
            "cup": 0.9,
            "spoon": 0.95,
            "fork": 0.7,
            "knife": 0.7,
            "bottle": 0.6,
            "wine glass": 0.4,
            "pizza": 0.5,  # Not core but food
            "sandwich": 0.5,
            "cake": 0.8,  # Indian sweets
            "donut": 0.5,
            "hot dog": 0.2,
            "person": 0.9,  # Chef, server, customer
            
            # TIER 2: Restaurant Environment (high relevance)
            "dining table": 0.85,
            "chair": 0.6,
            "couch": 0.5,
            "potted plant": 0.4,
            "oven": 0.9,  # Tandoor
            "microwave": 0.5,
            "refrigerator": 0.4,
            "sink": 0.5,
            "book": 0.6,  # Menu
            "clock": 0.2,
            "vase": 0.5,
            
            # TIER 3: Ambiance (medium relevance)
            "tv": 0.2,
            "laptop": 0.1,
            "cell phone": 0.15,
            "remote": 0.05,
            "umbrella": 0.3,
            "dog": 0.2,
            "cat": 0.2,
            
            # TIER 4: Distractors (low/negative)
            "car": 0.05,
            "truck": 0.0,
            "bus": 0.0,
            "bicycle": 0.1,
            "motorcycle": 0.05,
            "traffic light": 0.0,
            "stop sign": 0.0,
            "parking meter": 0.0,
            "backpack": 0.1,
            "handbag": 0.1,
        },
        
        # === SCENE TYPE WEIGHTS ===
        scene_weights={
            "cooking": 1.0,
            "plating": 0.95,
            "food_closeup": 1.0,
            "dining": 0.8,
            "atmosphere": 0.6,
            "kitchen_prep": 0.85,
            "serving": 0.9,
            "exterior": 0.2,
            "menu": 0.5,
            "ingredients": 0.75,
        },
        
        # === NARRATIVE ARC PREFERENCES ===
        narrative_arc={
            "preferred_duration": 30,  # seconds
            "hook_style": "food_reveal",  # Start with the most tempting shot
            "promise_style": "process_tease",  # Show hands working dough or spices
            "process_style": "cooking_sequence",  # Fire, steam, sizzle
            "payoff_style": "plating_money_shot",  # The final dish, glistening
            "social_style": "dining_joy",  # Students laughing, sharing
            "cta_style": "location_invite",  # "Come home to The Pakwaan"
            "pacing": "moderate",  # Not too fast (heritage), not too slow
            "color_temperature": "warm",  # Always warm for Indian food
            "transition_style": "soft_fade",  # Gentle, not jarring
        },
    )


def get_default_soul() -> RestaurantSoul:
    """Generic restaurant soul for fallback."""
    return RestaurantSoul(
        name="Restaurant",
        location="",
        cuisine_primary="",
        cuisine_secondary=[],
        tagline="",
        vibe_description="",
        primary_audience="",
        secondary_audience="",
        audience_age_range=(18, 65),
        audience_motivations=[],
        owner_intention="",
        core_message="",
        emotional_promise="",
        signature_dishes=[],
        signature_objects=[],
        signature_colors=["#FF6B35"],
        signature_sounds=[],
        object_relevance={},
        scene_weights={
            "cooking": 1.0,
            "plating": 0.9,
            "food_closeup": 1.0,
            "dining": 0.7,
            "atmosphere": 0.5,
            "kitchen_prep": 0.8,
            "serving": 0.85,
            "exterior": 0.3,
        },
        narrative_arc={
            "preferred_duration": 30,
            "hook_style": "food_reveal",
            "pacing": "moderate",
            "color_temperature": "warm",
            "transition_style": "soft_fade",
        },
    )


# Registry of known restaurant souls
SOUL_REGISTRY = {
    "pakwaan": get_pakwaan_soul,
    "default": get_default_soul,
}


def get_soul(restaurant_id: str = "pakwaan") -> RestaurantSoul:
    """Get a restaurant soul by ID."""
    if restaurant_id.lower() in SOUL_REGISTRY:
        return SOUL_REGISTRY[restaurant_id.lower()]()
    return get_default_soul()
