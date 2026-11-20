"""MySQL database loading for Toxic 2026 pipeline."""
import logging
import pymysql
from sqlalchemy import create_engine, text
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

logger = logging.getLogger(__name__)

FILM_ID = "TOXIC_2026"
IMDB_ID = "tt27530512"


def get_engine(host, port, user, password, database):
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
    return create_engine(url)


def run_schema(engine, schema_path: str):
    """Execute schema.sql to create/ensure all tables exist."""
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()
    with engine.begin() as conn:
        for statement in sql.split(";"):
            stmt = statement.strip()
            if stmt:
                conn.execute(text(stmt))
    logger.info("Schema applied from %s", schema_path)


def upsert_film(engine, record: dict):
    """Insert canonical film record if not exists."""
    sql = """
        INSERT IGNORE INTO films
            (film_id, imdb_id, canonical_title, primary_title, original_title,
             release_year, director, starring, genres, runtime_minutes)
        VALUES
            (:film_id, :imdb_id, :canonical_title, :primary_title, :original_title,
             :release_year, :director, :starring, :genres, :runtime_minutes)
    """
    with engine.begin() as conn:
        conn.execute(text(sql), record)
    logger.info("Upserted film record: %s", record.get("film_id"))


def insert_imdb_snapshot(engine, record: dict):
    """Insert IMDb snapshot. Each download creates a new snapshot row."""
    sql = """
        INSERT INTO imdb_snapshots
            (film_id, imdb_id, average_rating, num_votes, primary_title, original_title,
             release_year, genres, runtime_minutes, source_file_basics, source_file_ratings,
             dataset_download_timestamp, retrieval_timestamp)
        VALUES
            (:film_id, :imdb_id, :average_rating, :num_votes, :primary_title, :original_title,
             :release_year, :genres, :runtime_minutes, :source_file_basics, :source_file_ratings,
             :dataset_download_timestamp, :retrieval_timestamp)
    """
    with engine.begin() as conn:
        conn.execute(text(sql), record)
    logger.info("Inserted IMDb snapshot for %s", record.get("imdb_id"))


def insert_critic_reviews(engine, df: pd.DataFrame):
    """Insert critic reviews. Skip duplicates by review_id."""
    inserted = 0
    skipped = 0
    sql = """
        INSERT IGNORE INTO critic_reviews
            (review_id, film_id, publication, critic_name, review_date, rating_raw,
             rating_scale, rating_normalized, review_text, review_url, collection_date,
             collection_method, source_id, match_status)
        VALUES
            (:review_id, :film_id, :publication, :critic_name, :review_date, :rating_raw,
             :rating_scale, :rating_normalized, :review_text, :review_url, :collection_date,
             :collection_method, :source_id, :match_status)
    """
    for _, row in df.iterrows():
        with engine.begin() as conn:
            result = conn.execute(text(sql), row.to_dict())
            if result.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
    logger.info(
        "Critic reviews: %d inserted, %d skipped (duplicates)", inserted, skipped
    )
    return inserted, skipped


def insert_reddit_posts(engine, df: pd.DataFrame):
    """Insert Reddit posts. Skip duplicates by post_id."""
    inserted = skipped = 0
    sql = """
        INSERT IGNORE INTO reddit_posts
            (post_id, film_id, thread_id, subreddit, post_title, post_text, post_score,
             comment_count, thread_url, post_timestamp, retrieval_timestamp, is_deleted, match_status)
        VALUES
            (:post_id, :film_id, :thread_id, :subreddit, :post_title, :post_text, :post_score,
             :comment_count, :thread_url, :post_timestamp, :retrieval_timestamp, :is_deleted, :match_status)
    """
    for _, row in df.iterrows():
        with engine.begin() as conn:
            result = conn.execute(text(sql), row.to_dict())
            inserted += result.rowcount
    logger.info("Reddit posts: %d inserted, %d skipped", inserted, skipped)
    return inserted, skipped


def insert_reddit_comments(engine, df: pd.DataFrame):
    """Insert Reddit comments. Skip duplicates by comment_id."""
    inserted = 0
    sql = """
        INSERT IGNORE INTO reddit_comments
            (comment_id, post_id, film_id, parent_id, subreddit, comment_text, comment_score,
             comment_timestamp, retrieval_timestamp, is_deleted)
        VALUES
            (:comment_id, :post_id, :film_id, :parent_id, :subreddit, :comment_text, :comment_score,
             :comment_timestamp, :retrieval_timestamp, :is_deleted)
    """
    for _, row in df.iterrows():
        with engine.begin() as conn:
            result = conn.execute(text(sql), row.to_dict())
            inserted += result.rowcount
    logger.info("Reddit comments: %d inserted", inserted)
    return inserted


def insert_wikipedia_snapshot(engine, record: dict):
    """Insert Wikipedia snapshot. Each collection run creates a historical snapshot."""
    sql = """
        INSERT INTO wikipedia_snapshots
            (film_id, page_id, page_title, page_url, revision_id, revision_timestamp,
             full_extract, reception_text, critical_response_text, retrieval_timestamp)
        VALUES
            (:film_id, :page_id, :page_title, :page_url, :revision_id, :revision_timestamp,
             :full_extract, :reception_text, :critical_response_text, :retrieval_timestamp)
    """
    with engine.begin() as conn:
        conn.execute(text(sql), record)
    logger.info("Inserted Wikipedia snapshot for page %s (id %s)", record.get("page_title"), record.get("page_id"))
