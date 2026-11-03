import json

from grammarfixer import config


def test_defaults_when_missing(tmp_path):
    cfg = config.load_config(str(tmp_path / "nope.json"))
    assert cfg == config.DEFAULT_CFG
    assert cfg["api_key"] == ""


def test_roundtrip(tmp_path):
    path = str(tmp_path / "sub" / "config.json")
    cfg = dict(config.DEFAULT_CFG, api_key="abc", letter="G")
    config.save_config(cfg, path)
    assert config.load_config(path) == cfg


def test_old_config_is_upgraded(tmp_path):
    # Config written by the original single-file version.
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"api_key": "k", "model": "gemini-2.5-flash",
                                "letter": "o", "prompt": "Fix:\n\n"}))
    cfg = config.load_config(str(path))
    assert cfg["provider"] == "gemini"
    assert cfg["letter"] == "O"
    assert cfg["excluded_apps"] == config.DEFAULT_EXCLUDED_APPS


def test_invalid_values_fall_back(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"provider": "nope", "letter": "A"}))
    cfg = config.load_config(str(path))
    assert cfg["provider"] == "gemini"
    assert cfg["letter"] == "O"


def test_corrupt_file(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{not json")
    assert config.load_config(str(path)) == config.DEFAULT_CFG


def test_api_key_env_fallback(monkeypatch):
    monkeypatch.delenv("GRAMMARFIXER_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "from-env")
    cfg = dict(config.DEFAULT_CFG)
    assert config.api_key(cfg) == "from-env"
    assert not config.needs_setup(cfg)
    assert config.api_key(dict(cfg, api_key="explicit")) == "explicit"


def test_ollama_never_needs_setup(monkeypatch):
    monkeypatch.delenv("GRAMMARFIXER_API_KEY", raising=False)
    assert not config.needs_setup(dict(config.DEFAULT_CFG, provider="ollama"))
