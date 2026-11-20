#!/usr/bin/env python3
"""
collect_reddit.py
Reddit data collection for TOXIC_2026 via official PRAW OAuth2 API.

ACCESS REQUIREMENTS (must be completed before running):
  1. Register a Reddit developer application at https://www.reddit.com/prefs/apps
     Choose "script" type for personal/academic non-commercial use.
  2. Copy .env.example to .env and populate:
         REDDIT_CLIENT_ID=<your app client_id>
         REDDIT_CLIENT_SECRET=<your app secret>
         REDDIT_USER_AGENT=ToxicMovieResearch/1.0 by <YourRedditUsername>
  3. In config/settings.yaml set:  reddit.enabled: true
  4. Re-run this script.

If credentials are absent or reddit.enabled is false the script exits with
a clear error message and writes status "disabled" to the collection log.
It never substitutes mock data or another data source.

API policy notes (as of 2026):
  - Reddit API v2 requires OAuth2 for all meaningful access.
  - Rate limit: 100 QPM for authenticated free tier.
  - Pushshift is SHUT DOWN for public/academic use (closed ~mid-2023).
  - Permitted library: PRAW (python-praw) in read_only mode.
  - Personal data: author usernames are NOT collected; only content IDs,
    text, timestamps, scores, and subreddit names are retained.

Usage:
    python scripts/collect_reddit.py
    python scripts/collect_reddit.py --dry-run   # check credentials only
"""

import sys
import logging
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from toxic_pipeline.config import load_config
from toxic_pipeline.reddit import collect_reddit, check_reddit_access

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/collect_reddit.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Collect Reddit data for TOXIC_2026 via PRAW OAuth.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Check credentials and config only; do not collect.")
    parser.add_argument("--config", default=None, help="Path to settings YAML.")
    args = parser.parse_args()

    config = load_config(args.config)
    reddit_cfg  = config.get("reddit", {})
    raw_dir     = reddit_cfg.get("raw_dir",      "data/raw/reddit")
    staging_dir = reddit_cfg.get("staging_dir",  "data/staging/reddit")
    delay       = reddit_cfg.get("request_delay_seconds", 2.0)

    Path(staging_dir).mkdir(parents=True, exist_ok=True)

    # Credential / config gate
    if not check_reddit_access():
        logger.error(
            "Reddit collection BLOCKED.\n"
            "  Missing environment variables — set them in .env (see .env.example).\n"
            "  Then set reddit.enabled: true in config/settings.yaml.\n"
            "  Then register a Reddit developer app at https://www.reddit.com/prefs/apps\n"
            "  This script will NOT substitute mock data."
        )
        _write_collection_log("reddit_praw", "credential_check", 0, 0, "disabled",
                               "OAuth credentials not configured.")
        sys.exit(1)

    if not reddit_cfg.get("enabled", False):
        logger.warning(
            "Reddit collection is disabled in config (reddit.enabled=false). "
            "Set reddit.enabled: true in config/settings.yaml after configuring credentials."
        )
        _write_collection_log("reddit_praw", "credential_check", 0, 0, "disabled",
                               "reddit.enabled=false in config.")
        sys.exit(0)

    if args.dry_run:
        logger.info("Dry-run: credentials present, config enabled — ready to collect.")
        sys.exit(0)

    logger.info("=== Reddit Collection — TOXIC_2026 ===")
    result = collect_reddit(config, raw_dir, delay=delay)

    if result["status"] == "error":
        logger.error("Collection error: %s", result.get("message"))
        _write_collection_log("reddit_praw", "collect", 0, 0, "error", result.get("message"))
        sys.exit(1)

    posts    = result["posts"]
    comments = result["comments"]
    logger.info("Collected %d posts, %d comments", len(posts), len(comments))

    # Stage
    if posts:
        df_posts = pd.DataFrame(posts)
        out_posts = Path(staging_dir) / "reddit_posts_staging.csv"
        df_posts.to_csv(out_posts, index=False, encoding="utf-8")
        logger.info("Staged posts → %s", out_posts)

    if comments:
        df_comments = pd.DataFrame(comments)
        out_comments = Path(staging_dir) / "reddit_comments_staging.csv"
        df_comments.to_csv(out_comments, index=False, encoding="utf-8")
        logger.info("Staged comments → %s", out_comments)

    _write_collection_log("reddit_praw", "collect", len(posts), 0, "success",
                           f"{len(posts)} posts, {len(comments)} comments staged.")


def _write_collection_log(source, operation, records_collected, records_failed, status, notes=""):
    log_path = Path("logs") / "collection_log.csv"
    write_header = not log_path.exists()
    with open(log_path, "a", encoding="utf-8", newline="") as f:
        import csv
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["timestamp", "source", "operation", "records_collected",
                             "records_failed", "status", "notes"])
        writer.writerow([datetime.now(timezone.utc).isoformat(), source, operation,
                         records_collected, records_failed, status, notes])


if __name__ == "__main__":
    main()
