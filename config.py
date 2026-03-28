import os
from pathlib import Path

from dotenv import load_dotenv


def load_config(env_path: str = ".env") -> dict:
    """Load and validate configuration from .env file.

    Returns dict with keys: api_key, api_base.
    Raises FileNotFoundError if .env missing, ValueError if keys invalid.
    """
    env_file = Path(env_path)
    if not env_file.exists():
        raise FileNotFoundError(f".env file not found at: {env_path}")

    load_dotenv(env_file, override=True)

    api_key = os.getenv("KIMI_API_KEY", "").strip()
    api_base = os.getenv("KIMI_API_BASE", "https://api.moonshot.cn/v1").strip()

    if not api_key:
        raise ValueError("KIMI_API_KEY is missing or empty in .env file")

    if not api_base:
        raise ValueError("KIMI_API_BASE is empty in .env file")

    return {
        "api_key": api_key,
        "api_base": api_base,
    }
