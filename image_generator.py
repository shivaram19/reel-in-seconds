"""
Instagram Content Generator for Restaurants.
Generates branded story (1080x1920) and post (1080x1080) images.
"""

import os
import uuid
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import Dict, Tuple

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static", "generated")
os.makedirs(STATIC_DIR, exist_ok=True)
LOGOS_DIR = os.path.join(os.path.dirname(__file__), "static", "logos")

# Try to load nice fonts, fall back to defaults
def _get_font(size: int, bold: bool = False):
    """Load a system font with fallback."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                pass
    return ImageFont.load_default()


def _hex_to_rgb(color) -> Tuple[int, int, int]:
    """Convert hex string or RGB tuple/list to RGB tuple. Defensive against bad data."""
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"[_hex_to_rgb] INPUT type={type(color).__name__} value={color!r}")
    
    # Already a tuple/list of 3 integers — return as-is
    if isinstance(color, (tuple, list)) and len(color) >= 3:
        result = tuple(int(c) for c in color[:3])
        logger.debug(f"[_hex_to_rgb] Detected tuple/list, returning {result}")
        return result
    # String hex color like "#FF6B35" or "FF6B35"
    if isinstance(color, str):
        color = color.lstrip("#")
        if len(color) == 6:
            result = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            logger.debug(f"[_hex_to_rgb] Parsed hex string, returning {result}")
            return result
    # Fallback to a safe orange
    logger.warning(f"[_hex_to_rgb] UNEXPECTED INPUT type={type(color).__name__} value={color!r} — falling back to orange")
    return (255, 107, 53)


def _lighten(color: Tuple[int, int, int], factor: float = 1.3) -> Tuple[int, int, int]:
    return tuple(min(255, int(c * factor)) for c in color)


def _darken(color: Tuple[int, int, int], factor: float = 0.7) -> Tuple[int, int, int]:
    return tuple(max(0, int(c * factor)) for c in color)


def _draw_gradient(draw, width: int, height: int, color1: Tuple[int, int, int], color2: Tuple[int, int, int], vertical: bool = True):
    """Draw a smooth gradient between two colors."""
    for i in range(height if vertical else width):
        ratio = i / (height if vertical else width)
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        if vertical:
            draw.line([(0, i), (width, i)], fill=(r, g, b))
        else:
            draw.line([(i, 0), (i, height)], fill=(r, g, b))


def _wrap_text(draw, text: str, font, max_width: int) -> list:
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines if lines else [text]


def _add_noise_overlay(image: Image.Image, intensity: int = 15) -> Image.Image:
    """Add subtle texture to make it look more organic."""
    import random
    overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
    pixels = overlay.load()
    for i in range(0, image.width, 2):
        for j in range(0, image.height, 2):
            if random.random() > 0.7:
                val = random.randint(255 - intensity, 255)
                pixels[i, j] = (val, val, val, 8)
    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def _overlay_logo(img: Image.Image, restaurant: Dict, position: str = "top-right", max_size: int = 120) -> Image.Image:
    """Overlay restaurant logo on the generated image."""
    logo_path = restaurant.get("logo", "")
    if not logo_path:
        return img
    
    # Convert relative URL to filesystem path
    if logo_path.startswith("/static/"):
        logo_path = logo_path.replace("/static/", "", 1)
    logo_full_path = os.path.join(os.path.dirname(__file__), "static", logo_path)
    
    if not os.path.exists(logo_full_path):
        return img
    
    try:
        logo = Image.open(logo_full_path).convert("RGBA")
        
        # Calculate new size maintaining aspect ratio
        ratio = min(max_size / logo.width, max_size / logo.height)
        new_width = int(logo.width * ratio)
        new_height = int(logo.height * ratio)
        logo = logo.resize((new_width, new_height), Image.LANCZOS)
        
        # Add subtle white background circle behind logo for visibility
        padding = 8
        bg_size = (new_width + padding * 2, new_height + padding * 2)
        bg = Image.new("RGBA", bg_size, (255, 255, 255, 180))
        bg.paste(logo, (padding, padding), logo)
        
        # Position the logo
        margin = 40
        if position == "top-right":
            x = img.width - bg.width - margin
            y = margin
        elif position == "top-left":
            x = margin
            y = margin
        elif position == "bottom-right":
            x = img.width - bg.width - margin
            y = img.height - bg.height - margin
        else:  # bottom-left
            x = margin
            y = img.height - bg.height - margin
        
        # Composite logo onto image
        img = img.convert("RGBA")
        img.paste(bg, (x, y), bg)
        return img.convert("RGB")
    except Exception:
        # If logo processing fails, return original image
        return img


def generate_story(restaurant: Dict, context: str, event: str, offer: str = "") -> str:
    """Generate an Instagram Story (1080x1920)."""
    width, height = 1080, 1920
    c1 = _hex_to_rgb(restaurant.get("color1", "#FF6B35"))
    c2 = _hex_to_rgb(restaurant.get("color2", "#F7931E"))

    img = Image.new("RGB", (width, height), c1)
    draw = ImageDraw.Draw(img)

    # Background gradient
    _draw_gradient(draw, width, height, c1, c2, vertical=True)

    # Add decorative top arc
    draw.pieslice([(-200, -400), (1280, 600)], 0, 180, fill=_lighten(c1, 1.15))

    # Add decorative bottom wave-like shape
    draw.pieslice([(-100, 1400), (1180, 2200)], 180, 360, fill=_darken(c2, 0.85))

    # Fonts
    font_title = _get_font(90, bold=True)
    font_event = _get_font(70, bold=True)
    font_context = _get_font(48)
    font_offer = _get_font(56, bold=True)
    font_small = _get_font(36)
    font_tagline = _get_font(40)

    # Margins
    margin = 80
    text_width = width - 2 * margin

    # Restaurant name at top
    y_pos = 180
    name = restaurant["name"].upper()
    draw.text((width // 2, y_pos), name, font=font_title, fill=(255, 255, 255),
              anchor="mm", stroke_width=2, stroke_fill=_darken(c1, 0.5))

    # Tagline
    y_pos += 100
    if restaurant.get("tagline"):
        draw.text((width // 2, y_pos), restaurant["tagline"], font=font_tagline,
                  fill=(255, 255, 255), anchor="mm")

    # Separator line
    y_pos += 80
    draw.line([(margin + 100, y_pos), (width - margin - 100, y_pos)],
              fill=(255, 255, 255), width=3)

    # Event / Headline
    y_pos += 120
    event_lines = _wrap_text(draw, event.upper(), font_event, text_width)
    for line in event_lines:
        draw.text((width // 2, y_pos), line, font=font_event, fill=(255, 255, 255),
                  anchor="mm", stroke_width=2, stroke_fill=_darken(c2, 0.4))
        y_pos += 90

    # Context / Body
    y_pos += 40
    context_lines = _wrap_text(draw, context, font_context, text_width)
    for line in context_lines[:8]:  # limit lines
        draw.text((width // 2, y_pos), line, font=font_context, fill=(255, 255, 255),
                  anchor="mm")
        y_pos += 65

    # Offer highlight box
    if offer:
        y_pos += 60
        offer_text = f"🎉 {offer.upper()}"
        bbox = draw.textbbox((0, 0), offer_text, font=font_offer)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        box_pad = 40
        box_coords = [
            (width - tw) // 2 - box_pad,
            y_pos - th // 2 - box_pad // 2,
            (width + tw) // 2 + box_pad,
            y_pos + th // 2 + box_pad // 2
        ]
        draw.rounded_rectangle(box_coords, radius=20, fill=(255, 255, 255),
                                outline=(255, 255, 255), width=4)
        draw.text((width // 2, y_pos), offer_text, font=font_offer,
                  fill=c2, anchor="mm")
        y_pos += 120

    # Footer info
    y_pos = height - 180
    draw.text((width // 2, y_pos), f"📍 {restaurant.get('location', '')}",
              font=font_small, fill=(255, 255, 255), anchor="mm")
    y_pos += 55
    if restaurant.get("phone"):
        draw.text((width // 2, y_pos), f"📞 {restaurant['phone']}",
                  font=font_small, fill=(255, 255, 255), anchor="mm")
    y_pos += 55
    if restaurant.get("instagram"):
        draw.text((width // 2, y_pos), f"@{restaurant['instagram']}",
                  font=font_small, fill=(255, 255, 255), anchor="mm")

    # Subtle noise overlay for organic feel
    img = _add_noise_overlay(img, intensity=12)
    
    # Overlay logo
    img = _overlay_logo(img, restaurant, position="top-right", max_size=140)

    filename = f"story_{restaurant['id']}_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(STATIC_DIR, filename)
    img.save(filepath, "PNG", quality=95)
    return filename


def generate_post(restaurant: Dict, context: str, event: str, offer: str = "") -> str:
    """Generate an Instagram Post (1080x1080 square)."""
    width, height = 1080, 1080
    c1 = _hex_to_rgb(restaurant.get("color1", "#FF6B35"))
    c2 = _hex_to_rgb(restaurant.get("color2", "#F7931E"))

    img = Image.new("RGB", (width, height), c1)
    draw = ImageDraw.Draw(img)

    # Diagonal gradient effect
    _draw_gradient(draw, width, height, c1, c2, vertical=False)

    # Decorative circles
    draw.ellipse([(-150, -150), (350, 350)], fill=_lighten(c1, 1.1))
    draw.ellipse([(700, 600), (1200, 1100)], fill=_darken(c2, 0.8))

    # Fonts
    font_title = _get_font(80, bold=True)
    font_event = _get_font(60, bold=True)
    font_context = _get_font(42)
    font_offer = _get_font(50, bold=True)
    font_small = _get_font(32)
    font_tagline = _get_font(36)

    margin = 80
    text_width = width - 2 * margin

    # Restaurant name
    y_pos = 160
    name = restaurant["name"].upper()
    draw.text((width // 2, y_pos), name, font=font_title, fill=(255, 255, 255),
              anchor="mm", stroke_width=2, stroke_fill=_darken(c1, 0.5))

    # Tagline
    y_pos += 90
    if restaurant.get("tagline"):
        draw.text((width // 2, y_pos), restaurant["tagline"], font=font_tagline,
                  fill=(255, 255, 255), anchor="mm")

    # Separator
    y_pos += 70
    draw.line([(margin + 150, y_pos), (width - margin - 150, y_pos)],
              fill=(255, 255, 255), width=3)

    # Event headline
    y_pos += 100
    event_lines = _wrap_text(draw, event.upper(), font_event, text_width)
    for line in event_lines:
        draw.text((width // 2, y_pos), line, font=font_event, fill=(255, 255, 255),
                  anchor="mm", stroke_width=1, stroke_fill=_darken(c2, 0.4))
        y_pos += 80

    # Context body
    y_pos += 30
    context_lines = _wrap_text(draw, context, font_context, text_width)
    for line in context_lines[:6]:
        draw.text((width // 2, y_pos), line, font=font_context, fill=(255, 255, 255),
                  anchor="mm")
        y_pos += 60

    # Offer box
    if offer:
        y_pos += 50
        offer_text = f"🎉 {offer.upper()}"
        bbox = draw.textbbox((0, 0), offer_text, font=font_offer)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        box_pad = 35
        box_coords = [
            (width - tw) // 2 - box_pad,
            y_pos - th // 2 - box_pad // 2,
            (width + tw) // 2 + box_pad,
            y_pos + th // 2 + box_pad // 2
        ]
        draw.rounded_rectangle(box_coords, radius=18, fill=(255, 255, 255),
                                outline=(255, 255, 255), width=3)
        draw.text((width // 2, y_pos), offer_text, font=font_offer,
                  fill=c2, anchor="mm")

    # Footer
    y_pos = height - 130
    footer_parts = []
    if restaurant.get("location"):
        footer_parts.append(f"📍 {restaurant['location']}")
    if restaurant.get("phone"):
        footer_parts.append(f"📞 {restaurant['phone']}")
    if restaurant.get("instagram"):
        footer_parts.append(f"@{restaurant['instagram']}")

    if footer_parts:
        footer_text = "  •  ".join(footer_parts)
        draw.text((width // 2, y_pos), footer_text, font=font_small,
                  fill=(255, 255, 255), anchor="mm")

    # Organic noise
    img = _add_noise_overlay(img, intensity=10)
    
    # Overlay logo
    img = _overlay_logo(img, restaurant, position="top-right", max_size=120)

    filename = f"post_{restaurant['id']}_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(STATIC_DIR, filename)
    img.save(filepath, "PNG", quality=95)
    return filename
