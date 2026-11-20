"""Configuration management for Toxic 2026 pipeline."""
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def load_config(config_path: str = None) -> dict:
    """Load configuration from YAML file."""
    if config_path is None:
        base = Path(__file__).parent.parent.parent
        for name in ["config/settings.yaml", "config/settings.example.yaml"]:
            p = base / name
            if p.exists():
                config_path = str(p)
                break
    if config_path is None:
        raise FileNotFoundError(
            "No settings.yaml found. Copy config/settings.example.yaml to config/settings.yaml and configure it."
        )
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_env(key: str, required: bool = True) -> str:
    """Get an environment variable, raising clearly if missing and required."""
    val = os.environ.get(key)
    if val is None and required:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. See .env.example."
        )
    return val


FILM_ID = "TOXIC_2026"
IMDB_ID = "tt27530512"
CANONICAL_TITLE = "Toxic: A Fairytale for Grown-Ups"
RELEASE_YEAR = 2026
