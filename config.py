import json
import os
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent / ".env"
SETTINGS_PATH = Path(__file__).parent / "settings.json"

DEFAULT_SYSTEM_PROMPT = (
    "你是一个智能视觉助手。请分析用户提供的图片。"
    "如果图片主体是普通英文文本，请提供信达雅的中文翻译。"
    "如果图片主体是编程代码，请提供深度的代码解析"
    "（包含编程逻辑、语法解析、关键函数分析）。"
    "使用 Markdown 格式输出。"
)

_DEFAULT_SETTINGS = {
    "panel_title": "朱鸿宇的AI翻译助手",
    "system_prompt": DEFAULT_SYSTEM_PROMPT,
    "prompt_history": [],
    "api_history": [],
}


def load_config(env_path: str = ".env") -> dict:
    """Load and validate configuration from .env file.

    Returns dict with keys: api_key, api_base, model.
    Raises FileNotFoundError if .env missing, ValueError if keys invalid.
    """
    env_file = Path(env_path)
    if not env_file.exists():
        raise FileNotFoundError(f".env file not found at: {env_path}")

    load_dotenv(env_file, override=True)

    api_key = os.getenv("KIMI_API_KEY", "").strip()
    api_base = os.getenv("KIMI_API_BASE", "https://api.moonshot.cn/v1").strip()
    model = os.getenv("KIMI_MODEL", "kimi-k2.5").strip() or "kimi-k2.5"

    if not api_key:
        raise ValueError("KIMI_API_KEY is missing or empty in .env file")

    if not api_base:
        raise ValueError("KIMI_API_BASE is empty in .env file")

    return {
        "api_key": api_key,
        "api_base": api_base,
        "model": model,
    }


def load_settings() -> dict:
    """Load UI settings from settings.json. Returns defaults if file absent."""
    if not SETTINGS_PATH.exists():
        return dict(_DEFAULT_SETTINGS)
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        return {**_DEFAULT_SETTINGS, **data}
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULT_SETTINGS)


def save_settings(data: dict) -> None:
    """Write panel_title / system_prompt / prompt_history / api_history to settings.json."""
    payload = {
        "panel_title": data.get("panel_title", _DEFAULT_SETTINGS["panel_title"]),
        "system_prompt": data.get("system_prompt", _DEFAULT_SETTINGS["system_prompt"]),
        "prompt_history": data.get("prompt_history", []),
        "api_history": data.get("api_history", []),
    }
    SETTINGS_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def remove_api_history_entry(history: list[dict], index: int) -> list[dict]:
    """Return a new list with the entry at `index` removed. No-op for invalid index."""
    if 0 <= index < len(history):
        return history[:index] + history[index + 1:]
    return list(history)


def save_env_config(api_key: str, api_base: str, model: str) -> None:
    """Update KIMI_API_KEY / KIMI_API_BASE / KIMI_MODEL in .env file in-place."""
    lines: list[str] = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()

    targets = {"KIMI_API_KEY": api_key, "KIMI_API_BASE": api_base, "KIMI_MODEL": model}
    updated: set[str] = set()
    new_lines: list[str] = []
    for line in lines:
        replaced = False
        for key, val in targets.items():
            if line.startswith(f"{key}=") or line.startswith(f"{key} ="):
                new_lines.append(f"{key}={val}")
                updated.add(key)
                replaced = True
                break
        if not replaced:
            new_lines.append(line)

    for key, val in targets.items():
        if key not in updated:
            new_lines.append(f"{key}={val}")

    ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
