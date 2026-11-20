# Toxic 2026 Movie Data Pipeline

**Film:** *Toxic: A Fairytale for Grown-Ups*  
**IMDb ID:** `tt27530512` | **Film ID:** `TOXIC_2026`  
**Director:** Geetu Mohandas | **Lead Actor:** Yash  
**Release Year:** 2026 | **Academic Context:** Reproducible Movie Data Acquisition Case Study

---

## 1. Project Purpose & Scope Boundaries

This repository implements an academic-grade, auditable, and legally/policy compliant Python ETL pipeline that extracts, stages, cleans, validates, and stores four streams of publicly accessible data about the 2026 film *Toxic: A Fairytale for Grown-Ups*:

1. **Official IMDb Audience Data:** Bulk non-commercial TSV datasets (`title.basics.tsv.gz`, `title.ratings.tsv.gz`).
2. **Professional Film Critic Reviews:** Verified reviews from major Indian and international film publications transcribed via a structured manual entry workflow to respect publication terms of service and robots.txt restrictions.
3. **Wikipedia Action API (Live REST API):** Free, open REST API returning native JSON with verified reception sections, box office summaries, and production history.
4. **Reddit Social Audience Data (PRAW OAuth2):** Real-time discussion collection via the official Reddit API with strict PII scrubbing.

> **CRITICAL SCOPE RESTRICTION:**  
> This project strictly covers **data engineering only** — source identification, verification, API integration, bulk streaming ingestion, raw data preservation, cleaning, normalisation, relational database modeling, and automated quality assurance.  
> It does **NOT** perform sentiment analysis, natural language processing, topic modeling, visualizations, or answer interpretive research questions about the film.

---

## 2. Implementation & Execution Status

Per strict reproducibility criteria, here is the verified status of all pipeline components:

| Component | Ingestion Mechanism | Format | Status | Details / Audit Trail |
|---|---|---|---|---|
| **IMDb Bulk Datasets** | Streaming TSV.GZ download | Structured (`TSV.GZ`) | **Executed Successfully** | Downloaded 239.5 MB; filtered to `tt27530512` (Rating: 4.0, Votes: 29,840) |
| **Critics Reviews** | Manual entry template | Unstructured (Prose) + Structured (Ratings) | **Executed Successfully** | 7 verified reviews populated, cleaned, and validated |
| **Wikipedia Action API** | Public HTTP GET (`api.php`) | Semi-structured (`JSON`) | **Executed Successfully** | Live JSON extracted (PageID: 78832995, RevID: 1386737157, 23,553 chars) |
| **Reddit Audience API** | PRAW OAuth2 (`oauth.reddit.com`) | Semi-structured (`JSONL`) | **Implemented (Requires Credentials)** | Collector code complete; exits gracefully when credentials missing |
| **Automated QA Validation** | Rule assertions (`validate_data.py`) | Markdown report | **Executed Successfully** | **20 passed, 0 failed** across all active sources |
| **Unit Test Suite** | Standard `unittest` | Python tests | **Executed Successfully** | **9 unit tests passed** in `tests/test_pipeline.py` (0.012s) |
| **MySQL Relational Load** | SQLAlchemy / PyMySQL | Relational schema | **Implemented (Requires DB Credentials)** | DDL schema ready; requires `MYSQL_USER`/`PASSWORD` in `.env` |

---

## 3. Data Taxonomy (Structured, Semi-Structured, Unstructured)

The pipeline integrates all three standard data formats:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DATA PIPELINE TAXONOMY                          │
├──────────────────┬───────────────────────┬─────────────────────────────┤
│ Structured       │ Semi-Structured       │ Unstructured                │
├──────────────────┼───────────────────────┼─────────────────────────────┤
│ • IMDb TSV.GZ    │ • Wikipedia JSON      │ • Critic Review Prose       │
│ • Staged CSVs    │ • Reddit JSON / JSONL │ • Wikipedia Section Text    │
│ • MySQL Tables   │ • Settings YAML       │ • Reddit Post Bodies        │
│ • Parquet Schema │ • IMDb Staging JSON   │ • Reddit Comment Bodies     │
└──────────────────┴───────────────────────┴─────────────────────────────┘
```

* **Structured:** IMDb non-commercial bulk files with rigid columns and types; MySQL schema with foreign keys and indexes; Parquet columnar files for Reddit text.
* **Semi-Structured:** Live Wikipedia Action API JSON payloads; raw Reddit JSONL submissions; hierarchical configuration in `settings.yaml`.
* **Unstructured:** Free-form critical review prose written by critics (e.g. Vivek M.V., Shubhra Gupta); narrative reception sections; raw Reddit comment bodies.

---

## 4. Environment Setup & Prerequisites

### Step 1: Clone Repository & Create Virtual Environment

```powershell
# Open terminal in project root:
cd "E:\Desktop\Release day radar\Toxic_Movie_Case_Study"

