"""Unit tests for ingest_annotate/classifier.py."""

import pytest

from ingest_annotate.classifier import (
    classify_scene,
    classify_visibility,
    compute_scene_luminance,
    is_jpg_key,
    parse_object_key,
)


class TestIsJpgKey:
    def test_jpg_lowercase(self):
        assert is_jpg_key("image.jpg") is True

    def test_png_extension(self):
        assert is_jpg_key("image.png") is False


class TestParseObjectKey:
    VALID_KEY = "camera/volcano/images/2026/TKAH/TKAH.01/2026.169/2026.169.0800.00.TKAH.01.jpg"

    def test_valid_key_returns_correct_dict(self):
        result = parse_object_key(self.VALID_KEY)
        assert result is not None
        assert result["camera_id"] == "TKAH.01"
        assert result["utc_day"] == "2026.169"
        assert result["captured_utc"] == "2026-06-18T08:00:00Z"

    def test_invalid_key_random_string(self):
        assert parse_object_key("some/random/string.jpg") is None


class TestClassifyVisibility:
    def test_night(self):
        assert classify_visibility(0.05) == "night"

    def test_low_light(self):
        assert classify_visibility(0.12) == "low_light"

    def test_daylight(self):
        assert classify_visibility(0.55) == "daylight"


class TestClassifyScene:
    def test_day_phase_day(self):
        result = classify_scene(12, 0.55)
        assert result["day_phase"] == "day"
        assert result["visibility"] == "daylight"

    def test_day_phase_night(self):
        result = classify_scene(2, 0.05)
        assert result["day_phase"] == "night"
        assert result["visibility"] == "night"


class TestComputeSceneLuminance:
    def test_sample_image_luminance(self):
        try:
            from PIL import Image  # noqa: F401
        except ImportError:
            pytest.skip("Pillow not available")
        sample = "samples/volcano/2026.169.0240.00.TKAH.01.jpg"
        with open(sample, "rb") as f:
            lum = compute_scene_luminance(f.read())
        assert 0.0 <= lum <= 1.0
