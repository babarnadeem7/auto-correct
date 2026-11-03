# Contributing

Thanks for helping out! Bug reports, ideas and pull requests are all welcome.

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/grammarfixer.git
cd grammarfixer
python -m venv .venv && .venv\Scripts\activate
pip install -e ".[dev]"
python -m grammarfixer     # runs with a console, so you can see errors
```

## Before opening a PR

- `ruff check .` passes
- `pytest` passes, and new logic comes with tests (provider, config and hotkey logic are
  designed to be testable without Windows APIs)
- Keep the app small: one hotkey, one job

## Project layout

| File | What it does |
|---|---|
| `grammarfixer/app.py` | Tray icon, menu, entry point |
| `grammarfixer/hotkey.py` | Global Ctrl+A+letter detection (keyboard hook) |
| `grammarfixer/fixer.py` | Select → copy → correct → paste workflow |
| `grammarfixer/providers.py` | Gemini and OpenAI-compatible backends |
| `grammarfixer/config.py` | Defaults, presets, load/save |
| `grammarfixer/settings_ui.py` | Tkinter settings window |
| `grammarfixer/winapi.py` | Win32 helpers (foreground window, autostart, single instance) |

## Ideas for contributions

- Undo the last correction (keep the original text and restore it with a hotkey)
- Show a diff or preview popup before replacing
- "Fix selection only" mode (no Ctrl+A)
- Store the API key in Windows Credential Manager (`keyring`)
- macOS / Linux support
