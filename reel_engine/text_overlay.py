"""
Text Overlay Renderer — Branded Text for Reels using PIL

Renders restaurant-branded text as transparent PNG images for FFmpeg overlay.
Supports: stroke/outline, shadows, gradients, multi-line wrapping, custom fonts.

Citations:
    - PIL is the standard for programmatic image generation in Python
      [pypi.org/project/Pillow/]
    - PIL supports stroke/outline text, multi-line wrapping, custom fonts
      [pillow.readthedocs.io/en/stable/reference/ImageDraw.html]
    - Used by Stack Builders for automated video thumbnails
      [stackbuilders.com/insights/python-video-generation/, 2019 updated 2024]
    - TikTokAIVideoGenerator uses PIL for subtitle styling
      [github.com/GabrielLaxy/TikTokAIVideoGenerator, 2025]
"""

import os
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Optional

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")


def _hex_to_rgb(color) -> Tuple[int, int, int]:
    """Convert hex string or RGB tuple/list to RGB tuple. Defensive against bad data."""
    if isinstance(color, (tuple, list)) and len(color) >= 3:
        return tuple(int(c) for c in color[:3])
    if isinstance(color, str):
        color = color.lstrip("#")
        if len(color) == 6:
            return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    return (255, 107, 53)


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
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
            except Exception:
                pass
    return ImageFont.load_default()


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.Draw) -> list:
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        text_width = bbox[2] - bbox[0]
        if text_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines if lines else [text]


def render_text_overlay(
    text: str,
    width: int = 1080,
    font_size: int = 80,
    text_color: str = "#FFFFFF",
    stroke_color: str = "#000000",
    stroke_width: int = 4,
    shadow_offset: Tuple[int, int] = (4, 4),
    shadow_blur: int = 8,
    max_width: int = 900,
    line_spacing: float = 1.3,
    padding: int = 40,
    align: str = "center"
) -> Image.Image:
    """
    Render text as a transparent PNG image for FFmpeg overlay.
    
    Returns PIL Image in RGBA mode with transparent background.
    """
    font = _get_font(font_size, bold=True)
    
    # Create a temporary image for text measurement
    temp_img = Image.new("RGBA", (width * 2, width * 2), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp_img)
    
    # Wrap text
    lines = _wrap_text(text, font, max_width, temp_draw)
    
    # Calculate total height
    line_heights = []
    total_text_height = 0
    for line in lines:
        bbox = temp_draw.textbbox((0, 0), line, font=font)
        lh = bbox[3] - bbox[1]
        line_heights.append(lh)
        total_text_height += lh
    
    total_text_height += int(line_heights[0] * (line_spacing - 1.0)) * (len(lines) - 1)
    
    # Calculate image dimensions
    img_width = width
    img_height = total_text_height + padding * 2 + shadow_blur * 2 + stroke_width * 2
    
    # Create final image with transparent background
    img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw shadow
    rgb_text = _hex_to_rgb(text_color)
    rgb_stroke = _hex_to_rgb(stroke_color)
    
    y_offset = padding + shadow_blur + stroke_width
    for i, line in enumerate(lines):
        line_width = draw.textbbox((0, 0), line, font=font)[2] - draw.textbbox((0, 0), line, font=font)[0]
        
        if align == "center":
            x = (img_width - line_width) // 2
        elif align == "right":
            x = img_width - line_width - padding
        else:
            x = padding
        
        # Shadow
        if shadow_offset[0] or shadow_offset[1]:
            shadow_x = x + shadow_offset[0]
            shadow_y = y_offset + shadow_offset[1]
            for dx in range(-shadow_blur, shadow_blur + 1, 2):
                for dy in range(-shadow_blur, shadow_blur + 1, 2):
                    alpha = max(0, 80 - abs(dx) * 10 - abs(dy) * 10)
                    draw.text((shadow_x + dx, shadow_y + dy), line, font=font,
                              fill=(0, 0, 0, alpha))
        
        # Stroke
        if stroke_width > 0:
            for dx in range(-stroke_width, stroke_width + 1):
                for dy in range(-stroke_width, stroke_width + 1):
                    if dx * dx + dy * dy <= stroke_width * stroke_width:
                        draw.text((x + dx, y_offset + dy), line, font=font,
                                  fill=rgb_stroke + (255,))
        
        # Fill
        draw.text((x, y_offset), line, font=font, fill=rgb_text + (255,))
        
        y_offset += int(line_heights[i] * line_spacing)
    
    # Crop to content
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    
    return img


