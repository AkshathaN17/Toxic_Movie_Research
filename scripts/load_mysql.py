#!/usr/bin/env python3
"""
load_mysql.py
Load all processed data into the MySQL toxic_case_study database.

Requires environment variables (set in .env):
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

Idempotent: uses INSERT IGNORE to skip existing primary keys.
Historical IMDb snapshots are always appended (never overwritten).
Unverified / ambiguous records are NOT loaded without an explicit match_status.

Usage:
    python scripts/load_mysql.py
    python scripts/load_mysql.py --schema-only   # apply schema without loading data
"""
import sys
import os
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from toxic_pipeline.database import (
    get_engine, run_schema,
    upsert_film, insert_imdb_snapshot,
    insert_critic_reviews, insert_reddit_posts, insert_reddit_comments,
    insert_wikipedia_snapshot,
)

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/load_mysql.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Load processed TOXIC_2026 data into MySQL.")
    parser.add_argument("--schema-only", action="store_true",
                        help="Apply schema.sql only, then exit without loading data.")
    args = parser.parse_args()

    host     = os.environ.get("MYSQL_HOST",     "localhost")
    port     = int(os.environ.get("MYSQL_PORT", 3306))
    user     = os.environ.get("MYSQL_USER")
    password = os.environ.get("MYSQL_PASSWORD")
    database = os.environ.get("MYSQL_DATABASE", "toxic_case_study")

    if not user or not password:
        logger.error(
            "MYSQL_USER and MYSQL_PASSWORD must be set in .env.\n"
            "Copy .env.example to .env and configure your MySQL credentials."
        )
        sys.exit(1)

    logger.info("Connecting to MySQL %s:%s/%s as %s", host, port, database, user)
    engine = get_engine(host, port, user, password, database)

    # Always apply schema (idempotent — IF NOT EXISTS)
    run_schema(engine, "sql/schema.sql")
    logger.info("Schema applied.")

    if args.schema_only:
        logger.info("--schema-only flag set. Exiting after schema application.")
        return

    # ── Canonical film record ─────────────────────────────────────────────────
    upsert_film(engine, {
        "film_id":        "TOXIC_2026",
        "imdb_id":        "tt27530512",
        "canonical_title":"Toxic: A Fairytale for Grown-Ups",
        "primary_title":  None,   # will be updated from IMDb snapshot
        "original_title": None,
        "release_year":   2026,
        "director":       "Geetu Mohandas",
        "starring":       "Yash",
        "genres":         None,
        "runtime_minutes":None,
    })

    # ── IMDb snapshot ─────────────────────────────────────────────────────────
    imdb_path = Path("data/processed/imdb/imdb_toxic_2026_clean.json")
    if imdb_path.exists():
        with open(imdb_path, encoding="utf-8") as f:
            imdb_record = json.load(f)
        insert_imdb_snapshot(engine, imdb_record)
        logger.info("IMDb snapshot loaded.")
    else:
        logger.warning("IMDb processed file not found — skipping snapshot load.")

    # ── Critic reviews ────────────────────────────────────────────────────────
    critics_path = Path("data/processed/critics/critics_clean.csv")
    if critics_path.exists():
        df_critics = pd.read_csv(critics_path)
        # Exclude any ambiguous records
        if "match_status" in df_critics.columns:
            ambiguous = df_critics[df_critics["match_status"] == "ambiguous"]
            if not ambiguous.empty:
                logger.warning(
                    "%d critic records have match_status='ambiguous' and will NOT be loaded. "
                    "Resolve manually and set match_status='verified'.",
                    len(ambiguous),
                )
            df_critics = df_critics[df_critics["match_status"].isin(["verified", ""])]
        inserted, skipped = insert_critic_reviews(engine, df_critics)
        logger.info("Critics: %d inserted, %d skipped (duplicates).", inserted, skipped)
    else:
        logger.warning("Critics processed file not found — skipping.")

    # ── Reddit posts ──────────────────────────────────────────────────────────
    posts_path = Path("data/processed/reddit/reddit_posts_clean.parquet")
    if posts_path.exists():
        df_posts = pd.read_parquet(posts_path)
        insert_reddit_posts(engine, df_posts)
        logger.info("Reddit posts loaded.")
    else:
        logger.warning("Reddit posts processed file not found — skipping.")

    # ── Reddit comments ───────────────────────────────────────────────────────
    comments_path = Path("data/processed/reddit/reddit_comments_clean.parquet")
    if comments_path.exists():
        df_comments = pd.read_parquet(comments_path)
        insert_reddit_comments(engine, df_comments)
        logger.info("Reddit comments loaded.")
    else:
        logger.warning("Reddit comments processed file not found — skipping.")

    # ── Wikipedia snapshot ────────────────────────────────────────────────────
    wiki_path = Path("data/processed/wikipedia/wikipedia_toxic_2026_clean.json")
    if wiki_path.exists():
        with open(wiki_path, encoding="utf-8") as f:
            wiki_record = json.load(f)
        insert_wikipedia_snapshot(engine, wiki_record)
        logger.info("Wikipedia snapshot loaded.")
    else:
        logger.warning("Wikipedia processed file not found — skipping.")

    logger.info("=== Load complete ===")


if __name__ == "__main__":
    main()
