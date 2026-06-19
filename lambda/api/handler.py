"""API Lambda handler – queries annotations and returns filtered presigned URLs."""

from __future__ import annotations

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

from validator import validate_params
from s3_annotations import get_object_annotation

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MAX_ITEMS = 200
DEFAULT_LIMIT = 60
ANNOTATION_NAMESPACE = "environment"


def _get_env() -> dict:
    """Read required environment variables."""
    return {
        "private_bucket": os.environ["PRIVATE_BUCKET"],
        "dynamodb_table": os.environ.get("DYNAMODB_TABLE", ""),
        "presign_expiry": int(os.environ.get("PRESIGN_EXPIRY_SECONDS", "900")),
    }


def _build_success_response(
    items: list[dict], total_available: int, offset: int, limit: int
) -> dict:
    """Build a 200 API Gateway response."""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({
            "items": items,
            "total_available": total_available,
            "offset": offset,
            "limit": limit,
        }),
    }


def _build_error_response(status_code: int, message: str) -> dict:
    """Build an error API Gateway response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({"error": message}),
    }


def _matches_filters(tags: dict, filters: dict) -> bool:
    """Check if an annotation object matches all supplied filter criteria."""
    if "day_phase" in filters and tags.get("day_phase") != filters["day_phase"]:
        return False
    if "utc_day" in filters and tags.get("utc_day") != filters["utc_day"]:
        return False
    if "visibility" in filters and tags.get("visibility") != filters["visibility"]:
        return False
    return True


def _fetch_annotation_for_key(s3, bucket: str, key: str) -> dict | None:
    """Fetch a single object annotation."""
    try:
        annotation_value = get_object_annotation(
            s3,
            bucket=bucket,
            key=key,
            name=ANNOTATION_NAMESPACE,
        )
        tags = json.loads(annotation_value)
        return {"key": key, "tags": tags}
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code in ("NoSuchAnnotation", "NoSuchKey", "404"):
            return None
        logger.warning("Failed to get annotation for %s: %s", key, e)
        return None
    except (json.JSONDecodeError, Exception) as e:
        logger.warning("Failed to parse annotation for %s: %s", key, e)
        return None


def _list_bucket_keys(s3, bucket: str) -> list[str]:
    """List object keys in the private bucket, newest first."""
    keys: list[str] = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])
    keys.sort(reverse=True)
    return keys


def _fetch_annotations_for_keys(s3, bucket: str, keys: list[str]) -> list[dict]:
    """Fetch annotations for a specific key list in parallel."""
    if not keys:
        return []

    max_workers = min(int(os.environ.get("ANNOTATION_FETCH_WORKERS", "48")), len(keys))
    results: list[dict] = []
    chunk_size = max_workers * 2

    for idx in range(0, len(keys), chunk_size):
        batch = keys[idx: idx + chunk_size]
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(_fetch_annotation_for_key, s3, bucket, key) for key in batch
            ]
            for future in as_completed(futures):
                item = future.result()
                if item is not None:
                    results.append(item)

    return results


def _query_annotations(
    s3, bucket: str, filters: dict, offset: int, limit: int
) -> tuple[list[dict], int]:
    """List objects and retrieve annotations for the requested page.

    Without filters, only annotations for the current page are fetched so the
    API stays within API Gateway's 30s integration timeout. With filters, all
    annotations are scanned to compute an accurate total_available count.
    """
    keys = _list_bucket_keys(s3, bucket)
    if not keys:
        return [], 0

    if not filters:
        total_available = len(keys)
        page_keys = keys[offset: offset + limit]
        page_items = _fetch_annotations_for_keys(s3, bucket, page_keys)
        page_items.sort(key=lambda i: i["tags"].get("captured_utc", ""), reverse=True)
        return page_items, total_available

    max_workers = min(int(os.environ.get("ANNOTATION_FETCH_WORKERS", "48")), len(keys))
    chunk_size = max_workers * 2
    matches: list[dict] = []

    for idx in range(0, len(keys), chunk_size):
        batch = keys[idx: idx + chunk_size]
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(_fetch_annotation_for_key, s3, bucket, key) for key in batch
            ]
            for future in as_completed(futures):
                item = future.result()
                if item is not None and _matches_filters(item["tags"], filters):
                    matches.append(item)

    matches.sort(key=lambda i: i["tags"].get("captured_utc", ""), reverse=True)
    return matches[offset: offset + limit], len(matches)


def _query_dynamodb(table_name: str) -> list[dict]:
    """Scan DynamoDB table for all annotation items.

    Returns a list of dicts with 'key' and 'tags' for each item.
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)
    results: list[dict] = []

    scan_kwargs: dict = {}
    while True:
        response = table.scan(**scan_kwargs)
        for item in response.get("Items", []):
            key = item.get("image_key", "")
            # Convert Decimal types from DynamoDB to float
            tags = {}
            for k, v in item.items():
                if k == "image_key":
                    continue
                if isinstance(v, Decimal):
                    tags[k] = float(v)
                else:
                    tags[k] = v
            results.append({"key": key, "tags": tags})

        # Handle pagination
        if "LastEvaluatedKey" in response:
            scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
        else:
            break

    return results


def _generate_presigned_url(s3, bucket: str, key: str, expiry: int) -> str | None:
    """Generate a presigned GET URL for an S3 object."""
    try:
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expiry,
        )
        return url
    except Exception:
        logger.exception("Failed to generate presigned URL for: %s", key)
        return None


def handler(event: dict, context) -> dict:
    """Lambda entry point for the API query endpoint."""
    try:
        env = _get_env()
    except KeyError as e:
        logger.error("Missing environment variable: %s", e)
        return _build_error_response(500, "Internal configuration error")

    # --- Parse and validate query parameters ---
    params = event.get("queryStringParameters", {}) or {}
    validated, error_msg = validate_params(params)

    if error_msg:
        return _build_error_response(400, error_msg)

    # --- Query annotations or DynamoDB ---
    s3 = boto3.client("s3")

    offset = validated.get("offset", 0)
    limit = min(validated.get("limit", DEFAULT_LIMIT), MAX_ITEMS)
    filter_criteria = {
        key: value for key, value in validated.items() if key not in {"offset", "limit"}
    }

    try:
        if env["dynamodb_table"]:
            all_items = _query_dynamodb(env["dynamodb_table"])
            filtered_items = [
                item for item in all_items if _matches_filters(item["tags"], filter_criteria)
            ]
            filtered_items.sort(key=lambda i: i["tags"].get("captured_utc", ""), reverse=True)
            total_available = len(filtered_items)
            page_items = filtered_items[offset: offset + limit]
        else:
            page_items, total_available = _query_annotations(
                s3, env["private_bucket"], filter_criteria, offset, limit
            )
    except Exception:
        logger.exception("Failed to query image metadata")
        return _build_error_response(500, "Failed to retrieve image data")

    # --- Generate presigned URLs ---
    response_items: list[dict] = []
    for item in page_items:
        url = _generate_presigned_url(
            s3, env["private_bucket"], item["key"], env["presign_expiry"]
        )
        if url is None:
            # Skip items where presigned URL generation fails
            continue
        response_items.append({
            "key": item["key"],
            "tags": item["tags"],
            "image_url": url,
        })

    return _build_success_response(response_items, total_available, offset, limit)
