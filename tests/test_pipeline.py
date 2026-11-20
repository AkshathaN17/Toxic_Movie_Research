"""Unit tests for Toxic 2026 Movie Data Pipeline using SYNTHETIC test data.
Built using standard library unittest to run seamlessly in any standard Python environment.
"""
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import pandas as pd
from toxic_pipeline.film_matching import (
    FILM_ID,
    IMDB_ID,
    CANONICAL_TITLE,
    RELEASE_YEAR,
    normalize_title,
    verify_imdb_id,
    match_record,
    flag_ambiguous,
)
from toxic_pipeline.critics import (
    normalize_rating,
    KNOWN_RATING_SCALES,
)
from toxic_pipeline.cleaning import (
    normalize_whitespace,
    clean_critics_df,
    clean_imdb_record,
    clean_reddit_df,
)
from toxic_pipeline.validation import (
    ValidationReport,
    validate_critics,
    validate_imdb,
    validate_reddit,
    validate_wikipedia,
)
from toxic_pipeline.wikipedia import (
    extract_wikipedia_record,
    clean_wikipedia_record,
)


class TestToxicPipeline(unittest.TestCase):

    def test_film_matching_constants(self):
        self.assertEqual(FILM_ID, "TOXIC_2026")
        self.assertEqual(IMDB_ID, "tt27530512")
        self.assertTrue(verify_imdb_id("tt27530512"))
        self.assertFalse(verify_imdb_id("tt99999999"))
        self.assertFalse(verify_imdb_id(""))

    def test_normalize_title(self):
        self.assertEqual(normalize_title("Toxic: A Fairytale for Grown-Ups"), "toxic a fairytale for grown ups")
        self.assertEqual(normalize_title("  TOXIC   "), "toxic")
        self.assertEqual(normalize_title(""), "")
        self.assertEqual(normalize_title(None), "")

    def test_match_record_and_flag_ambiguous(self):
        synthetic_records = [
            {"tconst": "tt27530512", "primaryTitle": "Toxic", "startYear": "2026"},
            {"tconst": "tt0000002", "primaryTitle": "Toxic", "startYear": "2024"},
            {"tconst": "tt0000003", "primaryTitle": "Toxic: A Fairytale for Grown-Ups", "startYear": "2026"},
            {"tconst": "tt0000004", "primaryTitle": "Completely Unrelated", "startYear": "2026"},
        ]
        verified, ambiguous, no_match = flag_ambiguous(synthetic_records)
        self.assertEqual(len(verified), 1)
        self.assertEqual(verified[0]["tconst"], "tt27530512")
        self.assertEqual(len(ambiguous), 2)  # Toxic (2024) and title match without IMDb ID
        self.assertEqual(len(no_match), 1)

    def test_rating_normalization(self):
        self.assertEqual(normalize_rating("3", "5star"), 6.0)
        self.assertEqual(normalize_rating("4", "5star"), 8.0)
        self.assertEqual(normalize_rating("3.5", "4star"), 8.75)
        self.assertEqual(normalize_rating("7.5", "10point"), 7.5)
        self.assertEqual(normalize_rating("85", "100point"), 8.5)
        self.assertIsNone(normalize_rating("A", "lettergrade"))
        self.assertIsNone(normalize_rating(None, "5star"))
        self.assertIsNone(normalize_rating("3", None))
        self.assertIsNone(normalize_rating("15", "10point"))

    def test_clean_critics_df(self):
        synthetic_critics = pd.DataFrame([
            {
                "review_id": "SYN_01",
                "film_id": "TOXIC_2026",
                "publication": " Test Pub ",
                "critic_name": " John   Doe ",
                "review_date": "2026-04-10",
                "rating_raw": "3",
                "rating_scale": "5star",
                "rating_normalized": "6.0",
                "review_text": " Great   film  with intense sequences. ",
                "review_url": "https://example.com/rev1",
                "collection_date": "2026-04-11",
                "collection_method": "manual_entry",
                "source_id": "CRITICS_SYNTHETIC",
            },
            {
                "review_id": "SYN_02",
                "film_id": "TOXIC_2026",
                "publication": " Test Pub ",
                "critic_name": " John Doe ",
                "review_date": "2026-04-10",
                "rating_raw": "3",
                "rating_scale": "5star",
                "rating_normalized": "6.0",
                "review_text": " Duplicate entry ",
                "review_url": "https://example.com/rev1",
                "collection_date": "2026-04-11",
                "collection_method": "manual_entry",
                "source_id": "CRITICS_SYNTHETIC",
            }
        ])
        cleaned = clean_critics_df(synthetic_critics)
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned.iloc[0]["critic_name"], "John Doe")
        self.assertEqual(cleaned.iloc[0]["publication"], "Test Pub")
        self.assertEqual(cleaned.iloc[0]["review_text"], "Great film with intense sequences.")

    def test_clean_imdb_record(self):
        raw_synthetic = {
            "film_id": "TOXIC_2026",
            "imdb_id": "tt27530512",
            "average_rating": "4.0",
            "num_votes": "29840",
            "release_year": "2026",
            "runtime_minutes": "192",
            "genres": "Action,Crime,Drama",
        }
        cleaned = clean_imdb_record(raw_synthetic)
        self.assertIsInstance(cleaned["average_rating"], float)
        self.assertEqual(cleaned["average_rating"], 4.0)
        self.assertIsInstance(cleaned["num_votes"], int)
        self.assertEqual(cleaned["num_votes"], 29840)
        self.assertEqual(cleaned["release_year"], 2026)
        self.assertEqual(cleaned["runtime_minutes"], 192)

    def test_clean_reddit_df(self):
        synthetic_posts = pd.DataFrame([
            {
                "post_id": "post_syn_01",
                "film_id": "TOXIC_2026",
                "author": "should_be_removed_user",
                "post_title": "Discussion on Toxic 2026",
                "post_text": "Detailed audience feedback.",
                "post_score": "150",
                "comment_count": "25",
                "post_timestamp": "2026-04-10T12:00:00Z",
            }
        ])
        synthetic_comments = pd.DataFrame([
            {
                "comment_id": "comm_syn_01",
                "post_id": "post_syn_01",
                "film_id": "TOXIC_2026",
                "author": "another_private_user",
                "comment_text": "Loved the cinematography.",
                "comment_score": "10",
                "comment_timestamp": "2026-04-10T12:05:00Z",
            }
        ])
        cleaned_posts, cleaned_comments = clean_reddit_df(synthetic_posts, synthetic_comments)
        self.assertNotIn("author", cleaned_posts.columns)
        self.assertNotIn("author", cleaned_comments.columns)
        self.assertTrue(pd.api.types.is_numeric_dtype(cleaned_posts["post_score"]))
        self.assertTrue(pd.api.types.is_numeric_dtype(cleaned_comments["comment_score"]))

    def test_validation_report(self):
        report = ValidationReport()
        report.add("check_true", True, "Passed ok")
        report.add("check_false", False, "Failed reason")
        self.assertEqual(report.passed, 1)
        self.assertEqual(report.failed, 1)
        self.assertIn("FAIL", report.summary())

    def test_wikipedia_extract_and_clean(self):
        synthetic_api_response = {
            "query": {
                "pages": {
                    "78832995": {
                        "pageid": 78832995,
                        "title": "Toxic (2026 film)",
                        "fullurl": "https://en.wikipedia.org/wiki/Toxic_(2026_film)",
                        "revisions": [{"revid": 12345678, "timestamp": "2026-08-27T00:00:00Z"}],
                        "extract": "Toxic: A Fairy Tale for Grown-Ups is a 2026 Indian film.\n\n== Reception ==\nThe film received mixed to negative reviews.\n\n== Critical response ==\nCritics noted stylistic ambitions but criticized the runtime."
                    }
                }
            }
        }
        record = extract_wikipedia_record(synthetic_api_response, film_id="TOXIC_2026")
        self.assertEqual(record["page_id"], 78832995)
        self.assertEqual(record["film_id"], "TOXIC_2026")
        self.assertIn("mixed to negative", record["reception_text"])
        self.assertIn("stylistic ambitions", record["critical_response_text"])

        cleaned = clean_wikipedia_record(record)
        self.assertIsInstance(cleaned["page_id"], int)
        self.assertIsInstance(cleaned["revision_id"], int)

        report = validate_wikipedia(cleaned)
        self.assertEqual(report.failed, 0)
        self.assertEqual(report.passed, 6)


if __name__ == "__main__":
    unittest.main()
