<div align="center">

# ✔ GrammarFixer

**Fix the grammar of any text box on Windows, in any app, with one hotkey.**

Press <kbd>Ctrl</kbd> + <kbd>A</kbd> + <kbd>O</kbd> and the text you're typing gets corrected in place.
Works in Chrome, Slack, WhatsApp, Word, Notepad, Discord, email, and anywhere else you can type.

[![CI](https://github.com/YOUR_USERNAME/grammarfixer/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/grammarfixer/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/YOUR_USERNAME/grammarfixer)](https://github.com/YOUR_USERNAME/grammarfixer/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Platform](https://img.shields.io/badge/platform-Windows-0078d6)

<!-- Record a short GIF (e.g. with ScreenToGif) and save it as docs/demo.gif -->
<!-- ![demo](docs/demo.gif) -->

</div>

---

## Why?

Grammar checkers usually only work inside one website or need a browser extension.
GrammarFixer is a tiny tray app that works **system-wide**: no copy-pasting into ChatGPT, no switching windows.

- ⚡ **One hotkey.** <kbd>Ctrl</kbd>+<kbd>A</kbd>+<kbd>O</kbd> selects the text, fixes it and replaces it.
- 🌍 **Any language, including mixed ones.** Roman Urdu stays Roman Urdu, Hinglish stays Hinglish, English stays English.
- 🔌 **Bring your own model.** Google Gemini (has a free tier), OpenAI or any OpenAI-compatible API (Groq, OpenRouter, LM Studio…).
- 🔒 **Fully offline option.** Point it at a local [Ollama](https://ollama.com) model and nothing leaves your PC.
- ✍️ **Custom prompt.** Make it formal, casual, shorter, or translate instead of correcting.
- 🪶 **Lightweight.** Lives in the system tray, can start with Windows, and has a single `.exe`.

## Install

### Option 1: Download the .exe (easiest)

1. Download **`GrammarFixer.exe`** from the [latest release](https://github.com/YOUR_USERNAME/grammarfixer/releases/latest).
2. Run it. The settings window opens on first launch.
3. Pick a provider, paste your API key, click **Test**, then **Save**.

> Windows SmartScreen may warn about an unsigned app. Click *More info → Run anyway*,
> or build it yourself from source (below).

### Option 2: From source

```bash
git clone https://github.com/YOUR_USERNAME/grammarfixer.git
cd grammarfixer
pip install .
grammarfixer            # or: pythonw -m grammarfixer
```

## Getting an API key

| Provider | Key | Notes |
|---|---|---|
| **Google Gemini** (default) | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | Free tier, fast with `gemini-2.5-flash` |
| **OpenAI** | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | Any chat model |
| **OpenAI-compatible** | your provider | Choose *OpenAI* and change the **Base URL** (e.g. `https://api.groq.com/openai/v1`) |
| **Ollama** (local) | none | `ollama pull llama3.2`, then pick *Ollama* in Settings |

Instead of saving the key in Settings, you can also set the `GRAMMARFIXER_API_KEY`
environment variable, or `GEMINI_API_KEY` / `OPENAI_API_KEY`.

## Usage

1. Click into any text field and type (or paste) something.
2. Hold <kbd>Ctrl</kbd>, press <kbd>A</kbd>, then press <kbd>O</kbd> while still holding both.
3. The tray icon turns orange while it works, and you hear a beep when the text is replaced.

The tray menu lets you turn the hotkey on and off, open **Settings**, enable **Start with Windows**, and open the log.

**Tips**
- Change the letter in Settings (e.g. <kbd>Ctrl</kbd>+<kbd>A</kbd>+<kbd>G</kbd>).
- Replace the prompt with *"Rewrite this text to sound more professional."* and it becomes a rewriter.
- If you switch windows while it's working, the result is put on your clipboard instead of being pasted into the wrong app.

## How it works

```
Ctrl+A+O  ──►  Ctrl+A, Ctrl+C  ──►  LLM fixes the text  ──►  Ctrl+V  ──►  your clipboard is restored
```

A low-level keyboard hook detects the combo and swallows the letter key, so the app you're in
never receives e.g. <kbd>Ctrl</kbd>+<kbd>O</kbd> ("Open file").
Terminals are excluded by default because <kbd>Ctrl</kbd>+<kbd>C</kbd> means something else there.

## Configuration

Settings are stored in `%APPDATA%\GrammarFixer\config.json`. Advanced options not in the UI:

| Key | Default | Description |
|---|---|---|
| `temperature` | `0.2` | Lower values give more conservative edits |
| `timeout` | `30` | Request timeout in seconds |
| `max_chars` | `10000` | Refuse larger texts so you don't accidentally send a whole document |
| `excluded_apps` | terminals | Process names where the hotkey does nothing |

## Privacy

The selected text is sent to the provider you configure. Nothing else is sent anywhere, and
there is no telemetry. Your API key is stored in plain text in your user profile folder.
For complete privacy, use Ollama.

## Limitations

- Windows only (it uses Win32 keyboard hooks and the registry).
- It corrects **all** text in the focused field (that's what <kbd>Ctrl</kbd>+<kbd>A</kbd> selects).
- Only plain text is kept on the clipboard: images or files you had copied are not restored.
- Apps running as administrator can't receive simulated keys from a non-admin app.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
pyinstaller GrammarFixer.spec     # -> dist/GrammarFixer.exe
```

Releases are built automatically by GitHub Actions when you push a tag:
`git tag v1.0.0 && git push --tags`.

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
