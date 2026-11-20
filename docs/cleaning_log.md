# Cleaning Log — Toxic 2026 Movie Data Pipeline

**Film:** Toxic: A Fairytale for Grown-Ups | TOXIC_2026 | tt27530512

## Instructions

This log is appended automatically by the cleaning scripts:
- `scripts/clean_critics.py` → appends a "critics" section
- `scripts/clean_imdb.py` → does not append (single-record; details in script log)
- `scripts/clean_reddit.py` → appends a "reddit" section

Each run appends a timestamped section. Raw data is never overwritten.

## Log initialised: 2026-11-20T18:00:00Z

---

*Cleaning runs will be recorded below automatically.*

## Cleaning run — critics — 2026-11-20T18:37:16.944095+00:00
- rating_normalized: 3 null values preserved as NULL
- Input: 7 rows | Output: 7 rows | Removed: 0

## Cleaning run — critics — 2026-11-20T18:37:43.585055+00:00
- rating_normalized: 3 null values preserved as NULL
- Input: 7 rows | Output: 7 rows | Removed: 0

## Cleaning run — wikipedia — 2026-11-20T18:56:11.719638+00:00
- page_id: 78832995 (verified integer)
- revision_id: 1386737157
- full_extract length: 23553 characters
- reception_text present: False
- critical_response_text present: True
- Input: 1 record | Output: 1 record | Removed: 0

## Cleaning run — wikipedia — 2026-11-20T19:04:08.432234+00:00
- page_id: 78832995 (verified integer)
- revision_id: 1386737157
- full_extract length: 23553 characters
- reception_text present: False
- critical_response_text present: True
- Input: 1 record | Output: 1 record | Removed: 0

## Cleaning run — critics — 2026-11-20T19:05:12.940623+00:00
- rating_normalized: 3 null values preserved as NULL
- Input: 7 rows | Output: 7 rows | Removed: 0
