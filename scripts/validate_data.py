#!/usr/bin/env python3
"""
validate_data.py
Run all structural, identity, duplicate, and type-safety checks on processed data.
Writes docs/data_quality_report.md.

Exit code 0 = all checks passed.
Exit code 1 = one or more checks failed (see report).

This script does NOT claim data is complete; it only checks what has been
processed.  Missing-data sections are reported as "No processed data found."
"""
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from toxic_pipeline.validation import validate_critics, validate_imdb, validate_reddit, validate_wikipedia
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/validate_data.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

REPORT_PATH = Path("docs/data_quality_report.md")


def main():
    overall_pass = overall_fail = 0
    sections = []

    header = (
        "# Data Quality Report — Toxic 2026 Movie Data Pipeline\n\n"
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}  \n"
        "**Film:** Toxic: A Fairytale for Grown-Ups  \n"
        "**IMDb ID:** tt27530512  \n"
        "**Project ID:** TOXIC_2026\n\n"
        "---\n"
    )

    # ── Critics ──────────────────────────────────────────────────────────────
    critics_path = Path("data/processed/critics/critics_clean.csv")
    if critics_path.exists():
        df = pd.read_csv(critics_path, dtype=str)
        r  = validate_critics(df)
        overall_pass += r.passed
        overall_fail += r.failed
        sections.append(f"## Critics\n\n**File:** `{critics_path}`  \n"
                        f"**Rows:** {len(df)}\n\n```\n{r.summary()}\n```\n")
        logger.info("[Critics] %s", r.summary())
    else:
        sections.append(
            "## Critics\n\nNo processed data found at `data/processed/critics/critics_clean.csv`.\n"
            "Run `scripts/collect_critics.py` and `scripts/clean_critics.py` first.\n"
        )
        logger.warning("Critics processed data not found.")

    # ── IMDb ─────────────────────────────────────────────────────────────────
    imdb_path = Path("data/processed/imdb/imdb_toxic_2026_clean.json")
    if imdb_path.exists():
        with open(imdb_path, encoding="utf-8") as f:
            record = json.load(f)
        r = validate_imdb(record)
        overall_pass += r.passed
        overall_fail += r.failed
        avg = record.get("average_rating", "N/A")
        votes = record.get("num_votes", "N/A")
        sections.append(f"## IMDb\n\n**File:** `{imdb_path}`  \n"
                        f"**averageRating:** {avg}  \n"
                        f"**numVotes:** {votes}\n\n```\n{r.summary()}\n```\n")
        logger.info("[IMDb] %s", r.summary())
    else:
        sections.append(
            "## IMDb\n\nNo processed data found at `data/processed/imdb/imdb_toxic_2026_clean.json`.\n"
            "Run `scripts/download_imdb.py` and `scripts/clean_imdb.py` first.\n"
        )
        logger.warning("IMDb processed data not found.")

    # ── Reddit ────────────────────────────────────────────────────────────────
    posts_path    = Path("data/processed/reddit/reddit_posts_clean.parquet")
    comments_path = Path("data/processed/reddit/reddit_comments_clean.parquet")
    if posts_path.exists() or comments_path.exists():
        posts_df    = pd.read_parquet(posts_path)    if posts_path.exists()    else pd.DataFrame()
        comments_df = pd.read_parquet(comments_path) if comments_path.exists() else pd.DataFrame()
        r = validate_reddit(posts_df, comments_df)
        overall_pass += r.passed
        overall_fail += r.failed
        sections.append(f"## Reddit\n\n**Posts:** {len(posts_df)}  \n"
                        f"**Comments:** {len(comments_df)}\n\n```\n{r.summary()}\n```\n")
        logger.info("[Reddit] %s", r.summary())
    else:
        sections.append(
            "## Reddit\n\nNo processed data found.\n"
            "Reddit collection requires OAuth credentials — see `.env.example`.\n"
            "Run `scripts/collect_reddit.py` and `scripts/clean_reddit.py` once configured.\n"
        )
        logger.warning("Reddit processed data not found.")

    # ── Wikipedia ─────────────────────────────────────────────────────────────
    wiki_path = Path("data/processed/wikipedia/wikipedia_toxic_2026_clean.json")
    if wiki_path.exists():
        with open(wiki_path, encoding="utf-8") as f:
            wiki_record = json.load(f)
        r = validate_wikipedia(wiki_record)
        overall_pass += r.passed
        overall_fail += r.failed
        sections.append(f"## Wikipedia Action API\n\n**File:** `{wiki_path}`  \n"
                        f"**Page ID:** {wiki_record.get('page_id')}  \n"
                        f"**Title:** {wiki_record.get('page_title')}  \n"
                        f"**Revision ID:** {wiki_record.get('revision_id')}\n\n```\n{r.summary()}\n```\n")
        logger.info("[Wikipedia] %s", r.summary())
    else:
        sections.append(
            "## Wikipedia Action API\n\nNo processed data found at `data/processed/wikipedia/wikipedia_toxic_2026_clean.json`.\n"
            "Run `scripts/collect_wikipedia.py` and `scripts/clean_wikipedia.py` first.\n"
        )
        logger.warning("Wikipedia processed data not found.")

    # ── Summary ───────────────────────────────────────────────────────────────
    summary = (
        f"---\n\n## Summary\n\n"
        f"| Metric | Value |\n|---|---|\n"
        f"| Checks passed | {overall_pass} |\n"
        f"| Checks failed | {overall_fail} |\n"
        f"| Report generated | {datetime.now(timezone.utc).isoformat()} |\n"
    )

    report_text = header + "\n".join(sections) + "\n" + summary
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report_text, encoding="utf-8")
    logger.info("Data quality report written → %s", REPORT_PATH)
    logger.info("Overall: %d passed, %d failed", overall_pass, overall_fail)

    if overall_fail > 0:
        logger.error("%d check(s) FAILED — review the report at %s", overall_fail, REPORT_PATH)
        sys.exit(1)


if __name__ == "__main__":
    main()
