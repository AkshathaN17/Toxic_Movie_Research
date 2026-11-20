#!/usr/bin/env python3
"""
clean_critics.py
Clean staged critic review data for TOXIC_2026.

Reads from:  data/staging/critics/critics_manual_entries.csv
Writes to:   data/processed/critics/critics_clean.csv
Appends to:  docs/cleaning_log.md

Raw data is NEVER modified. Cleaning always derives from staging.
"""
import sys
import logging
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from toxic_pipeline.cleaning import clean_critics_df
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/clean_critics.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

STAGING_PATH = Path("data/staging/critics/critics_manual_entries.csv")
PROCESSED_DIR = Path("data/processed/critics")
CLEANING_LOG  = "docs/cleaning_log.md"


def main():
    if not STAGING_PATH.exists():
        logger.warning(
            "No staged critics data at %s. "
            "Run scripts/collect_critics.py first after filling the manual template.",
            STAGING_PATH,
        )
        return

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(STAGING_PATH, dtype=str)
    logger.info("Loaded %d rows from staging.", len(df))

    df_clean = clean_critics_df(df, log_path=CLEANING_LOG)

    out = PROCESSED_DIR / "critics_clean.csv"
    df_clean.to_csv(out, index=False, encoding="utf-8")
    logger.info("Cleaned critics saved → %s  (%d rows)", out, len(df_clean))

    removed = len(df) - len(df_clean)
    logger.info("Rows removed by cleaning: %d", removed)


if __name__ == "__main__":
    main()
