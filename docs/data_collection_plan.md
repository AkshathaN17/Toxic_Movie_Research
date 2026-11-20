# Data Collection Plan — Toxic 2026 Movie Data Pipeline

**Film:** Toxic: A Fairytale for Grown-Ups  
**IMDb ID:** tt27530512 | **Director:** Geetu Mohandas | **Starring:** Yash  
**Project ID:** TOXIC_2026 | **Plan version:** 1.0 | **Date:** 2026-11-20

---

## 1. Project Overview

This data collection plan governs the acquisition of three streams of publicly
available data for the film *Toxic: A Fairytale for Grown-Ups* (2026).

**Research question (context only):** "Do critics, IMDb users and Reddit users
agree about the same film? Where do they split, and why?"

**Scope of this plan:** Data engineering only — source identification,
access verification, collection method, cleaning, and storage. This plan does
NOT cover sentiment analysis, topic modelling, visualisation, or any
interpretation of the data.

**Film identity anchor:** All records must be linked to `film_id = TOXIC_2026`
and verified against `imdb_id = tt27530512`. Records matched only on the word
"Toxic" are flagged ambiguous and excluded from the main dataset.

---

## 2. Data Sources

### 2A. Critics

#### Source selection rationale

Professional film critic reviews provide structured, expert assessments of the
film with traceable publication dates, named authors, and (usually) explicit
ratings. This data stream is essential for comparing the professional critical
response to the audience response.

The following sources were verified as confirmed through web research:

| Source ID | Publication | URL | Review Confirmed | Rating Scale |
|---|---|---|---|---|
| CRITICS_RT | Rotten Tomatoes | https://www.rottentomatoes.com/m/toxic_a_fairytale_for_grown_ups | ✅ (~21% Tomatometer) | Tomatometer % |
| CRITICS_THEHINDU | The Hindu | https://www.thehindu.com | ✅ (Vivek M.V.) | Varies |
| CRITICS_NDTV | NDTV Movies | https://www.ndtv.com | ✅ (3/5 stars) | 5-star |
| CRITICS_THRINDIA | THR India | https://www.hollywoodreporterindia.com/global/reviews/toxic-movie-review-anupama-chopra-thr-india | ✅ (Anupama Chopra) | None (prose) |
| CRITICS_RANGAN_GALATTA | Galatta Plus | https://galattaplus.com/geetu-mohandass-toxic-is-eccentric... | ✅ (Baradwaj Rangan) | None (prose) |
| CRITICS_IGN | IGN | https://www.ign.com | ✅ | 10-point |
| CRITICS_HT | Hindustan Times | https://www.hindustantimes.com | ✅ | Varies |
| CRITICS_INDIANEXPRESS | Indian Express | https://www.indianexpress.com | ✅ | 5-star |
| CRITICS_FIRSTPOST | Firstpost | https://www.firstpost.com | ✅ | Varies |
| CRITICS_DECCANCHRONICLE | Deccan Chronicle | https://www.deccanchronicle.com | ✅ | Varies |

**Not confirmed / excluded:** RogerEbert.com (no review), IndieWire (no review),
Variety (not confirmed), Film Companion (not confirmed — Anupama Chopra now
leads THR India).

#### Why these sources are suitable

- All are established, named publications with identifiable critics.
- Together they provide a mix of pan-Indian, regional, and international
  perspectives appropriate for a film starring a major South Indian star.
- Each review is linkable to a unique URL and dateable to the film's release window.

#### Collection method

**Automated scraping is prohibited** by the terms of service of every source
listed above. Rotten Tomatoes (Fandango ToS) explicitly bans bots, spiders,
and data extractors. All other sites prohibit automated reproduction.

Collection method: **Manual entry** using the provided CSV template at
`data/raw/critics/manual_entry_template.csv`.

Workflow:
1. Visit each publication's review URL directly in a browser.
2. Record the review metadata fields into the template row.
3. Run `scripts/collect_critics.py` to stage the entries.

#### Sampling strategy

Target: 10–20 critic reviews from verified sources.  
No reviews are invented or inferred. If a source cannot be accessed (paywall,
page not found), it is excluded and the exclusion is recorded.

#### Inclusion criteria
- Review must be for `tt27530512` specifically (verified by critic name, film title, year).
- Review must be published by a named critic at a named publication.
- Review URL must be recorded.

