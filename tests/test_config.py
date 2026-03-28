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


import json
import config as config_module
from config import load_settings, save_settings, save_env_config


def test_load_settings_returns_defaults_when_no_file(tmp_path, monkeypatch):
    """load_settings() returns sensible defaults when settings.json is absent."""
    monkeypatch.setattr(config_module, "SETTINGS_PATH", tmp_path / "settings.json")
    result = load_settings()
    assert result["panel_title"] == "朱鸿宇的AI翻译助手"
    assert result["prompt_history"] == []
    assert len(result["system_prompt"]) > 20  # non-empty default prompt


def test_load_settings_reads_existing_file(tmp_path, monkeypatch):
    """load_settings() returns values from settings.json when it exists."""
    f = tmp_path / "settings.json"
    f.write_text(
        '{"panel_title":"My Bot","system_prompt":"Be helpful.","prompt_history":["old"]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(config_module, "SETTINGS_PATH", f)
    result = load_settings()
    assert result["panel_title"] == "My Bot"
    assert result["system_prompt"] == "Be helpful."
    assert result["prompt_history"] == ["old"]


def test_save_settings_roundtrip(tmp_path, monkeypatch):
    """save_settings() writes JSON that load_settings() can read back."""
    f = tmp_path / "settings.json"
    monkeypatch.setattr(config_module, "SETTINGS_PATH", f)
    data = {
        "panel_title": "Test Panel",
        "system_prompt": "You are a test.",
        "prompt_history": ["p1", "p2"],
    }
    save_settings(data)
    raw = json.loads(f.read_text(encoding="utf-8"))
    assert raw["panel_title"] == "Test Panel"
    assert raw["prompt_history"] == ["p1", "p2"]


def test_save_env_config_creates_new_entries(tmp_path, monkeypatch):
    """save_env_config() writes all three keys when .env is empty."""
    env_file = tmp_path / ".env"
    env_file.write_text("", encoding="utf-8")
    monkeypatch.setattr(config_module, "ENV_PATH", env_file)
    save_env_config("new-key", "https://new-api.com/v1", "new-model")
    content = env_file.read_text(encoding="utf-8")
    assert "KIMI_API_KEY=new-key" in content
    assert "KIMI_API_BASE=https://new-api.com/v1" in content
    assert "KIMI_MODEL=new-model" in content


def test_save_env_config_updates_existing_keys(tmp_path, monkeypatch):
    """save_env_config() overwrites existing keys and preserves unrelated lines."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "KIMI_API_KEY=old-key\nKIMI_API_BASE=old-base\nOTHER=keep\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config_module, "ENV_PATH", env_file)
    save_env_config("new-key", "new-base", "new-model")
    content = env_file.read_text(encoding="utf-8")
    assert "KIMI_API_KEY=new-key" in content
    assert "KIMI_API_BASE=new-base" in content
    assert "KIMI_MODEL=new-model" in content
    assert "OTHER=keep" in content
    assert "old-key" not in content


def test_load_config_returns_model(tmp_path, monkeypatch):
    """load_config() now includes 'model' key in returned dict."""
    monkeypatch.delenv("KIMI_API_KEY", raising=False)
    monkeypatch.delenv("KIMI_API_BASE", raising=False)
    monkeypatch.delenv("KIMI_MODEL", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("KIMI_API_KEY=sk-test\nKIMI_MODEL=my-model\n")
    monkeypatch.chdir(tmp_path)
    from config import load_config
    result = load_config(str(env_file))
    assert result["model"] == "my-model"


def test_load_config_model_defaults_to_kimi_k25(tmp_path, monkeypatch):
    """load_config() returns 'kimi-k2.5' as default model when KIMI_MODEL is absent."""
    monkeypatch.delenv("KIMI_API_KEY", raising=False)
    monkeypatch.delenv("KIMI_API_BASE", raising=False)
    monkeypatch.delenv("KIMI_MODEL", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("KIMI_API_KEY=sk-test\n")
    monkeypatch.chdir(tmp_path)
    from config import load_config
    result = load_config(str(env_file))
    assert result["model"] == "kimi-k2.5"


# ── API history tests ─────────────────────────────────────────────────────────

def test_load_settings_includes_empty_api_history_by_default(tmp_path, monkeypatch):
    """load_settings() returns api_history=[] when settings.json is absent."""
    monkeypatch.setattr(config_module, "SETTINGS_PATH", tmp_path / "settings.json")
    result = load_settings()
    assert result["api_history"] == []


def test_load_settings_reads_api_history(tmp_path, monkeypatch):
    """load_settings() returns api_history list from existing settings.json."""
    f = tmp_path / "settings.json"
    history = [{"api_key": "sk-a", "api_base": "https://a.com/v1", "model": "m1"}]
    f.write_text(json.dumps({"api_history": history}), encoding="utf-8")
    monkeypatch.setattr(config_module, "SETTINGS_PATH", f)
    result = load_settings()
    assert result["api_history"] == history


def test_save_settings_persists_api_history(tmp_path, monkeypatch):
    """save_settings() writes api_history to settings.json and load_settings() reads it back."""
    f = tmp_path / "settings.json"
    monkeypatch.setattr(config_module, "SETTINGS_PATH", f)
    history = [
        {"api_key": "sk-1", "api_base": "https://one.com/v1", "model": "model-a"},
        {"api_key": "sk-2", "api_base": "https://two.com/v1", "model": "model-b"},
    ]
    save_settings({"api_history": history})
    raw = json.loads(f.read_text(encoding="utf-8"))
    assert raw["api_history"] == history
