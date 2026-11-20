"""Wikipedia Action API collector and extractor for TOXIC_2026.

Queries the official MediaWiki / Wikipedia Action API (https://en.wikipedia.org/w/api.php)
which returns native JSON without requiring authentication, payment, or API keys.
Preserves raw JSON responses, parses key sections (Reception, Critical response),
and formats structured records for staging and processing.
"""
import re
import logging
import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
DEFAULT_PAGE_TITLE = "Toxic_(2026_film)"
DEFAULT_USER_AGENT = "ToxicMovieCaseStudy/1.0 (Academic research; non-commercial)"
FILM_ID = "TOXIC_2026"


def fetch_wikipedia_page(
    page_title: str = DEFAULT_PAGE_TITLE,
    user_agent: str = DEFAULT_USER_AGENT,
    timeout: int = 15,
) -> Dict[str, Any]:
    """
    Query the Wikipedia Action API for the target film article.
    Returns the raw JSON response as a dictionary.
    """
    params = {
        "action": "query",
        "prop": "extracts|revisions|info|pageprops",
        "titles": page_title,
        "explaintext": "1",
        "rvprop": "timestamp|ids",
        "inprop": "url",
        "format": "json",
    }
    headers = {"User-Agent": user_agent}
    logger.info("Querying Wikipedia Action API: %s?titles=%s", WIKIPEDIA_API_URL, page_title)
    response = requests.get(WIKIPEDIA_API_URL, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    return data


def extract_wikipedia_record(raw_json: Dict[str, Any], film_id: str = FILM_ID) -> Dict[str, Any]:
    """
    Parse the raw Wikipedia Action API JSON response into a normalized record.
    Extracts page identifiers, revision timestamps, canonical URLs, full extract,
    and isolates the 'Reception' and 'Critical response' sections.
    """
    retrieval_ts = datetime.now(timezone.utc).isoformat()
    pages = raw_json.get("query", {}).get("pages", {})
    if not pages:
        raise ValueError("No pages found in Wikipedia API response.")

    page_id_str = list(pages.keys())[0]
    if page_id_str == "-1":
        raise ValueError(f"Wikipedia page not found (pageid -1): {pages[page_id_str]}")

    page_data = pages[page_id_str]
    title = page_data.get("title", "")
    full_url = page_data.get("fullurl", f"https://en.wikipedia.org/wiki/{DEFAULT_PAGE_TITLE}")
    page_id = int(page_data.get("pageid", 0))

    revisions = page_data.get("revisions", [])
    rev_id = revisions[0].get("revid") if revisions else None
    rev_timestamp = revisions[0].get("timestamp") if revisions else None

    extract = page_data.get("extract", "")

    # Parse sections from plain text extract
    reception_text = _extract_section_text(extract, "Reception")
    critical_text = _extract_section_text(extract, "Critical response")

    record = {
        "film_id": film_id,
        "page_id": page_id,
        "page_title": title,
        "page_url": full_url,
        "revision_id": int(rev_id) if rev_id else None,
        "revision_timestamp": rev_timestamp,
        "full_extract": extract,
        "reception_text": reception_text,
        "critical_response_text": critical_text,
        "retrieval_timestamp": retrieval_ts,
    }
    return record


def _extract_section_text(full_text: str, section_name: str) -> Optional[str]:
    """Extract plain text of a named section (e.g. 'Reception' or 'Critical response')."""
    pattern = rf"(?:^|\n)==+\s*{re.escape(section_name)}\s*==+\n(.*?)(?=\n==+|$)"
    match = re.search(pattern, full_text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def clean_wikipedia_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and type-cast a Wikipedia record."""
    cleaned = dict(record)
    cleaned["page_id"] = int(cleaned["page_id"])
    if cleaned.get("revision_id"):
        cleaned["revision_id"] = int(cleaned["revision_id"])

    # Clean whitespace in text fields
    for text_field in ["full_extract", "reception_text", "critical_response_text"]:
        val = cleaned.get(text_field)
        if isinstance(val, str):
            cleaned[text_field] = re.sub(r"\s+", " ", val).strip()

    return cleaned
