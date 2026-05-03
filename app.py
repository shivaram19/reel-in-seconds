"""
Sabrika Brand Manager - Instagram Content Automation for Restaurants
A simple web app for generating branded Instagram Stories and Posts.
"""

import os
import uuid
import traceback
import logging
import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from restaurants import load_restaurants, add_restaurant, get_restaurant, delete_restaurant
from image_generator import generate_story, generate_post
from reel_engine import generate_reel, generate_reel_v2, get_soul

# Setup file logging for deep debugging
LOG_FILE = os.path.join(os.path.dirname(__file__), "server_debug.log")
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info("=" * 60)
logger.info("SERVER STARTING - Sabrika Brand Manager")
logger.info(f"Working directory: {os.path.dirname(__file__)}")
logger.info(f"Python executable: {os.sys.executable}")
logger.info("=" * 60)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sabrika-brand-manager-2026'

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static", "generated")
os.makedirs(STATIC_DIR, exist_ok=True)
REELS_DIR = os.path.join(os.path.dirname(__file__), "static", "reels")
os.makedirs(REELS_DIR, exist_ok=True)
THUMBNAILS_DIR = os.path.join(os.path.dirname(__file__), "static", "thumbnails")
os.makedirs(THUMBNAILS_DIR, exist_ok=True)
LOGOS_DIR = os.path.join(os.path.dirname(__file__), "static", "logos")
os.makedirs(LOGOS_DIR, exist_ok=True)


@app.route("/")
def index():
    restaurants = load_restaurants()
    return render_template("index.html", restaurants=restaurants)


@app.route("/api/restaurants", methods=["GET", "POST"])
def api_restaurants():
    if request.method == "GET":
        return jsonify(load_restaurants())
    
    data = request.json
    restaurant = add_restaurant(
        name=data.get("name", ""),
        cuisine=data.get("cuisine", ""),
        location=data.get("location", ""),
        tagline=data.get("tagline", ""),
        color1=data.get("color1", "#FF6B35"),
        color2=data.get("color2", "#F7931E"),
        phone=data.get("phone", ""),
        instagram=data.get("instagram", ""),
        logo=data.get("logo", "")
    )
    return jsonify(restaurant), 201


@app.route("/api/restaurants/<int:rid>", methods=["DELETE"])
def api_delete_restaurant(rid):
    restaurant = get_restaurant(rid)
    if restaurant and restaurant.get("logo"):
        logo_path = os.path.join(os.path.dirname(__file__), restaurant["logo"].lstrip("/"))
        if os.path.exists(logo_path):
            os.remove(logo_path)
    delete_restaurant(rid)
    return jsonify({"status": "deleted"})