# Use Python 3.12 (or py -3):
py -3 -m venv .venv
.venv\Scripts\activate

# Install locked dependencies:
py -3 -m pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

```powershell
# Copy placeholder environment file:
copy .env.example .env
```

Edit `.env` as needed:
* **Wikipedia Action API:** No credentials or tokens required (works immediately out of the box).
* **IMDb Non-Commercial Datasets:** No credentials required (direct download).
* **Reddit OAuth:** If you wish to pull live Reddit threads, add your free `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` from <https://www.reddit.com/prefs/apps>.
* **MySQL Database:** If loading to a live MySQL instance, specify `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_HOST`, and `MYSQL_PORT`.

---

## 5. How to Run the Pipeline (Step-by-Step)

All commands should be executed from `Toxic_Movie_Case_Study/`.

### Step 1: Collect & Process Wikipedia Data (Live JSON REST API)

Queries the official MediaWiki Action API for `Toxic_(2026_film)` and saves raw JSON:

```powershell
# 1. Fetch raw JSON and stage:
py -3 scripts/collect_wikipedia.py

# 2. Clean whitespace and extract reception sections:
py -3 scripts/clean_wikipedia.py
```
* **Raw Artifact:** `data/raw/wikipedia/wikipedia_toxic_2026_raw.json`
* **Processed Artifact:** `data/processed/wikipedia/wikipedia_toxic_2026_clean.json` & `.csv`

---

### Step 2: Download & Extract Official IMDb Bulk Datasets

Downloads official `.tsv.gz` files from `datasets.imdbws.com`, streams through millions of records without high memory overhead, and extracts the record matching `tt27530512`:

```powershell
# 1. Download and extract target film:
py -3 scripts/download_imdb.py

# 2. Clean types and format:
py -3 scripts/clean_imdb.py
```
* **Raw Artifacts:** `data/raw/imdb/title.basics.tsv.gz` (230.7 MB), `data/raw/imdb/title.ratings.tsv.gz` (8.8 MB)
* **Processed Artifacts:** `data/processed/imdb/imdb_toxic_2026_clean.json` & `.csv`

---

### Step 3: Collect & Clean Critic Reviews

Review metadata is curated via `data/raw/critics/manual_entry_template.csv` to adhere to web scraping prohibitions in publication terms of service:

```powershell
# 1. Stage manual reviews:
py -3 scripts/collect_critics.py

# 2. Clean, deduplicate, and normalize ratings (0–10 scale):
py -3 scripts/clean_critics.py
```
* **Raw Artifact:** `data/raw/critics/manual_entry_template.csv`
* **Processed Artifact:** `data/processed/critics/critics_clean.csv`

---

### Step 4: Run Data Quality Validation Suite

Executes automated structural, type-safety, duplicate, and domain checks across all processed data files:

```powershell
py -3 scripts/validate_data.py
```
* Inspect output: `docs/data_quality_report.md` (Currently: **20 checks passed, 0 failed**).

---

### Step 5: Run Unit Tests

Execute the test suite using synthetic test fixtures:

```powershell
py -3 -m unittest discover tests -v
```
* Runs 9 automated unit tests verifying film matching, rating normalisation, whitespace cleaning, and Wikipedia parsing.

---

### Step 6: Load Data into MySQL Database (Optional)

Apply relational schema and perform idempotent data ingestion (`INSERT IGNORE`):

```powershell
# Apply DDL schema only:
py -3 scripts/load_mysql.py --schema-only

# Full relational ingestion:
py -3 scripts/load_mysql.py
```

---

## 6. Directory Structure

