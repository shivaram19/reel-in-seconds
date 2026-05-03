import json
import os
from typing import List, Dict, Optional

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "restaurants.json")

def _ensure_data_dir():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)

def load_restaurants() -> List[Dict]:
    _ensure_data_dir()
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_restaurants(restaurants: List[Dict]):
    _ensure_data_dir()
    with open(DATA_FILE, "w") as f:
        json.dump(restaurants, f, indent=2)

def _sanitize_color(color):
    """Ensure color is always a valid hex string. Handles tuples/lists/strings/None."""
    if isinstance(color, (tuple, list)) and len(color) >= 3:
        return "#{:02x}{:02x}{:02x}".format(int(color[0]), int(color[1]), int(color[2]))
    if isinstance(color, str):
        color = color.strip()
        if color.startswith("#") and len(color) == 7:
            return color
        if len(color) == 6:
            return "#" + color
    return "#FF6B35"


def add_restaurant(name: str, cuisine: str, location: str, tagline: str,
                   color1: str, color2: str, phone: str = "", instagram: str = "", logo: str = "") -> Dict:
    restaurants = load_restaurants()
    next_id = max((r["id"] for r in restaurants), default=0) + 1
    restaurant = {
        "id": next_id,
        "name": name,
        "cuisine": cuisine,
        "location": location,
        "tagline": tagline,
        "color1": _sanitize_color(color1),
        "color2": _sanitize_color(color2),
        "phone": phone,
        "instagram": instagram,
        "logo": logo
    }
    restaurants.append(restaurant)
    save_restaurants(restaurants)
    return restaurant

def get_restaurant(rid: int) -> Optional[Dict]:
    for r in load_restaurants():
        if r["id"] == rid:
            return r
    return None

def delete_restaurant(rid: int):
    restaurants = [r for r in load_restaurants() if r["id"] != rid]
    save_restaurants(restaurants)
