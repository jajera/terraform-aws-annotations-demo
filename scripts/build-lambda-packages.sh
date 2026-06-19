#!/usr/bin/env bash
# Build Lambda deployment zips with application code + pinned boto3 (S3 Annotations API).
# When invoked by Terraform external data source, reads JSON query on stdin and
# prints JSON with base64 SHA256 hashes of each zip.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_ROOT="${ROOT}/terraform/.build"
REQ="${ROOT}/lambda/requirements.txt"
PIP="${PIP:-pip3}"
CACHE_HASH_FILE="${BUILD_ROOT}/.source-hash"

read_query_hash() {
  if [[ -t 0 ]]; then
    echo ""
    return
  fi
  # Non-TTY stdin with no piped data (e.g. IDE shells) must not block forever.
  python3 - <<'PY' 2>/dev/null || echo ""
import json
import select
import sys

if not select.select([sys.stdin], [], [], 0)[0]:
    print("")
else:
    print(json.load(sys.stdin).get("source_hash", ""))
PY
}

SOURCE_HASH="$(read_query_hash)"

zip_b64_sha256() {
  python3 -c "import base64,hashlib,sys; print(base64.b64encode(hashlib.sha256(open(sys.argv[1],'rb').read()).digest()).decode())" "$1"
}

build_module() {
  local module="$1"
  local src_dir="${ROOT}/lambda/${module}"
  local pkg_dir="${BUILD_ROOT}/${module}_pkg"
  local zip_path="${BUILD_ROOT}/${module}.zip"

  rm -rf "${pkg_dir}"
  mkdir -p "${pkg_dir}"

  cp "${src_dir}"/*.py "${pkg_dir}/"
  cp "${ROOT}/lambda/shared/s3_annotations.py" "${pkg_dir}/"

  "${PIP}" install -r "${REQ}" -t "${pkg_dir}" --upgrade --quiet \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.14 \
    --only-binary=:all:

  rm -f "${zip_path}"
  (cd "${pkg_dir}" && zip -qr "${zip_path}" .)
}

should_build=true
if [[ -n "${SOURCE_HASH}" && -f "${BUILD_ROOT}/ingest_annotate.zip" && -f "${BUILD_ROOT}/api.zip" ]]; then
  if [[ -f "${CACHE_HASH_FILE}" && "$(cat "${CACHE_HASH_FILE}")" == "${SOURCE_HASH}" ]]; then
    should_build=false
  fi
fi

if [[ "${should_build}" == true ]]; then
  mkdir -p "${BUILD_ROOT}"
  build_module ingest_annotate
  build_module api
  if [[ -n "${SOURCE_HASH}" ]]; then
    echo "${SOURCE_HASH}" > "${CACHE_HASH_FILE}"
  fi
fi

INGEST_HASH="$(zip_b64_sha256 "${BUILD_ROOT}/ingest_annotate.zip")"
API_HASH="$(zip_b64_sha256 "${BUILD_ROOT}/api.zip")"

python3 - <<PY
import json
print(json.dumps({
    "ingest_hash": "${INGEST_HASH}",
    "api_hash": "${API_HASH}",
}))
PY
