"""Film identity matching and verification for TOXIC_2026."""
import re
import unicodedata
from typing import Optional

FILM_ID = "TOXIC_2026"
IMDB_ID = "tt27530512"
CANONICAL_TITLE = "Toxic: A Fairytale for Grown-Ups"
RELEASE_YEAR = 2026
KNOWN_ALIASES = [
    "toxic: a fairytale for grown-ups",
    "toxic a fairytale for grown ups",
    "toxic",
]


def normalize_title(title: str) -> str:
    """Lowercase, strip punctuation, normalize unicode."""
    if not title:
        return ""
    t = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    t = re.sub(r"[^a-z0-9 ]", " ", t.lower())
    return re.sub(r"\s+", " ", t).strip()


def verify_imdb_id(imdb_id: str) -> bool:
    """Return True only if the IMDb ID exactly matches the canonical film."""
    return str(imdb_id).strip() == IMDB_ID


def match_record(
    record: dict,
    imdb_id_field: str = "tconst",
    title_field: str = "primaryTitle",
    year_field: str = "startYear",
) -> str:
    """
    Returns 'verified', 'ambiguous', or 'no_match'.
    Priority: IMDb ID match > title + year match.
    Records matching only on title (without year confirmation) are flagged 'ambiguous'.
    Records containing only the word 'toxic' are flagged 'ambiguous', never auto-matched.
    """
    record_imdb_id = str(record.get(imdb_id_field, "")).strip()
    if record_imdb_id and verify_imdb_id(record_imdb_id):
        return "verified"

    record_title = normalize_title(str(record.get(title_field, "")))
    record_year = str(record.get(year_field, "")).strip()

    if record_title == "toxic" and record_year != str(RELEASE_YEAR):
        return "ambiguous"

    if record_title in [normalize_title(a) for a in KNOWN_ALIASES]:
        if record_year == str(RELEASE_YEAR):
            return "ambiguous"  # title+year match without IMDb ID: flag for manual review
        return "no_match"

    return "no_match"


def flag_ambiguous(records: list, **kwargs) -> tuple:
    """Split records into (verified, ambiguous, no_match) lists."""
    verified, ambiguous, no_match = [], [], []
    for r in records:
        status = match_record(r, **kwargs)
        r["_match_status"] = status
        if status == "verified":
            verified.append(r)
        elif status == "ambiguous":
            ambiguous.append(r)
        else:
            no_match.append(r)
    return verified, ambiguous, no_match
