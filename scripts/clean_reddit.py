#!/usr/bin/env python3
"""
clean_reddit.py
Clean staged Reddit posts and comments for TOXIC_2026.

Reads from:  data/staging/reddit/reddit_posts_staging.csv
             data/staging/reddit/reddit_comments_staging.csv
Writes to:   data/processed/reddit/reddit_posts_clean.parquet
             data/processed/reddit/reddit_comments_clean.parquet
Appends to:  docs/cleaning_log.md

Parquet is used for Reddit (text-heavy) per the data format specification.
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from toxic_pipeline.cleaning import clean_reddit_df
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/clean_reddit.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

STAGING_DIR   = Path("data/staging/reddit")
PROCESSED_DIR = Path("data/processed/reddit")
CLEANING_LOG  = "docs/cleaning_log.md"


def main():
    posts_path    = STAGING_DIR / "reddit_posts_staging.csv"
    comments_path = STAGING_DIR / "reddit_comments_staging.csv"

    posts_df    = pd.read_csv(posts_path,    dtype=str) if posts_path.exists()    else pd.DataFrame()
    comments_df = pd.read_csv(comments_path, dtype=str) if comments_path.exists() else pd.DataFrame()

    if posts_df.empty and comments_df.empty:
        logger.warning(
            "No staged Reddit data found. "
            "Run scripts/collect_reddit.py after configuring OAuth credentials."
        )
        return

    logger.info("Loaded %d posts, %d comments from staging.", len(posts_df), len(comments_df))
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    posts_clean, comments_clean = clean_reddit_df(posts_df, comments_df, log_path=CLEANING_LOG)

    if not posts_clean.empty:
        out = PROCESSED_DIR / "reddit_posts_clean.parquet"
        posts_clean.to_parquet(out, index=False, engine="pyarrow")
        logger.info("Cleaned posts → %s  (%d rows)", out, len(posts_clean))

    if not comments_clean.empty:
        out = PROCESSED_DIR / "reddit_comments_clean.parquet"
        comments_clean.to_parquet(out, index=False, engine="pyarrow")
        logger.info("Cleaned comments → %s  (%d rows)", out, len(comments_clean))

    logger.info(
        "Rows removed — posts: %d, comments: %d",
        len(posts_df) - len(posts_clean),
        len(comments_df) - len(comments_clean),
    )


if __name__ == "__main__":
    main()
