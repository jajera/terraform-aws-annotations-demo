"""Validation helpers for API query parameters."""

from __future__ import annotations

from typing import Any

VALID_DAY_PHASE = {"night", "dawn", "day", "dusk"}
VALID_VISIBILITY = {"daylight", "low_light", "night"}
UTC_DAY_PATTERN = r"^[0-9]{4}\.[0-9]{3}$"


def validate_params(params: dict[str, str] | None) -> tuple[dict[str, Any] | None, str | None]:
    """Validate and normalize query parameters."""
    params = params or {}
    validated: dict[str, Any] = {}

    day_phase = params.get("day_phase")
    if day_phase:
        if day_phase not in VALID_DAY_PHASE:
            return None, "Invalid day_phase"
        validated["day_phase"] = day_phase

    utc_day = params.get("utc_day")
    if utc_day:
        import re

        if not re.fullmatch(UTC_DAY_PATTERN, utc_day):
            return None, "Invalid utc_day"
        validated["utc_day"] = utc_day

    visibility = params.get("visibility")
    if visibility:
        if visibility not in VALID_VISIBILITY:
            return None, "Invalid visibility"
        validated["visibility"] = visibility

    limit = params.get("limit")
    if limit:
        try:
            parsed_limit = int(limit)
        except (TypeError, ValueError):
            return None, "Invalid limit"

        if parsed_limit < 1 or parsed_limit > 200:
            return None, "Invalid limit"
        validated["limit"] = parsed_limit

    offset = params.get("offset")
    if offset:
        try:
            parsed_offset = int(offset)
        except (TypeError, ValueError):
            return None, "Invalid offset"

        if parsed_offset < 0:
            return None, "Invalid offset"
        validated["offset"] = parsed_offset

    return validated, None
