import pytest


def test_load_config_success(tmp_path, monkeypatch):
    """Valid .env file loads both keys correctly."""
    monkeypatch.delenv("KIMI_API_KEY", raising=False)
    monkeypatch.delenv("KIMI_API_BASE", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("KIMI_API_KEY=sk-test123\nKIMI_API_BASE=https://api.moonshot.cn/v1\n")
    monkeypatch.chdir(tmp_path)

    from config import load_config

    cfg = load_config(str(env_file))
    assert cfg["api_key"] == "sk-test123"
    assert cfg["api_base"] == "https://api.moonshot.cn/v1"


def test_load_config_default_api_base(tmp_path, monkeypatch):
    """When KIMI_API_BASE is absent, defaults to moonshot endpoint."""
    monkeypatch.delenv("KIMI_API_KEY", raising=False)
    monkeypatch.delenv("KIMI_API_BASE", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("KIMI_API_KEY=sk-test123\n")
    monkeypatch.chdir(tmp_path)

    from config import load_config

    cfg = load_config(str(env_file))
    assert cfg["api_base"] == "https://api.moonshot.cn/v1"


def test_load_config_missing_file(tmp_path, monkeypatch):
    """Missing .env file raises FileNotFoundError."""
    monkeypatch.delenv("KIMI_API_KEY", raising=False)
    monkeypatch.delenv("KIMI_API_BASE", raising=False)
    monkeypatch.chdir(tmp_path)

    from config import load_config

    with pytest.raises(FileNotFoundError, match=".env"):
        load_config(str(tmp_path / ".env"))


def test_load_config_empty_key(tmp_path, monkeypatch):
    """Empty KIMI_API_KEY raises ValueError."""
    monkeypatch.delenv("KIMI_API_KEY", raising=False)
    monkeypatch.delenv("KIMI_API_BASE", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("KIMI_API_KEY=\nKIMI_API_BASE=https://api.moonshot.cn/v1\n")
    monkeypatch.chdir(tmp_path)

    from config import load_config

    with pytest.raises(ValueError, match="KIMI_API_KEY"):
        load_config(str(env_file))


def test_load_config_missing_key(tmp_path, monkeypatch):
    """Missing KIMI_API_KEY raises ValueError."""
    monkeypatch.delenv("KIMI_API_KEY", raising=False)
    monkeypatch.delenv("KIMI_API_BASE", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("KIMI_API_BASE=https://api.moonshot.cn/v1\n")
    monkeypatch.chdir(tmp_path)

    from config import load_config

    with pytest.raises(ValueError, match="KIMI_API_KEY"):
        load_config(str(env_file))


def test_load_config_empty_api_base(tmp_path, monkeypatch):
    """Whitespace-only KIMI_API_BASE raises ValueError."""
    monkeypatch.delenv("KIMI_API_KEY", raising=False)
    monkeypatch.delenv("KIMI_API_BASE", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("KIMI_API_KEY=sk-test123\nKIMI_API_BASE=   \n")
    monkeypatch.chdir(tmp_path)

    from config import load_config

    with pytest.raises(ValueError, match="KIMI_API_BASE"):
        load_config(str(env_file))
