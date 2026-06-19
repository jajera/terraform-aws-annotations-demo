"""Unit tests for api/validator.py."""

import pytest

from api.validator import validate_params


class TestValidateParams:
    def test_empty_params(self):
        result, error = validate_params({})
        assert error is None
        assert result == {}

    def test_valid_day_phase(self):
        result, error = validate_params({"day_phase": "dawn"})
        assert error is None
        assert result == {"day_phase": "dawn"}

    def test_invalid_day_phase(self):
        result, error = validate_params({"day_phase": "afternoon"})
        assert result is None
        assert "day_phase" in error.lower()

    def test_valid_utc_day(self):
        result, error = validate_params({"utc_day": "2026.170"})
        assert error is None
        assert result == {"utc_day": "2026.170"}

    def test_invalid_utc_day(self):
        result, error = validate_params({"utc_day": "2026-170"})
        assert result is None
        assert "utc_day" in error.lower()

    def test_valid_visibility(self):
        result, error = validate_params({"visibility": "low_light"})
        assert error is None
        assert result == {"visibility": "low_light"}

    def test_invalid_visibility(self):
        result, error = validate_params({"visibility": "foggy"})
        assert result is None
        assert "visibility" in error.lower()

    def test_invalid_offset(self):
        result, error = validate_params({"offset": "-1"})
        assert result is None
        assert "offset" in error.lower()

    def test_valid_offset(self):
        result, error = validate_params({"offset": "24", "limit": "24"})
        assert error is None
        assert result == {"offset": 24, "limit": 24}

    def test_multiple_valid_params(self):
        params = {
            "day_phase": "day",
            "utc_day": "2026.170",
            "visibility": "daylight",
            "limit": "60",
        }
        result, error = validate_params(params)
        assert error is None
        assert result == {
            "day_phase": "day",
            "utc_day": "2026.170",
            "visibility": "daylight",
            "limit": 60,
        }