def render_hook_text(
    text: str,
    brand_color: str = "#FF6B35",
    width: int = 1080,
    output_path: Optional[str] = None
) -> str:
    """
    Render a "hook" text overlay (big, bold, attention-grabbing).
    Returns path to saved PNG.
    """
    img = render_text_overlay(
        text=text,
        width=width,
        font_size=100,
        text_color="#FFFFFF",
        stroke_color="#000000",
        stroke_width=5,
        shadow_offset=(6, 6),
        shadow_blur=12,
        max_width=950,
        line_spacing=1.2,
        align="center"
    )
    
    if output_path is None:
        import uuid
        output_path = os.path.join(STATIC_DIR, "generated", f"hook_{uuid.uuid4().hex[:8]}.png")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    return output_path


def render_offer_banner(
    text: str,
    brand_color1: str = "#FF6B35",
    brand_color2: str = "#F7931E",
    width: int = 1080,
    output_path: Optional[str] = None
) -> str:
    """
    Render an offer banner (e.g., "20% OFF FAMILY PACK").
    Returns path to saved PNG.
    """
    img = render_text_overlay(
        text=f"🎉 {text}",
        width=width,
        font_size=72,
        text_color="#FFFFFF",
        stroke_color=_hex_to_rgb(brand_color1),
        stroke_width=4,
        shadow_offset=(4, 4),
        shadow_blur=8,
        max_width=950,
        line_spacing=1.2,
        align="center"
    )
    
    if output_path is None:
        import uuid
        output_path = os.path.join(STATIC_DIR, "generated", f"offer_{uuid.uuid4().hex[:8]}.png")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    return output_path


def render_end_card(
    restaurant_name: str,
    location: str,
    instagram: str,
    phone: str,
    brand_color1: str = "#FF6B35",
    brand_color2: str = "#F7931E",
    width: int = 1080,
    height: int = 1920,
    output_path: Optional[str] = None
) -> str:
    """
    Render an end card PNG with restaurant info.
    Returns path to saved PNG.
    """
    # Create gradient background
    c1 = _hex_to_rgb(brand_color1)
    c2 = _hex_to_rgb(brand_color2)
    
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = img.load()
    
    for y in range(height):
        ratio = y / height
        r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
        g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
        b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
        for x in range(width):
            pixels[x, y] = (r, g, b, 230)
    
    draw = ImageDraw.Draw(img)
    
    # Restaurant name
    name_font = _get_font(90, bold=True)
    bbox = draw.textbbox((0, 0), restaurant_name.upper(), font=name_font)
    name_w = bbox[2] - bbox[0]
    name_x = (width - name_w) // 2
    name_y = height // 2 - 200
    
    # Draw stroke
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            draw.text((name_x + dx, name_y + dy), restaurant_name.upper(),
                      font=name_font, fill=(0, 0, 0, 200))
    draw.text((name_x, name_y), restaurant_name.upper(), font=name_font, fill=(255, 255, 255, 255))
    
    # Tagline / Location
    loc_font = _get_font(40)
    loc_text = f"📍 {location}" if location else ""
    if loc_text:
        bbox = draw.textbbox((0, 0), loc_text, font=loc_font)
        loc_w = bbox[2] - bbox[0]
        draw.text(((width - loc_w) // 2, name_y + 140), loc_text, font=loc_font,
                  fill=(255, 255, 255, 220))
    
    # Instagram
    ig_font = _get_font(36)
    ig_text = f"@{instagram}" if instagram else ""
    if ig_text:
        bbox = draw.textbbox((0, 0), ig_text, font=ig_font)
        ig_w = bbox[2] - bbox[0]
        draw.text(((width - ig_w) // 2, name_y + 220), ig_text, font=ig_font,
                  fill=(255, 255, 255, 200))
    
    # Phone
    phone_font = _get_font(32)
    phone_text = f"📞 {phone}" if phone else ""
    if phone_text:
        bbox = draw.textbbox((0, 0), phone_text, font=phone_font)
        phone_w = bbox[2] - bbox[0]
        draw.text(((width - phone_w) // 2, name_y + 290), phone_text, font=phone_font,
                  fill=(255, 255, 255, 180))
    
    # "Follow for more" CTA
    cta_font = _get_font(28)
    cta_text = "Follow us for more delicious updates!"
    bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    cta_w = bbox[2] - bbox[0]
    draw.text(((width - cta_w) // 2, name_y + 380), cta_text, font=cta_font,
              fill=(255, 255, 255, 150))
    
    if output_path is None:
        import uuid
        output_path = os.path.join(STATIC_DIR, "generated", f"endcard_{uuid.uuid4().hex[:8]}.png")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    return output_path
