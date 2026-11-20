"""Automated data quality validation checks."""
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

FILM_ID = "TOXIC_2026"
IMDB_ID = "tt27530512"


class ValidationReport:
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0

    def add(self, check_name: str, passed: bool, detail: str = ""):
        status = "PASS" if passed else "FAIL"
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        self.checks.append({"check": check_name, "status": status, "detail": detail})
        logger.info("[%s] %s: %s", status, check_name, detail)

    def summary(self) -> str:
        lines = [f"Validation: {self.passed} passed, {self.failed} failed"]
        for c in self.checks:
            lines.append(f"  [{c['status']}] {c['check']}: {c['detail']}")
        return "\n".join(lines)


def validate_critics(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport()
    required_cols = [
        "review_id",
        "film_id",
        "publication",
        "review_url",
        "collection_date",
        "collection_method",
    ]
    for col in required_cols:
        report.add(
            f"critics.col_exists.{col}",
            col in df.columns,
            f"column {'present' if col in df.columns else 'MISSING'}",
        )

    if "film_id" in df.columns:
        wrong_film = (df["film_id"] != FILM_ID).sum()
        report.add(
            "critics.film_id_all_correct",
            wrong_film == 0,
            f"{wrong_film} records with wrong film_id",
        )

    if "rating_normalized" in df.columns:
        norm_series = pd.to_numeric(df["rating_normalized"], errors="coerce").dropna()
        out_of_range = norm_series.between(0, 10).eq(False).sum()
        report.add(
            "critics.rating_normalized_range",
            out_of_range == 0,
            f"{out_of_range} normalized ratings out of [0,10]",
        )

    if "review_id" in df.columns:
        dups = df["review_id"].duplicated().sum()
        report.add(
            "critics.no_duplicate_review_ids",
            dups == 0,
            f"{dups} duplicate review_ids",
        )

    return report


def validate_imdb(record: dict) -> ValidationReport:
    report = ValidationReport()
    report.add(
        "imdb.imdb_id_correct",
        record.get("imdb_id") == IMDB_ID,
        f"imdb_id={record.get('imdb_id')}",
    )
    report.add(
        "imdb.film_id_correct",
        record.get("film_id") == FILM_ID,
        f"film_id={record.get('film_id')}",
    )

    avg = record.get("average_rating")
    if avg is not None:
        report.add(
            "imdb.rating_in_range",
            0 <= float(avg) <= 10,
            f"averageRating={avg}",
        )
    else:
        report.add(
            "imdb.rating_present",
            False,
            "averageRating is NULL (may not have enough votes yet)",
        )

    for field in ["primary_title", "release_year"]:
        report.add(
            f"imdb.field_{field}_present",
            record.get(field) not in (None, "\\N", ""),
            f"{field}={record.get(field)}",
        )

    return report


def validate_reddit(
    posts_df: pd.DataFrame, comments_df: pd.DataFrame
) -> ValidationReport:
    report = ValidationReport()

    if not posts_df.empty:
        wrong_film = (
            (posts_df["film_id"] != FILM_ID).sum()
            if "film_id" in posts_df.columns
            else "N/A"
        )
        report.add(
            "reddit.posts.film_id_correct",
            wrong_film == 0,
            f"{wrong_film} wrong film_ids",
        )
        dups = (
            posts_df["post_id"].duplicated().sum()
            if "post_id" in posts_df.columns
            else "N/A"
        )
        report.add(
            "reddit.posts.no_duplicate_ids",
            dups == 0,
            f"{dups} duplicate post_ids",
        )
        no_username = "author" not in posts_df.columns
        report.add(
            "reddit.posts.no_username_column",
            no_username,
            "author column removed" if no_username else "AUTHOR COLUMN PRESENT — remove it",
        )

    if not comments_df.empty:
        dups = (
            comments_df["comment_id"].duplicated().sum()
            if "comment_id" in comments_df.columns
            else "N/A"
        )
        report.add(
            "reddit.comments.no_duplicate_ids",
            dups == 0,
            f"{dups} duplicate comment_ids",
        )
        no_username = "author" not in comments_df.columns
        report.add(
            "reddit.comments.no_username_column",
            no_username,
            "author column removed" if no_username else "AUTHOR COLUMN PRESENT — remove it",
        )

    return report


def validate_wikipedia(record: dict) -> ValidationReport:
    """Validate extracted Wikipedia Action API movie record."""
    report = ValidationReport()
    report.add("wikipedia.film_id_correct", record.get("film_id") == FILM_ID, f"film_id={record.get('film_id')}")
    
    page_id = record.get("page_id")
    report.add("wikipedia.page_id_valid", isinstance(page_id, int) and page_id > 0, f"page_id={page_id}")
    
    title = str(record.get("page_title", ""))
    report.add("wikipedia.page_title_matches", "toxic" in title.lower(), f"page_title='{title}'")
    
    rev_id = record.get("revision_id")
    report.add("wikipedia.revision_id_present", rev_id is not None and int(rev_id) > 0, f"revision_id={rev_id}")
    
    extract_len = len(record.get("full_extract", "") or "")
    report.add("wikipedia.full_extract_present", extract_len > 100, f"extract length={extract_len} chars")
    
    reception = record.get("reception_text") or record.get("critical_response_text")
    report.add("wikipedia.reception_section_extracted", bool(reception), "reception section text present" if reception else "reception section missing/empty")
    
    return report
