"""Loading and saving the user configuration (stored in %APPDATA%\\GrammarFixer)."""
import json
import os

from . import APP_NAME

CFG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME)
CFG_FILE = os.path.join(CFG_DIR, "config.json")
LOG_FILE = os.path.join(CFG_DIR, "log.txt")

DEFAULT_PROMPT = (
    "Fix the grammar, spelling and punctuation of the text the user sends. "
    "Keep the same language, tone, meaning and formatting (line breaks, lists, "
    "emojis). If the text mixes languages or is written in a romanized form "
    "(for example Roman Urdu or Hinglish), keep it that way. "
    "Do not add explanations, quotes or anything else. Return only the corrected text."
)

# Provider presets. "gemini" speaks the Google Gemini API, everything else
# speaks the OpenAI-compatible /chat/completions API.
PRESETS = {
    "gemini": {
        "label": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "model": "gemini-2.5-flash",
        "needs_key": True,
        "env": "GEMINI_API_KEY",
    },
    "openai": {
        "label": "OpenAI / OpenAI-compatible",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "needs_key": True,
        "env": "OPENAI_API_KEY",
    },
    "ollama": {
        "label": "Ollama (local, offline)",
        "base_url": "http://localhost:11434/v1",
        "model": "llama3.2",
        "needs_key": False,
        "env": None,
    },
}

DEFAULT_EXCLUDED_APPS = [
    # Terminals: Ctrl+A / Ctrl+C mean something else there.
    "windowsterminal.exe", "cmd.exe", "powershell.exe", "pwsh.exe",
    "conhost.exe", "wezterm-gui.exe", "alacritty.exe", "mintty.exe",
]

DEFAULT_CFG = {
    "provider": "gemini",
    "api_key": "",
    "base_url": PRESETS["gemini"]["base_url"],
    "model": PRESETS["gemini"]["model"],
    "letter": "O",  # hotkey = Ctrl + A + this letter
    "prompt": DEFAULT_PROMPT,
    "temperature": 0.2,
    "timeout": 30,
    "max_chars": 10000,
    "excluded_apps": DEFAULT_EXCLUDED_APPS,
}


def load_config(path: str = CFG_FILE) -> dict:
    cfg = dict(DEFAULT_CFG)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            cfg.update(data)
    except (OSError, ValueError):
        pass
    if cfg.get("provider") not in PRESETS:
        cfg["provider"] = DEFAULT_CFG["provider"]
    letter = str(cfg.get("letter", "")).strip().upper()[:1]
    cfg["letter"] = letter if letter.isalpha() and letter != "A" else DEFAULT_CFG["letter"]
    return cfg


def save_config(cfg: dict, path: str = CFG_FILE):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def api_key(cfg: dict) -> str:
    """API key from the config, falling back to environment variables."""
    key = (cfg.get("api_key") or "").strip()
    if key:
        return key
    env = PRESETS[cfg["provider"]]["env"]
    return os.environ.get("GRAMMARFIXER_API_KEY") or (os.environ.get(env, "") if env else "")


def needs_setup(cfg: dict) -> bool:
    return PRESETS[cfg["provider"]]["needs_key"] and not api_key(cfg)
