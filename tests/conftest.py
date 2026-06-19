"""Pytest configuration — adds lambda/ to the import path."""

import sys
from pathlib import Path

# The lambda/ directory contains two packages: ingest_annotate/ and api/
# Each package uses bare imports internally (e.g. `from classifier import ...`).
# We add lambda/ for package-level imports (ingest_annotate.handler, api.handler)
# and also each subdirectory so bare imports within packages resolve.
lambda_dir = Path(__file__).resolve().parent.parent / "lambda"

for p in [
    str(lambda_dir),
    str(lambda_dir / "ingest_annotate"),
    str(lambda_dir / "api"),
    str(lambda_dir / "shared"),
]:
    if p not in sys.path:
        sys.path.insert(0, p)
