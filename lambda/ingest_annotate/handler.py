"""Ingest Lambda handler – copies GeoNet volcano images and writes S3 Annotations."""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

import boto3
from botocore import UNSIGNED
from botocore.config import Config

from classifier import (
    MODEL_VERSION,
    classify_scene,
    compute_scene_luminance,
    is_jpg_key,
    parse_object_key,
)
from s3_annotations import put_object_annotation

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

GEONET_BUCKET = "geonet-open-data"
SCHEMA_VERSION = "1"


def _utc_day_str(dt: datetime) -> str:
    """Format datetime as YYYY.DDD (day of year)."""
    return f"{dt.strftime('%Y')}.{dt.strftime('%j')}"


def _lookback_utc_days(days: int) -> list[str]:
    """Return UTC day strings for today and the previous (days - 1) days."""
    now = datetime.now(timezone.utc)
    return [_utc_day_str(now - timedelta(days=offset)) for offset in range(days)]


def _build_prefix_for_utc_day(utc_day: str) -> str:
    """Build GeoNet listing prefix for one UTC day folder."""
    year = utc_day.split(".", 1)[0]
    geonet_prefix = os.environ.get("GEONET_PREFIX", "camera/volcano/images")
    camera_path = os.environ.get("CAMERA_PATH", "TKAH/TKAH.01")
    return f"{geonet_prefix}/{year}/{camera_path}/{utc_day}/"


def _build_prefixes(lookback_days: int) -> list[str]:
    """Build listing prefixes for the ingest lookback window."""
    return [_build_prefix_for_utc_day(utc_day) for utc_day in _lookback_utc_days(lookback_days)]


def _list_jpg_keys(unsigned_s3, prefix: str) -> list[str]:
    """Paginated listing of .jpg keys from the GeoNet public bucket."""
    keys: list[str] = []
    paginator = unsigned_s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=GEONET_BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if is_jpg_key(key):
                keys.append(key)
    return keys


def handler(event: dict, context) -> dict:
    """Lambda entry point for the ingest pipeline."""
    private_bucket = os.environ["PRIVATE_BUCKET"]
    annotation_namespace = os.environ.get("ANNOTATION_NAMESPACE", "environment")
    dynamodb_table = os.environ.get("DYNAMODB_TABLE", "")
    local_tz_offset = int(os.environ.get("CAMERA_TZ_OFFSET_HOURS", "12"))

    ingest_run_id = str(uuid.uuid4())
    lookback_days = max(1, int(os.environ.get("INGEST_LOOKBACK_DAYS", "7")))
    utc_days = _lookback_utc_days(lookback_days)
    prefixes = _build_prefixes(lookback_days)

    unsigned_s3 = boto3.client(
        "s3",
        config=Config(signature_version=UNSIGNED),
    )
    s3 = boto3.client("s3")
    dynamodb = boto3.resource("dynamodb") if dynamodb_table else None

    images_copied = 0
    copy_failures = 0
    images_annotated = 0
    annotation_failures = 0

    logger.info(
        "Listing objects in %s for %d UTC day(s): %s",
        GEONET_BUCKET,
        lookback_days,
        ", ".join(utc_days),
    )
    jpg_keys: list[str] = []
    seen_keys: set[str] = set()
    for prefix in prefixes:
        for key in _list_jpg_keys(unsigned_s3, prefix):
            if key not in seen_keys:
                seen_keys.add(key)
                jpg_keys.append(key)
    logger.info("Found %d .jpg objects across lookback window", len(jpg_keys))

    if not jpg_keys:
        logger.info("Zero images found for UTC days %s", utc_days)

    for key in jpg_keys:
        image_bytes = None
        try:
            response = unsigned_s3.get_object(Bucket=GEONET_BUCKET, Key=key)
            image_bytes = response["Body"].read()
            s3.put_object(Bucket=private_bucket, Key=key, Body=image_bytes)
            images_copied += 1
            logger.info("Copied: %s", key)
        except Exception:
            logger.exception("Failed to copy object: %s", key)
            copy_failures += 1
            continue

        parsed = parse_object_key(key)
        if parsed is None:
            logger.warning("Key does not match expected pattern, skipping annotation: %s", key)
            continue

        local_hour = (parsed["hour"] + local_tz_offset) % 24
        try:
            scene_luminance = compute_scene_luminance(image_bytes)
        except Exception:
            logger.exception("Failed to compute luminance for: %s", key)
            scene_luminance = 0.5
        scene = classify_scene(local_hour, scene_luminance)

        now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        annotation_payload = {
            "schema_version": SCHEMA_VERSION,
            "camera_id": parsed["camera_id"],
            "volcano_site": parsed["volcano_site"],
            "utc_day": parsed["utc_day"],
            "captured_utc": parsed["captured_utc"],
            "day_phase": scene["day_phase"],
            "visibility": scene["visibility"],
            "model": MODEL_VERSION,
            "source_bucket": GEONET_BUCKET,
            "source_key": key,
            "ingest_run_id": ingest_run_id,
            "ingested_at": now_ts,
            "updated_at": now_ts,
        }

        try:
            put_object_annotation(
                s3,
                bucket=private_bucket,
                key=key,
                name=annotation_namespace,
                payload=annotation_payload,
            )
            images_annotated += 1
            logger.info("Annotated: %s", key)
        except Exception:
            logger.exception("Failed to write annotation for: %s", key)
            annotation_failures += 1
            continue

        if dynamodb_table and dynamodb:
            try:
                table = dynamodb.Table(dynamodb_table)
                table.put_item(
                    Item={
                        "image_key": key,
                        "captured_utc": parsed["captured_utc"],
                        "utc_day": parsed["utc_day"],
                        "volcano_site": parsed["volcano_site"],
                        "camera_id": parsed["camera_id"],
                        "day_phase": scene["day_phase"],
                        "visibility": scene["visibility"],
                        "ingest_run_id": ingest_run_id,
                        "model": MODEL_VERSION,
                        "updated_at": now_ts,
                    }
                )
                logger.info("DynamoDB mirror written for: %s", key)
            except Exception:
                logger.exception("DynamoDB write failed for: %s", key)

    return {
        "statusCode": 200,
        "body": {
            "images_copied": images_copied,
            "copy_failures": copy_failures,
            "images_annotated": images_annotated,
            "annotation_failures": annotation_failures,
            "lookback_days": lookback_days,
            "utc_days": utc_days,
        },
    }
