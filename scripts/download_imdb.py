#!/usr/bin/env python3
"""
download_imdb.py
Download IMDb non-commercial datasets and extract the TOXIC_2026 record.

Usage:
    python scripts/download_imdb.py
    python scripts/download_imdb.py --force   # re-download even if files exist

IMDb Non-Commercial Datasets licence:
  Personal and non-commercial use only.
  Attribution required: "Information courtesy of IMDb (https://www.imdb.com). Used with permission."
  See: https://developer.imdb.com/non-commercial-datasets/
"""

import sys
import os
import json
import logging
import argparse
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from toxic_pipeline.config import load_config, FILM_ID, IMDB_ID
from toxic_pipeline.imdb import download_imdb_file, extract_film_record
from toxic_pipeline.cleaning import clean_imdb_record
from toxic_pipeline.validation import validate_imdb

import pandas as pd
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/download_imdb.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Download IMDb datasets and extract TOXIC_2026 record.")
    parser.add_argument("--force", action="store_true", help="Re-download even if files already exist.")
    parser.add_argument("--config", default=None, help="Path to settings YAML.")
    args = parser.parse_args()

    config = load_config(args.config)
    imdb_cfg = config.get("imdb", {})
    raw_dir = imdb_cfg.get("raw_dir", "data/raw/imdb")
    staging_dir = imdb_cfg.get("staging_dir", "data/staging/imdb")
    Path(staging_dir).mkdir(parents=True, exist_ok=True)

    logger.info("=== IMDb Download — TOXIC_2026 / %s ===", IMDB_ID)

    # Step 1: Download raw files (skips if already present unless --force)
    basics_path = download_imdb_file("title.basics.tsv.gz", raw_dir, force=args.force)
    ratings_path = download_imdb_file("title.ratings.tsv.gz", raw_dir, force=args.force)

    # Step 2: Stream-extract the target film record
    record = extract_film_record(basics_path, ratings_path, imdb_id=IMDB_ID)
    if not record:
        logger.error(
            "IMDb ID %s was NOT found in title.basics.tsv.gz. "
            "The film may not yet be indexed, or the ID may be wrong. "
            "Verify at https://www.imdb.com/title/%s/",
            IMDB_ID, IMDB_ID,
        )
        sys.exit(1)

    # Step 3: Clean (type conversions, NULL handling)
    record = clean_imdb_record(record)
    logger.info("Extracted and cleaned record: %s", json.dumps(record, default=str, indent=2))

    # Step 4: Validate
    report = validate_imdb(record)
    logger.info(report.summary())
    if report.failed > 0:
        logger.warning("%d validation check(s) failed — review output above.", report.failed)

    # Step 5: Save to staging (JSON + CSV)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_json = Path(staging_dir) / "imdb_toxic_2026.json"
    out_csv  = Path(staging_dir) / "imdb_toxic_2026.csv"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, default=str)
    logger.info("Saved staging JSON: %s", out_json)

    pd.DataFrame([record]).to_csv(out_csv, index=False)
    logger.info("Saved staging CSV:  %s", out_csv)

    # Step 6: Write a collection log entry
    _write_collection_log(
        source="IMDb non-commercial datasets",
        operation="download_and_extract",
        records_collected=1 if record else 0,
        records_failed=0,
        status="success" if record else "failure",
        notes=f"basics={os.path.basename(basics_path)}, ratings={os.path.basename(ratings_path)}",
    )

    logger.info("=== IMDb download complete ===")


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
