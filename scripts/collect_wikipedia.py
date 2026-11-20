#!/usr/bin/env python3
"""
collect_wikipedia.py
Collect semi-structured movie article data via the Wikipedia Action API.

Queries: https://en.wikipedia.org/w/api.php
Article: Toxic_(2026_film)
Returns: Native JSON payload (no authentication or API key required).

Preserves:
  1. Raw JSON:     data/raw/wikipedia/wikipedia_toxic_2026_raw.json
  2. Staging JSON: data/staging/wikipedia/wikipedia_toxic_2026.json
  3. Staging CSV:  data/staging/wikipedia/wikipedia_toxic_2026.csv
  4. Audit Log:    logs/collection_log.csv
"""
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toxic_pipeline.config import FILM_ID
from toxic_pipeline.wikipedia import (
    fetch_wikipedia_page,
    extract_wikipedia_record,
    DEFAULT_PAGE_TITLE,
)
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/collect_wikipedia.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def main():
    raw_dir = Path("data/raw/wikipedia")
    staging_dir = Path("data/staging/wikipedia")
    raw_dir.mkdir(parents=True, exist_ok=True)
    staging_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=== Wikipedia Action API Collection — %s ===", DEFAULT_PAGE_TITLE)

    # 1. Fetch raw JSON from Wikipedia Action API
    try:
        raw_json = fetch_wikipedia_page()
    except Exception as e:
        logger.error("Failed to query Wikipedia Action API: %s", e)
        _write_collection_log("wikipedia_action_api", "fetch", 0, 1, "error", str(e))
        sys.exit(1)

    # 2. Preserve raw JSON immutably
    raw_json_path = raw_dir / "wikipedia_toxic_2026_raw.json"
    with open(raw_json_path, "w", encoding="utf-8") as f:
        json.dump(raw_json, f, indent=2, ensure_ascii=False)
    logger.info("Preserved raw API JSON → %s (%d bytes)", raw_json_path, raw_json_path.stat().st_size)

    # 3. Extract structured record
    try:
        record = extract_wikipedia_record(raw_json, film_id=FILM_ID)
    except Exception as e:
        logger.error("Failed to extract Wikipedia record: %s", e)
        _write_collection_log("wikipedia_action_api", "extract", 0, 1, "error", str(e))
        sys.exit(1)

    logger.info("Extracted page '%s' (PageID: %s, RevID: %s)",
                record["page_title"], record["page_id"], record["revision_id"])

    # 4. Save to staging (JSON + CSV)
    out_json = staging_dir / "wikipedia_toxic_2026.json"
    out_csv = staging_dir / "wikipedia_toxic_2026.csv"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    logger.info("Saved staging JSON → %s", out_json)

    pd.DataFrame([record]).to_csv(out_csv, index=False, encoding="utf-8")
    logger.info("Saved staging CSV  → %s", out_csv)

    # 5. Log collection operation
    _write_collection_log(
        source="Wikipedia Action API",
        operation="fetch_and_extract",
        records_collected=1,
        records_failed=0,
        status="success",
        notes=f"page_id={record['page_id']}, rev_id={record['revision_id']}, title={record['page_title']}",
    )
    logger.info("=== Wikipedia collection complete ===")


def _write_collection_log(source, operation, records_collected, records_failed, status, notes=""):
    log_path = Path("logs") / "collection_log.csv"
    write_header = not log_path.exists()
    with open(log_path, "a", encoding="utf-8", newline="") as f:
        import csv
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["timestamp", "source", "operation", "records_collected",
                             "records_failed", "status", "notes"])
        writer.writerow([
            datetime.now(timezone.utc).isoformat(), source, operation,
            records_collected, records_failed, status, notes,
        ])


if __name__ == "__main__":
    main()
