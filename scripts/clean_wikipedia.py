#!/usr/bin/env python3
"""
clean_wikipedia.py
Clean staged Wikipedia movie record for TOXIC_2026.

Reads from:  data/staging/wikipedia/wikipedia_toxic_2026.json
Writes to:   data/processed/wikipedia/wikipedia_toxic_2026_clean.json
             data/processed/wikipedia/wikipedia_toxic_2026_clean.csv
Appends to:  docs/cleaning_log.md
"""
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from toxic_pipeline.wikipedia import clean_wikipedia_record
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/clean_wikipedia.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

STAGING_PATH = Path("data/staging/wikipedia/wikipedia_toxic_2026.json")
PROCESSED_DIR = Path("data/processed/wikipedia")
CLEANING_LOG = "docs/cleaning_log.md"


def main():
    if not STAGING_PATH.exists():
        logger.error("No staged Wikipedia data at %s. Run scripts/collect_wikipedia.py first.", STAGING_PATH)
        return

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    with open(STAGING_PATH, encoding="utf-8") as f:
        record = json.load(f)
    logger.info("Loaded staging record for page: %s (page_id: %s)", record.get("page_title"), record.get("page_id"))

    # Clean and normalize
    cleaned = clean_wikipedia_record(record)

    out_json = PROCESSED_DIR / "wikipedia_toxic_2026_clean.json"
    out_csv = PROCESSED_DIR / "wikipedia_toxic_2026_clean.csv"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)
    logger.info("Cleaned Wikipedia JSON saved → %s", out_json)

    pd.DataFrame([cleaned]).to_csv(out_csv, index=False, encoding="utf-8")
    logger.info("Cleaned Wikipedia CSV saved  → %s", out_csv)

    # Append to cleaning log
    _append_cleaning_log(cleaned)


def _append_cleaning_log(record):
    log_path = Path(CLEANING_LOG)
    ts = datetime.now(timezone.utc).isoformat()
    entry = (
        f"\n## Cleaning run — wikipedia — {ts}\n"
        f"- page_id: {record.get('page_id')} (verified integer)\n"
        f"- revision_id: {record.get('revision_id')}\n"
        f"- full_extract length: {len(record.get('full_extract', ''))} characters\n"
        f"- reception_text present: {bool(record.get('reception_text'))}\n"
        f"- critical_response_text present: {bool(record.get('critical_response_text'))}\n"
        f"- Input: 1 record | Output: 1 record | Removed: 0\n"
    )
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)
    logger.info("Appended Wikipedia cleaning run to %s", log_path)


if __name__ == "__main__":
    main()
