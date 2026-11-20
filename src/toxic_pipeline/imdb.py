"""IMDb non-commercial dataset downloader and film extractor."""
import gzip
import csv
import os
import logging
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

IMDB_BASE = "https://datasets.imdbws.com/"
FILES = ["title.basics.tsv.gz", "title.ratings.tsv.gz"]
IMDB_ID = "tt27530512"
FILM_ID = "TOXIC_2026"


def download_imdb_file(filename: str, raw_dir: str, force: bool = False) -> str:
    """Download an IMDb dataset file to raw_dir. Returns local path. Skips if already present."""
    raw_path = Path(raw_dir)
    raw_path.mkdir(parents=True, exist_ok=True)
    dest = raw_path / filename
    if dest.exists() and not force:
        logger.info(f"Already present: {dest}. Skipping download.")
        return str(dest)
    url = IMDB_BASE + filename
    logger.info(f"Downloading {url} ...")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
    logger.info(f"Saved {dest} ({dest.stat().st_size:,} bytes)")
    return str(dest)


def extract_film_record(
    basics_path: str,
    ratings_path: str,
    imdb_id: str = IMDB_ID,
    chunk_size: int = 100_000,
) -> dict:
    """Stream through TSV.GZ files and extract the single record for the target film."""
    basics_record = None
    ratings_record = None
    download_ts = datetime.now(timezone.utc).isoformat()

    logger.info(f"Scanning title.basics.tsv.gz for {imdb_id}...")
    with gzip.open(basics_path, "rt", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("tconst") == imdb_id:
                basics_record = dict(row)
                logger.info(f"Found basics record: {basics_record}")
                break

    if basics_record is None:
        logger.warning(f"IMDb ID {imdb_id} NOT found in title.basics.tsv.gz")
        return {}

    logger.info(f"Scanning title.ratings.tsv.gz for {imdb_id}...")
    with gzip.open(ratings_path, "rt", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("tconst") == imdb_id:
                ratings_record = dict(row)
                logger.info(f"Found ratings record: {ratings_record}")
                break

    if ratings_record is None:
        logger.info(
            f"No ratings record yet for {imdb_id} (film may not have enough votes)."
        )

    result = {
        "film_id": FILM_ID,
        "imdb_id": imdb_id,
        "primary_title": basics_record.get("primaryTitle"),
        "original_title": basics_record.get("originalTitle"),
        "release_year": basics_record.get("startYear"),
        "genres": basics_record.get("genres"),
        "runtime_minutes": basics_record.get("runtimeMinutes"),
        "average_rating": ratings_record.get("averageRating") if ratings_record else None,
        "num_votes": ratings_record.get("numVotes") if ratings_record else None,
        "source_file_basics": os.path.basename(basics_path),
        "source_file_ratings": os.path.basename(ratings_path) if ratings_record else None,
        "dataset_download_timestamp": download_ts,
        "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return result
