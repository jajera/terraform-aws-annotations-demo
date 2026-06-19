"""Integration tests for ingest_annotate/handler.py with mocked AWS SDK calls."""

from unittest.mock import MagicMock, patch

import pytest

from ingest_annotate.handler import handler


INGEST_ENV = {
    "PRIVATE_BUCKET": "test-private-bucket",
    "GEONET_PREFIX": "camera/volcano/images",
    "CAMERA_PATH": "TKAH/TKAH.01",
    "DYNAMODB_TABLE": "",
    "ANNOTATION_NAMESPACE": "environment",
    "INGEST_LOOKBACK_DAYS": "7",
}

VALID_KEY_1 = "camera/volcano/images/2026/TKAH/TKAH.01/2026.169/2026.169.0800.00.TKAH.01.0.jpg"
VALID_KEY_2 = "camera/volcano/images/2026/TKAH/TKAH.01/2026.169/2026.169.1000.00.TKAH.01.0.jpg"
NON_MATCHING_KEY = "camera/volcano/images/2026/TKAH/TKAH.01/2026.169/2026.169.0800.00.TKAH.02.0.jpg"


def _build_list_pages(keys):
    if not keys:
        return [{}]
    return [{"Contents": [{"Key": k} for k in keys]}]


class _FakePaginator:
    def __init__(self, pages):
        self._pages = pages

    def paginate(self, **kwargs):
        return iter(self._pages)


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    for key, value in INGEST_ENV.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def mock_aws():
    mock_unsigned_s3 = MagicMock()
    mock_s3 = MagicMock()

    def client_factory(service, **kwargs):
        if service == "s3" and "config" in kwargs:
            return mock_unsigned_s3
        if service == "s3":
            return mock_s3
        return MagicMock()

    with patch("ingest_annotate.handler.boto3") as patched_boto3:
        patched_boto3.client.side_effect = client_factory
        patched_boto3.resource.return_value = None
        yield {
            "unsigned_s3": mock_unsigned_s3,
            "s3": mock_s3,
        }


def test_successful_ingest(mock_aws):
    mock_unsigned_s3 = mock_aws["unsigned_s3"]
    mock_s3 = mock_aws["s3"]

    pages = _build_list_pages([VALID_KEY_1, VALID_KEY_2])
    mock_unsigned_s3.get_paginator.return_value = _FakePaginator(pages)
    mock_unsigned_s3.get_object.return_value = {"Body": MagicMock(read=lambda: b"\xff\xd8\xff\xe0")}
    mock_s3.put_object.return_value = {}
    mock_s3.put_object_annotation.return_value = {}

    result = handler({}, None)

    assert result["statusCode"] == 200
    body = result["body"]
    assert body["images_copied"] == 2
    assert body["images_annotated"] == 2
    assert body["copy_failures"] == 0
    assert body["annotation_failures"] == 0


def test_empty_listing(mock_aws):
    mock_unsigned_s3 = mock_aws["unsigned_s3"]
    pages = [{}]
    mock_unsigned_s3.get_paginator.return_value = _FakePaginator(pages)

    result = handler({}, None)

    assert result["statusCode"] == 200
    body = result["body"]
    assert body["images_copied"] == 0
    assert body["images_annotated"] == 0


def test_copy_failure_for_one_image(mock_aws):
    mock_unsigned_s3 = mock_aws["unsigned_s3"]
    mock_s3 = mock_aws["s3"]

    pages = _build_list_pages([VALID_KEY_1, VALID_KEY_2])
    mock_unsigned_s3.get_paginator.return_value = _FakePaginator(pages)

    call_count = {"n": 0}

    def get_object_side_effect(**kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise Exception("Simulated S3 GetObject failure")
        return {"Body": MagicMock(read=lambda: b"\xff\xd8\xff\xe0")}

    mock_unsigned_s3.get_object.side_effect = get_object_side_effect
    mock_s3.put_object.return_value = {}
    mock_s3.put_object_annotation.return_value = {}

    result = handler({}, None)

    assert result["statusCode"] == 200
    body = result["body"]
    assert body["copy_failures"] == 1
    assert body["images_copied"] == 1
    assert body["images_annotated"] == 1


def test_non_matching_key(mock_aws):
    mock_unsigned_s3 = mock_aws["unsigned_s3"]
    mock_s3 = mock_aws["s3"]

    pages = _build_list_pages([NON_MATCHING_KEY])
    mock_unsigned_s3.get_paginator.return_value = _FakePaginator(pages)
    mock_unsigned_s3.get_object.return_value = {"Body": MagicMock(read=lambda: b"\xff\xd8\xff\xe0")}
    mock_s3.put_object.return_value = {}

    result = handler({}, None)

    assert result["statusCode"] == 200
    body = result["body"]
    assert body["images_copied"] == 1
    assert body["images_annotated"] == 0
