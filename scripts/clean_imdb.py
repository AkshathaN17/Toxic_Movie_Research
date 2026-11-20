#!/usr/bin/env python3
"""
clean_imdb.py
Clean staged IMDb record for TOXIC_2026.

Reads from:  data/staging/imdb/imdb_toxic_2026.json
Writes to:   data/processed/imdb/imdb_toxic_2026_clean.json
             data/processed/imdb/imdb_toxic_2026_clean.csv
"""
import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from toxic_pipeline.cleaning import clean_imdb_record
from toxic_pipeline.validation import validate_imdb
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/clean_imdb.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

STAGING_PATH  = Path("data/staging/imdb/imdb_toxic_2026.json")
PROCESSED_DIR = Path("data/processed/imdb")


def main():
    if not STAGING_PATH.exists():
        logger.error(
            "No staged IMDb data at %s. Run scripts/download_imdb.py first.",
            STAGING_PATH,
        )
        return

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    with open(STAGING_PATH, encoding="utf-8") as f:
        record = json.load(f)
    logger.info("Loaded staging record for IMDb ID: %s", record.get("imdb_id"))

    # Type conversions and NULL normalisation
    record = clean_imdb_record(record)

    # Validate after cleaning
    report = validate_imdb(record)
    logger.info(report.summary())

    out_json = PROCESSED_DIR / "imdb_toxic_2026_clean.json"
    out_csv  = PROCESSED_DIR / "imdb_toxic_2026_clean.csv"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, default=str)
    logger.info("Cleaned record → %s", out_json)

    pd.DataFrame([record]).to_csv(out_csv, index=False)
    logger.info("Cleaned record → %s", out_csv)


if __name__ == "__main__":
    main()
