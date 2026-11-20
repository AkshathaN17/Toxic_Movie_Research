# Data Quality Report — Toxic 2026 Movie Data Pipeline

**Generated:** 2026-11-20T19:05:18.963474+00:00  
**Film:** Toxic: A Fairytale for Grown-Ups  
**IMDb ID:** tt27530512  
**Project ID:** TOXIC_2026

---
## Critics

**File:** `data\processed\critics\critics_clean.csv`  
**Rows:** 7

```
Validation: 9 passed, 0 failed
  [PASS] critics.col_exists.review_id: column present
  [PASS] critics.col_exists.film_id: column present
  [PASS] critics.col_exists.publication: column present
  [PASS] critics.col_exists.review_url: column present
  [PASS] critics.col_exists.collection_date: column present
  [PASS] critics.col_exists.collection_method: column present
  [PASS] critics.film_id_all_correct: 0 records with wrong film_id
  [PASS] critics.rating_normalized_range: 0 normalized ratings out of [0,10]
  [PASS] critics.no_duplicate_review_ids: 0 duplicate review_ids
```

## IMDb

**File:** `data\processed\imdb\imdb_toxic_2026_clean.json`  
**averageRating:** 4.0  
**numVotes:** 29840

```
Validation: 5 passed, 0 failed
  [PASS] imdb.imdb_id_correct: imdb_id=tt27530512
  [PASS] imdb.film_id_correct: film_id=TOXIC_2026
  [PASS] imdb.rating_in_range: averageRating=4.0
  [PASS] imdb.field_primary_title_present: primary_title=Toxic
  [PASS] imdb.field_release_year_present: release_year=2026
```

## Reddit

No processed data found.
Reddit collection requires OAuth credentials — see `.env.example`.
Run `scripts/collect_reddit.py` and `scripts/clean_reddit.py` once configured.

## Wikipedia Action API

**File:** `data\processed\wikipedia\wikipedia_toxic_2026_clean.json`  
**Page ID:** 78832995  
**Title:** Toxic (2026 film)  
**Revision ID:** 1386737157

```
Validation: 6 passed, 0 failed
  [PASS] wikipedia.film_id_correct: film_id=TOXIC_2026
  [PASS] wikipedia.page_id_valid: page_id=78832995
  [PASS] wikipedia.page_title_matches: page_title='Toxic (2026 film)'
  [PASS] wikipedia.revision_id_present: revision_id=1386737157
  [PASS] wikipedia.full_extract_present: extract length=23553 chars
  [PASS] wikipedia.reception_section_extracted: reception section text present
```

---

## Summary

| Metric | Value |
|---|---|
| Checks passed | 20 |
| Checks failed | 0 |
| Report generated | 2026-11-20T19:05:19.008567+00:00 |
