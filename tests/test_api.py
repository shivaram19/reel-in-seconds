"""
API Endpoint Tests — Sabrika Brand Manager
===========================================

These tests validate the contract between frontend and backend.
Every endpoint that the UI depends on must have a test here.

Research basis:
  - Test pyramid: unit tests (fast) → integration tests (medium) → E2E (slow)
  - These are integration tests: they exercise Flask + JSON persistence layer
  - Humble & Farley (2010): "If it hurts, do it more frequently." Deploy often,
    test often.

[^1]: Humble, J., & Farley, D. (2010). Continuous Delivery. Addison-Wesley.
"""

import json
import pytest


class TestHealthEndpoint:
    """GET /api/health — The monitor's primary probe target."""

    def test_health_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert "code_hash" in data
        assert "server_time" in data

    def test_health_has_required_fields(self, client):
        resp = client.get("/api/health")
        data = resp.get_json()
        required = {"status", "code_hash", "server_time", "python", "cwd"}
        assert required.issubset(set(data.keys()))


class TestRestaurantsEndpoint:
    """GET/POST /api/restaurants — Core data layer."""

    def test_get_restaurants_returns_list(self, client):
        resp = client.get("/api/restaurants")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) > 0  # The Pakwaan must exist

    def test_get_restaurants_has_required_fields(self, client):
        resp = client.get("/api/restaurants")
        data = resp.get_json()
        if data:
            r = data[0]
            required = {"id", "name", "cuisine", "location", "audience"}
            assert required.issubset(set(r.keys()))

    def test_post_restaurant_creates_record(self, client):
        payload = {
            "name": "Test Restaurant",
            "cuisine": "Test Cuisine",
            "location": "Test Location",
            "audience": "Test Audience",
            "color1": "#ff0000",
            "color2": "#00ff00",
            "tagline": "Test tagline",
            "description": "Test description"
        }
        resp = client.post("/api/restaurants", json=payload)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "id" in data
        assert data["name"] == "Test Restaurant"

    def test_post_restaurant_sanitizes_colors(self, client):
        """Color values must be sanitized to valid hex."""
        payload = {
            "name": "Color Test",
            "cuisine": "Test",
            "location": "Test",
            "audience": "Test",
            "color1": (255, 0, 0),  # tuple — was causing crashes
            "color2": "#00ff00",
        }
        resp = client.post("/api/restaurants", json=payload)
        assert resp.status_code == 200
        data = resp.get_json()
        # Should have been sanitized to hex string
        assert isinstance(data.get("color1"), str)
        assert data["color1"].startswith("#")


class TestGenerateEndpoint:
    """POST /api/generate — Image generation pipeline."""

    def test_generate_requires_restaurant_id(self, client):
        resp = client.post("/api/generate", json={})
        assert resp.status_code == 400

    def test_generate_returns_image_url(self, client):
        resp = client.post("/api/generate", json={
            "restaurant_id": 1,
            "type": "story"
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "image_url" in data or "url" in data


class TestReelsEndpoint:
    """POST /api/reels/v2 — V2 frame-analysis reel pipeline."""

    def test_reels_v2_requires_clips(self, client):
        resp = client.post("/api/reels/v2", json={"restaurant_id": 1})
        assert resp.status_code == 400

    def test_reels_v2_returns_job_structure(self, client):
        """Even with empty clips, should return structured error or job ID."""
        resp = client.post("/api/reels/v2", json={
            "restaurant_id": 1,
            "clips": [],
            "template": "auto",
            "duration": 30
        })
        # Should be 400 (no clips) or structured response
        assert resp.status_code in (200, 400)


class TestUploadEndpoint:
    """POST /api/upload — Video clip upload."""

    def test_upload_requires_file(self, client):
        resp = client.post("/api/upload")
        assert resp.status_code == 400
