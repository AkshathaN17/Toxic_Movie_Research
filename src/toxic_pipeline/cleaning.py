"""Data cleaning utilities for the Toxic 2026 pipeline."""
import re
import logging
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def normalize_whitespace(text: str) -> str:
    if not isinstance(text, str):
        return text
    return re.sub(r"\s+", " ", text.strip())


def clean_critics_df(df: pd.DataFrame, log_path: str = None) -> pd.DataFrame:
    """Clean critic reviews DataFrame. Preserves raw data, documents all removals."""
    log_entries = []
    original_count = len(df)

    # Normalize whitespace in text fields
    for col in ["review_text", "critic_name", "publication"]:
        if col in df.columns:
            df[col] = df[col].apply(normalize_whitespace)

    # Convert review_date
    if "review_date" in df.columns:
        df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")
        null_dates = df["review_date"].isna().sum()
        if null_dates > 0:
            log_entries.append(
                f"review_date: {null_dates} could not be parsed, preserved as NaT"
            )

    # Normalize ratings only where scale is known
    if "rating_normalized" in df.columns and "rating_scale" in df.columns:
        missing_norm = df["rating_normalized"].isna().sum()
        log_entries.append(
            f"rating_normalized: {missing_norm} null values preserved as NULL"
        )

    # Deduplication: by review_url (primary), then by critic_name + publication + review_date
    before_dedup = len(df)
    if "review_url" in df.columns:
        df = df.drop_duplicates(subset=["review_url"], keep="first")
    after_url_dedup = len(df)
    removed_url = before_dedup - after_url_dedup
    if removed_url > 0:
        log_entries.append(f"Removed {removed_url} duplicates by review_url")

    if "critic_name" in df.columns and "publication" in df.columns:
        df = df.drop_duplicates(
            subset=["critic_name", "publication", "review_date"], keep="first"
        )
    after_dedup = len(df)
    removed_name_pub = after_url_dedup - after_dedup
    if removed_name_pub > 0:
        log_entries.append(
            f"Removed {removed_name_pub} duplicates by critic_name+publication+review_date"
        )

    final_count = len(df)
    log_entries.append(
        f"Input: {original_count} rows | Output: {final_count} rows | Removed: {original_count - final_count}"
    )

    if log_path:
        _write_log(log_path, "critics", log_entries)

    return df


def clean_imdb_record(record: dict) -> dict:
    """Type-convert and validate a single IMDb record."""
    cleaned = dict(record)
    # Average rating: float
    try:
        cleaned["average_rating"] = (
            float(cleaned["average_rating"])
            if cleaned.get("average_rating") not in (None, "\\N", "")
            else None
        )
    except (ValueError, TypeError):
        cleaned["average_rating"] = None
        logger.warning(
            "Could not convert average_rating to float: %s", record.get("average_rating")
        )
    # num_votes: int
    try:
        cleaned["num_votes"] = (
            int(cleaned["num_votes"])
            if cleaned.get("num_votes") not in (None, "\\N", "")
            else None
        )
    except (ValueError, TypeError):
        cleaned["num_votes"] = None
        logger.warning(
            "Could not convert num_votes to int: %s", record.get("num_votes")
        )
    # release_year: int
    try:
        cleaned["release_year"] = (
            int(cleaned["release_year"])
            if cleaned.get("release_year") not in (None, "\\N", "")
            else None
        )
    except (ValueError, TypeError):
        cleaned["release_year"] = None
    # runtime_minutes: int
    try:
        cleaned["runtime_minutes"] = (
            int(cleaned["runtime_minutes"])
            if cleaned.get("runtime_minutes") not in (None, "\\N", "")
            else None
        )
    except (ValueError, TypeError):
        cleaned["runtime_minutes"] = None
    # Preserve IMDb ID as string
    cleaned["imdb_id"] = str(cleaned.get("imdb_id", "")).strip()
    return cleaned


def clean_reddit_df(
    posts_df: pd.DataFrame, comments_df: pd.DataFrame, log_path: str = None
) -> tuple:
    """Clean Reddit posts and comments DataFrames."""
    log_entries = []

    # Posts
    if not posts_df.empty:
        p_orig = len(posts_df)
        posts_df["post_timestamp"] = pd.to_datetime(
            posts_df["post_timestamp"], errors="coerce", utc=True
        )
        posts_df["post_score"] = pd.to_numeric(posts_df["post_score"], errors="coerce")
        posts_df["comment_count"] = pd.to_numeric(
            posts_df["comment_count"], errors="coerce"
        )
        posts_df = posts_df.drop_duplicates(subset=["post_id"], keep="first")
        # Remove username-like columns if accidentally captured
        for col in ["author", "author_flair", "user_id"]:
            if col in posts_df.columns:
                posts_df = posts_df.drop(columns=[col])
                log_entries.append(f"Removed personal column '{col}' from posts")
        log_entries.append(
            f"Posts: {p_orig} -> {len(posts_df)} rows after dedup and type conversion"
        )

    # Comments
    if not comments_df.empty:
        c_orig = len(comments_df)
        no_text_count = comments_df["comment_text"].isna().sum()
        if no_text_count > 0:
            log_entries.append(
                f"Comments with null text (deleted/removed): {no_text_count} — preserved in table with is_deleted=1"
            )
        comments_df["comment_timestamp"] = pd.to_datetime(
            comments_df["comment_timestamp"], errors="coerce", utc=True
        )
        comments_df["comment_score"] = pd.to_numeric(
            comments_df["comment_score"], errors="coerce"
        )
        comments_df = comments_df.drop_duplicates(subset=["comment_id"], keep="first")
        for col in ["author", "author_flair", "user_id"]:
            if col in comments_df.columns:
                comments_df = comments_df.drop(columns=[col])
                log_entries.append(f"Removed personal column '{col}' from comments")
        log_entries.append(
            f"Comments: {c_orig} -> {len(comments_df)} rows after dedup"
        )

    if log_path:
        _write_log(log_path, "reddit", log_entries)

    return posts_df, comments_df


def _write_log(log_path: str, source: str, entries: list):
    """Append cleaning log entries to the cleaning log file."""
    with open(log_path, "a", encoding="utf-8") as f:
        ts = datetime.now(timezone.utc).isoformat()
        f.write(f"\n## Cleaning run — {source} — {ts}\n")
        for entry in entries:
            f.write(f"- {entry}\n")
