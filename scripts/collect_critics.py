#!/usr/bin/env python3
"""
collect_critics.py
Critic review collection for TOXIC_2026.

Automated scraping is PROHIBITED by the terms of service of all major review
aggregators and publications identified for this film.  This script therefore:

  1. Creates an empty manual-entry CSV template if it does not exist.
  2. Loads any rows already entered into that template, validates them, and
     copies them to the staging directory.

Workflow:
  a) Run this script once  →  template is created at data/raw/critics/manual_entry_template.csv
  b) Open the template in Excel or any CSV editor.
  c) For each review, visit the original publication URL, copy the metadata
     into the template row by row (review_id, film_id, publication, critic_name,
     review_date, rating_raw, rating_scale, rating_normalized, review_text,
     review_url, collection_date, collection_method, source_id).
  d) Save the template and re-run this script  →  entries staged automatically.

Confirmed review sources (manual collection required for all):
  - Rotten Tomatoes   https://www.rottentomatoes.com/m/toxic_a_fairytale_for_grown_ups
  - The Hindu         https://www.thehindu.com  (critic: Vivek M.V.)
  - NDTV Movies       https://www.ndtv.com      (3/5 stars confirmed)
  - THR India         https://www.hollywoodreporterindia.com/global/reviews/toxic-movie-review-anupama-chopra-thr-india
  - Baradwaj Rangan   https://galattaplus.com/geetu-mohandass-toxic-is-eccentric-ambitious-not-fully-successful-but-not-without-interest-either/
  - IGN               https://www.ign.com
  - Hindustan Times   https://www.hindustantimes.com
  - Indian Express    https://www.indianexpress.com
  - Firstpost         https://www.firstpost.com
  - Deccan Chronicle  https://www.deccanchronicle.com

Usage:
    python scripts/collect_critics.py
"""

import sys
import csv
import logging
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from toxic_pipeline.config import load_config, FILM_ID
from toxic_pipeline.critics import create_manual_template, load_manual_entries, normalize_rating
from toxic_pipeline.film_matching import verify_imdb_id

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/collect_critics.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def main():
    config = load_config()
    critics_cfg = config.get("critics", {})
    raw_dir     = critics_cfg.get("raw_dir",      "data/raw/critics")
    staging_dir = critics_cfg.get("staging_dir",  "data/staging/critics")
    template    = critics_cfg.get("manual_template", "data/raw/critics/manual_entry_template.csv")

    Path(raw_dir).mkdir(parents=True, exist_ok=True)
    Path(staging_dir).mkdir(parents=True, exist_ok=True)

    # 1. Ensure the manual-entry template exists
    create_manual_template(template)
    logger.info("Manual entry template: %s", template)
    logger.info(
        "Fill the template with critic review metadata and re-run this script "
        "to stage entries.  See docs/data_collection_plan.md for instructions."
    )

    # 2. Load whatever has been entered
    entries = load_manual_entries(template)
    if not entries:
        logger.info("No manual entries found yet — template is empty.")
        _write_collection_log("critics_manual", "load_template", 0, 0, "template_empty",
                               "Template created; awaiting manual data entry.")
        return

    # 3. Validate and stage
    valid, skipped = [], []
    for row in entries:
        # Must be linked to the correct film
        if row.get("film_id", "").strip() != FILM_ID:
            logger.warning("Skipping row — wrong film_id: %s", row.get("film_id"))
            skipped.append(row)
            continue
        # review_id must be present
        if not row.get("review_id", "").strip():
            logger.warning("Skipping row — missing review_id: %s", row.get("review_url"))
            skipped.append(row)
            continue
        # Apply rating normalization if scale is known but normalized value is blank
        if row.get("rating_raw") and row.get("rating_scale") and not row.get("rating_normalized"):
            norm = normalize_rating(row["rating_raw"], row["rating_scale"])
            if norm is not None:
                row["rating_normalized"] = str(norm)
        valid.append(row)

    logger.info("Entries: %d valid, %d skipped", len(valid), len(skipped))

    if valid:
        df = pd.DataFrame(valid)
        out = Path(staging_dir) / "critics_manual_entries.csv"
        df.to_csv(out, index=False, encoding="utf-8")
        logger.info("Staged %d critic reviews → %s", len(df), out)

    if skipped:
        df_skip = pd.DataFrame(skipped)
        out_skip = Path(staging_dir) / "critics_skipped.csv"
        df_skip.to_csv(out_skip, index=False, encoding="utf-8")
        logger.warning("%d rows skipped (see %s)", len(skipped), out_skip)

    _write_collection_log(
        "critics_manual", "stage_entries",
        records_collected=len(valid),
        records_failed=len(skipped),
        status="success" if valid else "no_data",
        notes=f"staged to {staging_dir}",
    )


def _write_collection_log(source, operation, records_collected, records_failed, status, notes=""):
    log_path = Path("logs") / "collection_log.csv"
    write_header = not log_path.exists()
    with open(log_path, "a", encoding="utf-8", newline="") as f:
        import csv as csv_mod
        writer = csv_mod.writer(f)
        if write_header:
            writer.writerow(["timestamp", "source", "operation", "records_collected",
                             "records_failed", "status", "notes"])
        writer.writerow([datetime.now(timezone.utc).isoformat(), source, operation,
                         records_collected, records_failed, status, notes])


if __name__ == "__main__":
    main()
