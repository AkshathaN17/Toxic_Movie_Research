"""Reddit data collector using official PRAW OAuth. Fails gracefully if unconfigured."""
import os
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

FILM_ID = "TOXIC_2026"
REQUIRED_ENV = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT"]


def check_reddit_access() -> bool:
    """Check if Reddit OAuth credentials are configured. Returns True if ready."""
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        logger.error(
            "Reddit collection is DISABLED. Missing environment variables: %s. "
            "Set these in your .env file and ensure your Reddit app has been approved. "
            "See docs/data_collection_plan.md for access requirements.",
            ", ".join(missing),
        )
        return False
    return True


def get_praw_reddit():
    """Initialize and return a read-only PRAW Reddit instance."""
    try:
        import praw
    except ImportError:
        raise ImportError("praw is not installed. Run: pip install praw")
    if not check_reddit_access():
        raise EnvironmentError(
            "Reddit OAuth credentials not configured. Cannot initialize PRAW. "
            "Configure REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT in .env"
        )
    return praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ["REDDIT_USER_AGENT"],
        read_only=True,
    )


def _clean_post(submission, film_id: str = FILM_ID, retrieval_ts: str = None) -> dict:
    """Extract fields from a PRAW submission, excluding personal info."""
    retrieval_ts = retrieval_ts or datetime.now(timezone.utc).isoformat()
    text = submission.selftext
    if text in ("[deleted]", "[removed]", ""):
        text = None
    is_deleted = int(submission.selftext in ("[deleted]", "[removed]"))
    return {
        "post_id": submission.id,
        "film_id": film_id,
        "thread_id": submission.id,
        "subreddit": str(submission.subreddit),
        "post_title": submission.title,
        "post_text": text,
        "post_score": submission.score,
        "comment_count": submission.num_comments,
        "thread_url": f"https://www.reddit.com{submission.permalink}",
        "post_timestamp": datetime.fromtimestamp(
            submission.created_utc, tz=timezone.utc
        ).isoformat(),
        "retrieval_timestamp": retrieval_ts,
        "is_deleted": is_deleted,
        "match_status": "verified",
    }


def _clean_comment(
    comment, post_id: str, film_id: str = FILM_ID, retrieval_ts: str = None
) -> Optional[dict]:
    """Extract fields from a PRAW comment, excluding personal info."""
    import praw.models

    if not isinstance(comment, praw.models.Comment):
        return None
    retrieval_ts = retrieval_ts or datetime.now(timezone.utc).isoformat()
    text = comment.body
    if text in ("[deleted]", "[removed]", ""):
        text = None
    is_deleted = int(comment.body in ("[deleted]", "[removed]"))
    return {
        "comment_id": comment.id,
        "post_id": post_id,
        "film_id": film_id,
        "parent_id": comment.parent_id,
        "subreddit": str(comment.subreddit),
        "comment_text": text,
        "comment_score": comment.score,
        "comment_timestamp": datetime.fromtimestamp(
            comment.created_utc, tz=timezone.utc
        ).isoformat(),
        "retrieval_timestamp": retrieval_ts,
        "is_deleted": is_deleted,
    }


def collect_reddit(config: dict, raw_dir: str, delay: float = 2.0) -> dict:
    """
    Main Reddit collection entry point.
    Returns {"posts": [...], "comments": [...], "status": "success"|"disabled"|"error"}
    If credentials not configured, returns status="disabled" immediately.
    """
    if not check_reddit_access():
        return {
            "posts": [],
            "comments": [],
            "status": "disabled",
            "message": "Reddit collection requires OAuth credentials. See .env.example.",
        }

    reddit_cfg = config.get("reddit", {})
    if not reddit_cfg.get("enabled", False):
        logger.warning(
            "Reddit collection is disabled in config (reddit.enabled=false). "
            "Enable it after configuring credentials."
        )
        return {
            "posts": [],
            "comments": [],
            "status": "disabled",
            "message": "Reddit collection disabled in config/settings.yaml (reddit.enabled=false).",
        }

    try:
        reddit = get_praw_reddit()
    except Exception as e:
        logger.error("Failed to initialize Reddit client: %s", e)
        return {"posts": [], "comments": [], "status": "error", "message": str(e)}

    raw_path = Path(raw_dir)
    raw_path.mkdir(parents=True, exist_ok=True)

    subreddits = reddit_cfg.get("subreddits", [])
    search_terms = reddit_cfg.get("search_terms", [])
    max_threads = reddit_cfg.get("max_threads", 100)
    max_comments = reddit_cfg.get("max_comments_per_thread", 500)

    all_posts = []
    all_comments = []
    seen_post_ids = set()
    retrieval_ts = datetime.now(timezone.utc).isoformat()

    for subreddit_name in subreddits:
        for term in search_terms:
            logger.info("Searching r/%s for '%s'", subreddit_name, term)
            try:
                sub = reddit.subreddit(subreddit_name)
                results = sub.search(
                    term, sort="relevance", time_filter="all", limit=max_threads
                )
                for submission in results:
                    if submission.id in seen_post_ids:
                        continue
                    seen_post_ids.add(submission.id)
                    post_data = _clean_post(submission, retrieval_ts=retrieval_ts)
                    all_posts.append(post_data)

                    # Collect comments
                    submission.comments.replace_more(limit=0)
                    comment_count = 0
                    for comment in submission.comments.list():
                        if comment_count >= max_comments:
                            break
                        c = _clean_comment(
                            comment, post_id=submission.id, retrieval_ts=retrieval_ts
                        )
                        if c:
                            all_comments.append(c)
                            comment_count += 1

                    # Save raw JSONL incrementally
                    with open(raw_path / "reddit_raw.jsonl", "a", encoding="utf-8") as f:
                        f.write(
                            json.dumps({"type": "post", "data": post_data}) + "\n"
                        )

                    time.sleep(delay)
            except Exception as e:
                logger.warning(
                    "Error searching r/%s for '%s': %s", subreddit_name, term, e
                )

    logger.info(
        "Reddit collection complete: %d posts, %d comments",
        len(all_posts),
        len(all_comments),
    )
    return {"posts": all_posts, "comments": all_comments, "status": "success"}