#### Exclusion criteria
- Anonymous reviews.
- Reviews of other films titled "Toxic".
- Reviews that cannot be unambiguously attributed to this film.
- Paywalled reviews where full text is inaccessible.

#### Date window
- Release date: 2026 (exact release date to be confirmed at collection time).
- Collection window: open — all reviews published from 2026-01-01 onwards.

#### Potential biases
- Indian publications are over-represented relative to global sources (reflects the film's market).
- Critical reception from non-English-language publications may require translation and may be absent.
- Rotten Tomatoes Tomatometer aggregates reviews but its methodology is opaque.

---

### 2B. IMDb Audience Data

#### Source selection rationale

IMDb is the most widely used film database globally, with verified vote counts
and an aggregate rating (`averageRating` on a 1–10 scale). The official
non-commercial bulk dataset is the only authorised, licence-compliant source
for IMDb data in this project.

**IMDb.com page scraping is explicitly prohibited** by IMDb's terms.

#### Source

- **Official URL:** https://datasets.imdbws.com/
- **Files used:** `title.basics.tsv.gz`, `title.ratings.tsv.gz`
- **Licence:** Personal and non-commercial use only. Attribution required:
  "Information courtesy of IMDb (https://www.imdb.com). Used with permission."
- **Terms:** https://developer.imdb.com/non-commercial-datasets/

#### Data contributed

| Field | Source file | Description |
|---|---|---|
| `tconst` | basics | IMDb title ID (tt27530512) |
| `primaryTitle` | basics | English title |
| `originalTitle` | basics | Original-language title |
| `startYear` | basics | Release year |
| `genres` | basics | Genre tags |
| `runtimeMinutes` | basics | Running time |
| `averageRating` | ratings | Weighted average on 1–10 |
| `numVotes` | ratings | Total vote count |

**Not available via official datasets:** Individual user review text, user
ratings broken down by demographic, or review publication dates.

#### Collection method

Automated download via `scripts/download_imdb.py`. The script:
1. Downloads both TSV.GZ files using `requests` with streaming.
2. Streams through each file line-by-line to find `tt27530512` without
   loading millions of records into memory.
3. Preserves the raw `.tsv.gz` files unchanged.
4. Saves the extracted record to staging as JSON and CSV.

#### Sampling strategy

Single record extraction — only the row with `tconst = tt27530512` is
retained from each file. No fuzzy matching; exact IMDb ID match only.

#### Date window

The IMDb datasets are updated daily. The download timestamp is recorded
in every staging and processed record. Each download creates a new IMDb
snapshot record in the database (historical snapshots are not overwritten).

#### Potential biases

- IMDb votes skew toward frequent internet users and self-selected raters.
- For a 2026 release, vote counts may be very low at the time of first
  collection; the rating may be unstable.
- IMDb does not distinguish between Indian and international voters.

---

### 2C. Reddit Audience Data

#### Source selection rationale

Reddit hosts organic, text-rich audience discussions about films, often in
real time around release. Comments on posts in relevant subreddits provide
informal, unstructured audience opinions that complement the structured
IMDb rating and the professional critic reviews.

#### Access requirements

Reddit changed its API access policy in mid-2023. As of 2026:
- All meaningful API access requires OAuth2 app registration.
- Read-only academic access is available but requires a registered developer app.
- Rate limit: 100 QPM (queries per minute) for OAuth-authenticated free tier.
- **Pushshift is fully shut down** for public/academic use (restricted to
  Reddit internal moderation tools). Do not use Pushshift or PSAW.
- PRAW (python-praw) is the standard compliant library.

**To enable Reddit collection:**
1. Register a "script" type app at https://www.reddit.com/prefs/apps
2. Set `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT` in `.env`.
3. Set `reddit.enabled: true` in `config/settings.yaml`.

If credentials are absent, the collector fails with a clear error message and
does not substitute any other data source.

#### Data contributed

| Field | Description |
|---|---|
| `post_id` | Reddit post ID |
| `subreddit` | Subreddit name |
| `post_title` | Post title text |
| `post_text` | Post body text (NULL if link post or deleted) |
| `post_score` | Upvote score at time of retrieval |
| `comment_count` | Number of comments at retrieval time |
| `thread_url` | Permalink URL |
| `post_timestamp` | UTC datetime of post creation |
| `comment_id` | Comment ID |
| `parent_id` | Parent post or comment ID |
| `comment_text` | Comment body text (NULL if deleted/removed) |
| `comment_score` | Comment upvote score |

**Not collected:** Usernames, profile URLs, user history, or any other
personally identifying information.

#### Collection method

`scripts/collect_reddit.py` using PRAW in `read_only=True` mode.

Subreddits searched: `r/bollywood`, `r/tollywood`, `r/india`, `r/movies`,
`r/worldcinema`, `r/netflix`.

Search terms: "Toxic Yash movie", "Toxic Fairytale Grown-Ups", "tt27530512",
"Toxic Geetu Mohandas".

#### Sampling strategy

Up to 100 threads per search, up to 500 comments per thread (configurable).
Duplicate post IDs are dropped. Posts from outside the 2026 date window are
included only if they are explicitly about the 2026 film (verified by context).

#### Privacy considerations

- Usernames are not collected or stored.
- Deleted and removed post text is preserved as `NULL` with `is_deleted=1`.
- No attempt is made to re-identify authors.
- Data is used for non-commercial academic research only.

#### Date window

- `start: 2026-01-01` | `end: 2026-12-31` (configurable in `settings.yaml`).

#### Potential biases

- English-language subreddits only; Kannada/Hindi Reddit communities may be under-represented.
- Reddit users skew younger and more internet-fluent than the general filmgoing population.
- Thread scores reflect engagement (controversy + agreement) not simply sentiment.
- Deleted posts create non-random gaps in the dataset.

---

### 2D. Wikipedia Action API (Live REST API)

#### Source selection rationale
The MediaWiki / Wikipedia Action API (`https://en.wikipedia.org/w/api.php`) is a 100% free,
open, and fully legally compliant REST API that returns structured and semi-structured
native JSON. It provides auditable encyclopedic documentation of the film's verified
critical reception, box office performance, production details, and audience response.

#### Source & Licensing
- **API Endpoint:** `https://en.wikipedia.org/w/api.php`
- **Target Page:** `Toxic_(2026_film)` (MediaWiki Page ID: `78832995`)
- **Format:** `application/json`
- **Licence:** Creative Commons Attribution-ShareAlike 4.0 (CC BY-SA 4.0).
- **Access Restrictions:** None. No API key, no OAuth tokens, no paid subscriptions, and no credit card required.

#### Data contributed
- Canonical Page Title, Page ID, and Canonical Article URL
- MediaWiki Revision ID and Revision Timestamp (for absolute historical auditability)
- Full plain-text extract (`explaintext=1`)
- Isolated 'Reception' and 'Critical response' sections detailing consensus from major outlets

#### Collection method
Automated collection via `scripts/collect_wikipedia.py` using `requests` with custom User-Agent.
Raw API response is saved verbatim to `data/raw/wikipedia/wikipedia_toxic_2026_raw.json`.
Structured records are staged to JSON and CSV, then cleaned by `scripts/clean_wikipedia.py`.

#### Limitations
Wikipedia articles are subject to collaborative community editing over time.
To guarantee reproducibility, the specific `revision_id` (`revid: 1386737157`) and
`revision_timestamp` are preserved in every record and database row.

---

## 3. Reproducibility

- Raw data is never overwritten.
- All collection timestamps are preserved.
- The `config/settings.yaml` file and `docs/source_register.csv` document
  the exact parameters used at collection time.
- The `logs/collection_log.csv` records each operation's row counts and status.
- Re-running any script produces the same output given the same inputs.

---

## 4. Missing Data Strategy

| Scenario | Action |
|---|---|
| Missing numeric rating | Preserve record; set `rating_normalized = NULL` |
| Missing review text | Preserve record if other metadata exists |
| Missing review date | Preserve as `NULL` |
| Missing rating scale | Do NOT normalize; preserve raw rating only |
| Ambiguous film match | Flag `match_status = 'ambiguous'`; exclude from main load |
| Deleted Reddit post/comment | Preserve with `is_deleted = 1`, text = `NULL` |
| IMDb film not yet indexed | Log warning; exit with error; do not substitute data |
| Reddit credentials absent | Exit with error; do not substitute data |

Missing values are **never replaced with zero** in numeric fields.
