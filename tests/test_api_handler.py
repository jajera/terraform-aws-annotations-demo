"""Integration tests for api/handler.py with mocked AWS SDK calls."""

import json
from unittest.mock import MagicMock, patch

import pytest

from api.handler import handler


# Environment variables needed by the handler
API_ENV = {
    "PRIVATE_BUCKET": "test-private-bucket",
    "DYNAMODB_TABLE": "",
    "PRESIGN_EXPIRY_SECONDS": "900",
}


def _make_annotation_value(
    day_phase="day",
    utc_day="2026.169",
    visibility="daylight",
    captured_utc="2026-06-18T08:00:00Z",
):
    """Build a JSON annotation value string."""
    return json.dumps({
        "camera_id": "TKAH.01",
        "utc_day": utc_day,
        "day_phase": day_phase,
        "visibility": visibility,
        "captured_utc": captured_utc,
    })


def _build_list_pages(keys):
    """Build paginator pages from a list of keys."""
    if not keys:
        return [{}]
    return [{"Contents": [{"Key": k} for k in keys]}]


class _FakePaginator:
    """Fake paginator that yields pre-built pages."""

    def __init__(self, pages):
        self._pages = pages

    def paginate(self, **kwargs):
        return iter(self._pages)


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    """Set required environment variables for the API handler."""
    for key, value in API_ENV.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def mock_aws():
    """Patch boto3 inside the api handler module."""
    mock_s3 = MagicMock()

    with patch("api.handler.boto3") as patched_boto3:
        patched_boto3.client.return_value = mock_s3
        patched_boto3.resource.return_value = None
        yield {"s3": mock_s3}


def test_no_filters_returns_items(mock_aws):
    """No filters — S3 listing returns objects with annotations → 200 with items and total_available."""
    mock_s3 = mock_aws["s3"]

    keys = [
        "camera/volcano/images/2026/TKAH/TKAH.01/2026.169/2026.169.0800.00.TKAH.01.0.jpg",
        "camera/volcano/images/2026/TKAH/TKAH.01/2026.169/2026.169.1000.00.TKAH.01.0.jpg",
    ]
    pages = _build_list_pages(keys)
    mock_s3.get_paginator.return_value = _FakePaginator(pages)

    # get_object_annotation — s3_annotations helper checks hasattr then calls it
    # The helper reads AnnotationPayload from the response
    mock_s3.get_object_annotation.return_value = {
        "AnnotationPayload": _make_annotation_value().encode("utf-8"),
    }

    # generate_presigned_url returns a dummy URL
    mock_s3.generate_presigned_url.return_value = "https://example.com/presigned"

    event = {"queryStringParameters": {}}
    result = handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["total_available"] == 2
    assert len(body["items"]) == 2
    for item in body["items"]:
        assert "key" in item
        assert "tags" in item
        assert "image_url" in item
        assert item["image_url"] == "https://example.com/presigned"


def test_filter_applied(mock_aws):
    """Filter applied — only matching annotations returned."""
    mock_s3 = mock_aws["s3"]

    keys = ["image1.jpg", "image2.jpg"]
    pages = _build_list_pages(keys)
    mock_s3.get_paginator.return_value = _FakePaginator(pages)

    # First image is "day", second is "night"
    call_count = {"n": 0}

    def get_annotation_side_effect(**kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return {"AnnotationPayload": _make_annotation_value(day_phase="day").encode("utf-8")}
        return {"AnnotationPayload": _make_annotation_value(day_phase="night").encode("utf-8")}

    mock_s3.get_object_annotation.side_effect = get_annotation_side_effect
    mock_s3.generate_presigned_url.return_value = "https://example.com/presigned"

    event = {"queryStringParameters": {"day_phase": "day"}}
    result = handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["total_available"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["tags"]["day_phase"] == "day"


def test_invalid_parameter_returns_400(mock_aws):
    """Invalid day_phase parameter → 400 response."""
    event = {"queryStringParameters": {"day_phase": "afternoon"}}
    result = handler(event, None)

    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert "error" in body


def test_empty_results(mock_aws):
    """Empty S3 listing → 200 with empty items and total_available=0."""
    mock_s3 = mock_aws["s3"]

    # Empty listing - no Contents key
    pages = [{}]
    mock_s3.get_paginator.return_value = _FakePaginator(pages)

    event = {"queryStringParameters": {}}
    result = handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["total_available"] == 0
    assert body["items"] == []


def test_cap_at_200_items(mock_aws):
    """Large number of annotated objects → response items ≤ 200."""
    mock_s3 = mock_aws["s3"]

    # Create 250 keys
    keys = [f"image_{i:04d}.jpg" for i in range(250)]
    pages = _build_list_pages(keys)
    mock_s3.get_paginator.return_value = _FakePaginator(pages)

    mock_s3.get_object_annotation.return_value = {
        "AnnotationPayload": _make_annotation_value().encode("utf-8"),
    }
    mock_s3.generate_presigned_url.return_value = "https://example.com/presigned"

    event = {"queryStringParameters": {}}
    result = handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert len(body["items"]) <= 200
    assert body["total_available"] == 250
    assert body["offset"] == 0
    assert body["limit"] == 60


def test_offset_pagination(mock_aws):
    """Offset skips earlier items while total_available reflects full result set."""
    mock_s3 = mock_aws["s3"]

    keys = [f"image_{i:04d}.jpg" for i in range(5)]
    pages = _build_list_pages(keys)
    mock_s3.get_paginator.return_value = _FakePaginator(pages)

    def get_annotation_side_effect(**kwargs):
        key = kwargs["Key"]
        index = int(key.split("_")[1].split(".")[0])
        return {
            "AnnotationPayload": _make_annotation_value(
                captured_utc=f"2026-06-18T{index:02d}:00:00Z"
            ).encode("utf-8"),
        }

    mock_s3.get_object_annotation.side_effect = get_annotation_side_effect
    mock_s3.generate_presigned_url.return_value = "https://example.com/presigned"

    event = {"queryStringParameters": {"limit": "2", "offset": "2"}}
    result = handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["total_available"] == 5
    assert body["offset"] == 2
    assert body["limit"] == 2
    assert len(body["items"]) == 2
