"""Critics collection: manual template + cautious web collection for permitted sources."""
import csv
import os
import logging
import time
import requests
import re
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

FILM_ID = "TOXIC_2026"
IMDB_ID = "tt27530512"

MANUAL_TEMPLATE_COLUMNS = [
    "review_id",
    "film_id",
    "publication",
    "critic_name",
    "review_date",
    "rating_raw",
    "rating_scale",
    "rating_normalized",
    "review_text",
    "review_url",
    "collection_date",
    "collection_method",
    "source_id",
]

KNOWN_RATING_SCALES = {
    "5star": 5.0,
    "4star": 4.0,
    "10point": 10.0,
    "100point": 100.0,
    "lettergrade": None,  # Cannot normalize automatically
}


def create_manual_template(output_path: str):
    """Create an empty CSV template for manual critic review entry."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        logger.info("Manual template already exists at %s", output_path)
        return
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MANUAL_TEMPLATE_COLUMNS)
        writer.writeheader()
    logger.info("Created manual entry template: %s", output_path)


def normalize_rating(raw_rating: str, scale: str):
    """Normalize a raw rating to 0-10 scale. Returns None if scale unknown or rating missing."""
    if not raw_rating or raw_rating.strip() in ("", "N/A", "None", "null"):
        return None
    if scale not in KNOWN_RATING_SCALES or KNOWN_RATING_SCALES[scale] is None:
        logger.warning(
            "Unknown or non-normalizable rating scale '%s'. Preserving raw only.", scale
        )
        return None
    try:
        value = float(raw_rating.strip().split("/")[0])
        max_val = KNOWN_RATING_SCALES[scale]
        normalized = round((value / max_val) * 10, 2)
        if not (0 <= normalized <= 10):
            logger.warning("Normalized rating %s out of range [0,10]", normalized)
            return None
        return normalized
    except (ValueError, ZeroDivisionError) as e:
        logger.warning(
            "Could not normalize rating '%s' on scale '%s': %s", raw_rating, scale, e
        )
        return None


def load_manual_entries(csv_path: str) -> list:
    """Load manually entered critic reviews from the template CSV."""
    path = Path(csv_path)
    if not path.exists():
        logger.warning("Manual entry file not found: %s", csv_path)
        return []
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("film_id", "").strip() != FILM_ID:
                logger.warning(
                    "Skipping row with wrong film_id: %s", row.get("film_id")
                )
                continue
            rows.append(row)
    logger.info("Loaded %d manually entered critic reviews", len(rows))
    return rows