```
Toxic_Movie_Case_Study/
├── config/
│   └── settings.example.yaml          # YAML configuration template
├── data/
│   ├── raw/                           # Raw, immutable data assets
│   │   ├── critics/manual_entry_template.csv
│   │   ├── imdb/title.basics.tsv.gz   # Compressed TSV dump (230 MB)
│   │   ├── imdb/title.ratings.tsv.gz  # Compressed ratings dump (8.8 MB)
│   │   ├── reddit/                    # JSONL target folder
│   │   └── wikipedia/wikipedia_toxic_2026_raw.json # Raw Wikipedia JSON
│   ├── staging/                       # Intermediate representations
│   │   ├── critics/critics_manual_entries.csv
│   │   ├── imdb/imdb_toxic_2026.json & .csv
│   │   ├── reddit/
│   │   └── wikipedia/wikipedia_toxic_2026.json & .csv
│   └── processed/                     # Cleaned, typed, production datasets
│       ├── critics/critics_clean.csv  # 7 verified reviews
│       ├── imdb/imdb_toxic_2026_clean.json & .csv
│       ├── reddit/                    # Parquet target
│       └── wikipedia/wikipedia_toxic_2026_clean.json & .csv
├── docs/
│   ├── source_register.csv            # Detailed source & legal terms register
│   ├── data_collection_plan.md        # Methodological collection plan
│   ├── data_dictionary.md             # Field-by-field schema reference
│   ├── cleaning_log.md                # Automated audit log of cleaning actions
│   ├── data_quality_report.md         # Generated validation report (20 checks)
│   └── limitations.md                 # Detailed limitations register
├── notebooks/
│   ├── 01_source_verification.ipynb   # Film matching and source verification
│   ├── 02_data_collection.ipynb       # Collection script walkthroughs
│   ├── 03_data_cleaning.ipynb         # Cleaning transformation review
│   └── 04_data_loading.ipynb          # Database loading & QA gate
├── scripts/
│   ├── collect_wikipedia.py           # Live Wikipedia Action API client
│   ├── clean_wikipedia.py             # Wikipedia cleaner & section extractor
│   ├── download_imdb.py               # IMDb bulk downloader & chunked filter
│   ├── clean_imdb.py                  # IMDb type conversion & validator
│   ├── collect_critics.py             # Critics template manager & stager
│   ├── clean_critics.py               # Critics normalizer & deduplicator
│   ├── collect_reddit.py              # PRAW OAuth Reddit collector
│   ├── clean_reddit.py                # Reddit cleaner & Parquet exporter
│   ├── validate_data.py               # Automated QA assertion runner
│   └── load_mysql.py                  # MySQL relational loader
├── src/toxic_pipeline/                # Production Python package
│   ├── __init__.py                    # Constants & package metadata
│   ├── config.py                      # Config & environment manager
│   ├── film_matching.py               # Strict film identity matching logic
│   ├── critics.py                     # Rating normalisation & scales
│   ├── imdb.py                        # Chunked TSV.GZ stream extractor
│   ├── wikipedia.py                   # Wikipedia Action API engine
│   ├── reddit.py                      # PRAW OAuth client & PII scrub
│   ├── cleaning.py                    # Multi-source cleaning transforms
│   ├── validation.py                  # Assertion rules & ValidationReport
│   └── database.py                    # Relational schema & SQLAlchemy ops
├── sql/
│   └── schema.sql                     # Full MySQL DDL (7 tables, utf8mb4)
├── tests/
│   └── test_pipeline.py               # Synthetic unit test suite (9 tests)
├── logs/
│   ├── collection_log.csv             # Ingestion audit log
│   └── *.log                          # Process log files
├── .env.example                       # Credential placeholders
├── .gitignore                         # Python/data exclusions
├── requirements.txt                   # Constrained Python packages
└── README.md                          # Documentation & execution guide
```

---

## 7. Data Quality & Validation Summary

Running `scripts/validate_data.py` generates the automated quality report at `docs/data_quality_report.md`:

```
========================================================
DATA QUALITY VALIDATION SUMMARY (20 PASS, 0 FAIL)
========================================================
[PASS] critics.col_exists.review_id: column present
[PASS] critics.col_exists.film_id: column present
[PASS] critics.col_exists.publication: column present
[PASS] critics.col_exists.review_url: column present
[PASS] critics.col_exists.collection_date: column present
[PASS] critics.col_exists.collection_method: column present
[PASS] critics.film_id_all_correct: 0 records with wrong film_id
[PASS] critics.rating_normalized_range: 0 normalized ratings out of [0,10]
[PASS] critics.no_duplicate_review_ids: 0 duplicate review_ids
[PASS] imdb.imdb_id_correct: imdb_id=tt27530512
[PASS] imdb.film_id_correct: film_id=TOXIC_2026
[PASS] imdb.rating_in_range: averageRating=4.0
[PASS] imdb.field_primary_title_present: primary_title=Toxic
[PASS] imdb.field_release_year_present: release_year=2026
[PASS] wikipedia.film_id_correct: film_id=TOXIC_2026
[PASS] wikipedia.page_id_valid: page_id=78832995
[PASS] wikipedia.page_title_matches: page_title='Toxic (2026 film)'
[PASS] wikipedia.revision_id_present: revision_id=1386737157
[PASS] wikipedia.full_extract_present: extract length=23553 chars
[PASS] wikipedia.reception_section_extracted: reception section text present
```

---

## 8. Attribution & Licensing

* **IMDb Non-Commercial Datasets:**  
  *Information courtesy of IMDb (https://www.imdb.com). Used with permission.* Licensed for personal and non-commercial use only.
* **Wikipedia Action API:**  
  Content sourced from Wikipedia under the *Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0)*.
* **Critic Reviews:**  
  Metadata and excerpts transcribed for academic commentary and data analysis under Fair Dealing / Fair Use principles. Automated scraping is intentionally disabled.
