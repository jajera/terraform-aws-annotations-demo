"""Core parsing and scene classification for ingest pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

KEY_PATTERN = re.compile(
    r"^camera/volcano/images/"
    r"(?P<year>\d{4})/"
    r"(?P<site>[A-Z0-9]+)/"
    r"(?P<camera>[A-Z0-9]+\.\d{2})/"
    r"(?P<utc_day>\d{4}\.\d{3})/"
    r"(?P<file_year>\d{4})\.(?P<file_doy>\d{3})\.(?P<hhmm>\d{4})\.(?P<ss>\d{2})\.(?P<camera_file>[A-Z0-9]+\.\d{2})(?:\.(?P<seq>\d+))?\.jpg$"
)

# Mean grayscale luminance thresholds (0.0–1.0).
LOW_LIGHT_LUMINANCE = 0.18
VERY_DARK_LUMINANCE = 0.10

MODEL_VERSION = "metadata-luminance-v1"


def is_jpg_key(key: str) -> bool:
    """Return True when key ends with .jpg (case-insensitive)."""
    return key.lower().endswith(".jpg")


def _day_phase(hour_local: int) -> str:
    """Display-only local light phase from camera timezone hour."""
    if 0 <= hour_local <= 4:
        return "night"
    if 5 <= hour_local <= 8:
        return "dawn"
    if 9 <= hour_local <= 16:
        return "day"
    if 17 <= hour_local <= 20:
        return "dusk"
    return "night"


def compute_scene_luminance(image_bytes: bytes) -> float:
    """Return mean grayscale luminance in [0.0, 1.0] from JPEG bytes."""
    from io import BytesIO

    from PIL import Image, ImageStat

    with Image.open(BytesIO(image_bytes)) as img:
        gray = img.convert("L")
        mean = ImageStat.Stat(gray).mean[0]
    return max(0.0, min(1.0, mean / 255.0))


def classify_visibility(scene_luminance: float) -> str:
    """Map pixel brightness to a simple visibility bucket."""
    if scene_luminance < VERY_DARK_LUMINANCE:
        return "night"
    if scene_luminance < LOW_LIGHT_LUMINANCE:
        return "low_light"
    return "daylight"


def classify_scene(hour_local: int, scene_luminance: float) -> dict[str, Any]:
    """Derive walkthrough tags from clock + pixels (no ML)."""
    return {
        "day_phase": _day_phase(hour_local),
        "visibility": classify_visibility(scene_luminance),
        "scene_luminance": round(scene_luminance, 3),
    }


def parse_object_key(key: str) -> dict[str, Any] | None:
    """
    Parse expected camera image key and extract normalized fields.

    Returns None if key does not match expected structure.
    """
    m = KEY_PATTERN.match(key)
    if not m:
        return None

    year = int(m.group("year"))
    file_year = int(m.group("file_year"))
    day_of_year = int(m.group("file_doy"))
    hhmm = m.group("hhmm")
    ss = int(m.group("ss"))
    hour = int(hhmm[:2])
    minute = int(hhmm[2:])

    if file_year != year:
        return None
    if not (1 <= day_of_year <= 366):
        return None
    if hour > 23 or minute > 59 or ss > 59:
        return None
    if m.group("camera") != m.group("camera_file"):
        return None

    dt = datetime.strptime(f"{year} {day_of_year:03d} {hour:02d}:{minute:02d}:{ss:02d}", "%Y %j %H:%M:%S").replace(
        tzinfo=timezone.utc
    )

    return {
        "camera_id": m.group("camera"),
        "volcano_site": m.group("site"),
        "utc_day": m.group("utc_day"),
        "sequence": int(m.group("seq") or 0),
        "captured_utc": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "year": year,
        "day_of_year": day_of_year,
        "hour": hour,
        "minute": minute,
        "second": ss,
    }
