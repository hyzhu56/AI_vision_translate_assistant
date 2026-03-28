import os
import pytest


def test_load_config_success(tmp_path, monkeypatch):
    """Valid .env file loads both keys correctly."""
    env_file = tmp_path / ".env"
    env_file.write_text("KIMI_API_KEY=sk-test123\nKIMI_API_BASE=https://api.moonshot.cn/v1\n")
    monkeypatch.chdir(tmp_path)

    from config import load_config

    cfg = load_config(str(env_file))
    assert cfg["api_key"] == "sk-test123"
    assert cfg["api_base"] == "https://api.moonshot.cn/v1"


def test_load_config_missing_file(tmp_path, monkeypatch):
    """Missing .env file raises FileNotFoundError."""
    monkeypatch.chdir(tmp_path)

    from config import load_config

    with pytest.raises(FileNotFoundError, match=".env"):
        load_config(str(tmp_path / ".env"))


def test_load_config_empty_key(tmp_path, monkeypatch):
    """Empty KIMI_API_KEY raises ValueError."""
    env_file = tmp_path / ".env"
    env_file.write_text("KIMI_API_KEY=\nKIMI_API_BASE=https://api.moonshot.cn/v1\n")
    monkeypatch.chdir(tmp_path)

    from config import load_config

    with pytest.raises(ValueError, match="KIMI_API_KEY"):
        load_config(str(env_file))


def test_load_config_missing_key(tmp_path, monkeypatch):
    """Missing KIMI_API_KEY raises ValueError."""
    env_file = tmp_path / ".env"
    env_file.write_text("KIMI_API_BASE=https://api.moonshot.cn/v1\n")
    monkeypatch.chdir(tmp_path)

    from config import load_config

    with pytest.raises(ValueError, match="KIMI_API_KEY"):
        load_config(str(env_file))