@app.route("/api/upload-logo", methods=["POST"])
def api_upload_logo():
    """Upload a restaurant logo image."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("png", "jpg", "jpeg", "gif", "webp", "svg"):
        return jsonify({"error": "Invalid file type. Use PNG, JPG, JPEG, GIF, WEBP, or SVG"}), 400
    
    filename = f"logo_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(LOGOS_DIR, filename)
    file.save(filepath)
    
    return jsonify({
        "filename": filename,
        "url": f"/static/logos/{filename}"
    }), 201


@app.route("/static/logos/<path:filename>")
def serve_logo(filename):
    return send_from_directory(LOGOS_DIR, filename)


@app.route("/api/health")
def api_health():
    """Health check endpoint - returns code version info for debugging."""
    import hashlib
    # Compute hash of image_generator.py to verify which version is running
    ig_path = os.path.join(os.path.dirname(__file__), "image_generator.py")
    with open(ig_path, "rb") as f:
        ig_hash = hashlib.md5(f.read()).hexdigest()[:8]
    return jsonify({
        "status": "ok",
        "code_hash": ig_hash,
        "server_time": datetime.datetime.now().isoformat(),
        "python": os.sys.version,
        "cwd": os.getcwd()
    })


@app.route("/api/generate", methods=["POST"])
def api_generate():
    logger.info(f"[api_generate] Request from {request.remote_addr}")
    try:
        data = request.json
        logger.info(f"[api_generate] Payload: {data}")
        if not data:
            logger.error("[api_generate] No JSON data received")
            return jsonify({"error": "No JSON data received"}), 400
        
        rid = data.get("restaurant_id")
        try:
            rid = int(rid)
        except (TypeError, ValueError):
            logger.error(f"[api_generate] Invalid restaurant_id: {rid}")
            return jsonify({"error": "Invalid restaurant_id"}), 400
        
        content_type = data.get("type", "story")
        context = data.get("context", "")
        event = data.get("event", "")
        offer = data.get("offer", "")
        
        restaurant = get_restaurant(rid)
        logger.info(f"[api_generate] Restaurant data: {restaurant}")
        if not restaurant:
            logger.error(f"[api_generate] Restaurant not found: {rid}")
            return jsonify({"error": "Restaurant not found"}), 404
        
        # Deep inspection of color fields
        color1 = restaurant.get("color1")
        color2 = restaurant.get("color2")
        logger.info(f"[api_generate] color1 type={type(color1).__name__} value={color1!r}")
        logger.info(f"[api_generate] color2 type={type(color2).__name__} value={color2!r}")
        
        if content_type == "story":
            logger.info("[api_generate] Calling generate_story...")
            filename = generate_story(restaurant, context, event, offer)
        else:
            logger.info("[api_generate] Calling generate_post...")
            filename = generate_post(restaurant, context, event, offer)
        
        logger.info(f"[api_generate] SUCCESS: {filename}")
        return jsonify({
            "filename": filename,
            "url": f"/static/generated/{filename}",
            "type": content_type,
            "restaurant": restaurant["name"]
        })
    except Exception as e:
        logger.exception("[api_generate] CRASH:")
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route("/static/generated/<path:filename>")
def serve_image(filename):
    return send_from_directory(STATIC_DIR, filename)


@app.route("/gallery")
def gallery():
    files = []
    for f in os.listdir(STATIC_DIR):
        if f.endswith('.png'):
            files.append({
                "filename": f,
                "url": f"/static/generated/{f}",
                "type": "story" if f.startswith("story") else "post"
            })
    files.sort(key=lambda x: os.path.getmtime(os.path.join(STATIC_DIR, x["filename"])), reverse=True)
    return render_template("gallery.html", images=files)


@app.route("/api/reels", methods=["POST"])
def api_generate_reel():
    """
    Generate a restaurant reel from raw clips.

    Research-backed pipeline:
        - PySceneDetect for scene boundaries (F1=91.59 on BBC dataset)
          [github.com/Breakthrough/PySceneDetect benchmark]
        - faster-whisper for subtitles (4x faster than original Whisper)
          [pypi.org/project/faster-whisper/, SYSTRAN, 2025]
        - FFmpeg for assembly (100x+ faster than MoviePy)
          [github.com/Zulko/moviepy/issues/2165, 2024]
        - PIL for branded text overlays
          [pillow.readthedocs.io, pypi.org/project/Pillow/]
    """
    data = request.json or {}
    rid = data.get("restaurant_id")
    try:
        rid = int(rid)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid restaurant_id"}), 400

    restaurant = get_restaurant(rid)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404

    clip_urls = data.get("clips", [])
    hook_text = data.get("hook", "")
    offer_text = data.get("offer", "")
    target_duration = data.get("duration", 30)
    generate_subs = data.get("subtitles", True)

    # Convert clip URLs to local paths
    clip_paths = []
    for url in clip_urls:
        # Handle /static/uploads/filename.mp4 format
        if url.startswith("/static/"):
            path = os.path.join(os.path.dirname(__file__), url.lstrip("/"))
            if os.path.exists(path):
                clip_paths.append(path)

    if not clip_paths:
        return jsonify({"error": "No valid clips provided"}), 400

    try:
        result = generate_reel(
            clip_paths=clip_paths,
            restaurant=restaurant,
            hook_text=hook_text,
            offer_text=offer_text,
            target_duration=float(target_duration),
            generate_subs=generate_subs,
            generate_thumbnail_flag=True
        )

        if "error" in result:
            return jsonify({"error": result["error"]}), 500

        return jsonify({
            "reel_id": result["reel_id"],
            "filename": result["filename"],
            "reel_url": result["reel_url"],
            "thumbnail_url": result.get("thumbnail_url", ""),
            "duration": result["duration"],
            "restaurant": result["restaurant"],
            "hook_text": result["hook_text"],
            "has_subtitles": result["has_subtitles"],
        }), 201

    except Exception as e:
        app.logger.exception("[api_generate_reel] FAILED")
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


@app.route("/api/reels/v2", methods=["POST"])
def api_generate_reel_v2():
    """
    Generate a restaurant reel using the new frame-by-frame analysis engine.
    
    V2 Pipeline:
        1. YOLOv8 frame-by-frame object detection
        2. Restaurant domain relevance mapping (The Pakwaan's soul)
        3. 6-act narrative assembly (Hook→Promise→Process→Payoff→Social→CTA)
        4. FFmpeg filter_complex with color grading + transitions
    
    No subtitles. Pure visual storytelling from the owner's perspective.
    """
    data = request.json or {}
    rid = data.get("restaurant_id")
    try:
        rid = int(rid)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid restaurant_id"}), 400

    restaurant = get_restaurant(rid)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404

    clip_urls = data.get("clips", [])
    template = data.get("template", "auto")  # auto, heritage, energetic, warm
    target_duration = data.get("duration", 30)

    # Convert clip URLs to local paths
    clip_paths = []
    for url in clip_urls:
        if url.startswith("/static/"):
            path = os.path.join(os.path.dirname(__file__), url.lstrip("/"))
            if os.path.exists(path):
                clip_paths.append(path)

    if not clip_paths:
        return jsonify({"error": "No valid clips provided"}), 400

    try:
        app.logger.info(f"[api_generate_reel_v2] Starting V2 reel for restaurant {rid}")
        app.logger.info(f"[api_generate_reel_v2] {len(clip_paths)} clips, template={template}")

        # Get restaurant soul
        soul = get_soul(restaurant.get("name", "default").lower().replace(" ", ""))
        
        # Override template if specified
        if template != "auto":
            soul.narrative_arc["pacing"] = template
        
        # Find logo
        logo_path = None
        if restaurant.get("logo"):
            logo_path = os.path.join(
                os.path.dirname(__file__), 
                "static", "logos", 
                restaurant["logo"]
            )
            if not os.path.exists(logo_path):
                logo_path = None

        # Generate reel
        result = generate_reel_v2(
            clip_paths=clip_paths,
            soul=soul,
            logo_path=logo_path,
        )

        if not result.success:
            return jsonify({
                "error": result.error_message or "Reel generation failed"
            }), 500

        # Get relative URL
        reel_filename = os.path.basename(result.output_path)
        reel_url = f"/static/reels/{reel_filename}"

        return jsonify({
            "success": True,
            "reel_url": reel_url,
            "filename": reel_filename,
            "duration": round(result.duration, 1),
            "resolution": f"{result.resolution[0]}x{result.resolution[1]}",
            "file_size_mb": round(result.file_size_mb, 1),
            "restaurant": restaurant.get("name", ""),
            "template_used": template,
            "engine_version": "v2",
            "message": f"Reel generated using {soul.name}'s soul profile",
        }), 201

    except Exception as e:
        app.logger.exception("[api_generate_reel_v2] FAILED")
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


@app.route("/api/reels/<reel_id>/timeline", methods=["GET"])
def api_reel_timeline(reel_id):
    """Get the narrative timeline for a generated reel."""
    # This would need persistent storage of reel metadata
    # For now, return a placeholder
    return jsonify({
        "reel_id": reel_id,
        "timeline": [
            {"act": "hook", "time": "0-3s", "emotion": "tempting"},
            {"act": "promise", "time": "3-8s", "emotion": "intriguing"},
            {"act": "process", "time": "8-20s", "emotion": "satisfying"},
            {"act": "payoff", "time": "20-25s", "emotion": "mouthwatering"},
            {"act": "social", "time": "25-28s", "emotion": "warm"},
            {"act": "cta", "time": "28-30s", "emotion": "inviting"},
        ]
    })


@app.route("/static/reels/<path:filename>")
def serve_reel(filename):
    return send_from_directory(REELS_DIR, filename)


@app.route("/static/thumbnails/<path:filename>")
def serve_thumbnail(filename):
    return send_from_directory(THUMBNAILS_DIR, filename)


@app.route("/api/upload", methods=["POST"])
def api_upload_clip():
    """Upload a raw video clip for reel creation."""
    upload_dir = os.path.join(os.path.dirname(__file__), "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("mp4", "mov", "avi", "mkv", "webm"):
        return jsonify({"error": "Invalid file type. Use MP4, MOV, AVI, MKV, or WEBM"}), 400

    filename = f"clip_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    return jsonify({
        "filename": filename,
        "url": f"/static/uploads/{filename}",
        "path": filepath,
    }), 201


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
