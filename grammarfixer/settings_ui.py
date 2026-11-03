"""Tkinter settings window."""
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from . import __version__, providers
from .config import DEFAULT_CFG, DEFAULT_PROMPT, PRESETS, load_config, save_config

SAMPLE = "i has went to the store yesterday and buyed three apple"


def settings_window(on_saved=lambda cfg: None):
    cfg = load_config()
    win = tk.Tk()
    win.title(f"GrammarFixer {__version__} - Settings")
    win.attributes("-topmost", True)
    win.resizable(False, False)
    frm = ttk.Frame(win, padding=12)
    frm.grid(sticky="nsew")
    pad = {"padx": 6, "pady": 4}

    labels = {k: v["label"] for k, v in PRESETS.items()}
    provider = tk.StringVar(value=labels[cfg["provider"]])
    api_key = tk.StringVar(value=cfg["api_key"])
    base_url = tk.StringVar(value=cfg["base_url"])
    model = tk.StringVar(value=cfg["model"])
    letter = tk.StringVar(value=cfg["letter"])
    status = tk.StringVar()

    def provider_id() -> str:
        return next(k for k, v in labels.items() if v == provider.get())

    def on_provider(_event=None):
        p = PRESETS[provider_id()]
        base_url.set(p["base_url"])
        model.set(p["model"])
        key_entry.configure(state="normal" if p["needs_key"] else "disabled")

    row = 0
    ttk.Label(frm, text="Provider").grid(row=row, column=0, sticky="w", **pad)
    combo = ttk.Combobox(frm, textvariable=provider, values=list(labels.values()),
                         state="readonly", width=30)
    combo.grid(row=row, column=1, sticky="w", **pad)
    combo.bind("<<ComboboxSelected>>", on_provider)

    row += 1
    ttk.Label(frm, text="API key").grid(row=row, column=0, sticky="w", **pad)
    key_entry = ttk.Entry(frm, textvariable=api_key, width=56, show="•")
    key_entry.grid(row=row, column=1, columnspan=2, sticky="we", **pad)
    if not PRESETS[cfg["provider"]]["needs_key"]:
        key_entry.configure(state="disabled")

    row += 1
    ttk.Label(frm, text="Base URL").grid(row=row, column=0, sticky="w", **pad)
    ttk.Entry(frm, textvariable=base_url, width=56).grid(row=row, column=1, columnspan=2,
                                                         sticky="we", **pad)
    row += 1
    ttk.Label(frm, text="Model").grid(row=row, column=0, sticky="w", **pad)
    ttk.Entry(frm, textvariable=model, width=30).grid(row=row, column=1, sticky="w", **pad)

    row += 1
    ttk.Label(frm, text="Hotkey").grid(row=row, column=0, sticky="w", **pad)
    hk = ttk.Frame(frm)
    hk.grid(row=row, column=1, sticky="w", **pad)
    ttk.Label(hk, text="Ctrl + A + ").pack(side="left")
    ttk.Entry(hk, textvariable=letter, width=3).pack(side="left")

    row += 1
    ttk.Label(frm, text="Prompt").grid(row=row, column=0, sticky="nw", **pad)
    prompt_t = tk.Text(frm, width=56, height=8, wrap="word", font=("Segoe UI", 9))
    prompt_t.insert("1.0", cfg["prompt"])
    prompt_t.grid(row=row, column=1, columnspan=2, sticky="we", **pad)

    row += 1
    ttk.Label(frm, textvariable=status, foreground="#555", wraplength=420).grid(
        row=row, column=0, columnspan=3, sticky="w", **pad)

    def collect() -> dict | None:
        ltr = letter.get().strip().upper()
        if len(ltr) != 1 or not ltr.isalpha() or ltr == "A":
            messagebox.showerror("Hotkey", "Enter a single letter other than A.", parent=win)
            return None
        pid = provider_id()
        return {
            **cfg,
            "provider": pid,
            "api_key": api_key.get().strip(),
            "base_url": base_url.get().strip() or PRESETS[pid]["base_url"],
            "model": model.get().strip() or PRESETS[pid]["model"],
            "letter": ltr,
            "prompt": prompt_t.get("1.0", "end").strip() or DEFAULT_PROMPT,
        }

    def test():
        new = collect()
        if new is None:
            return
        status.set("Testing…")
        result = {}

        def work():
            try:
                result["ok"] = providers.correct(SAMPLE, new)
            except providers.ProviderError as e:
                result["err"] = str(e)

        def poll():
            if t.is_alive():
                win.after(100, poll)
            elif "ok" in result:
                status.set(f"✔ {result['ok']}")
            else:
                status.set(f"✖ {result['err']}")

        t = threading.Thread(target=work, daemon=True)
        t.start()
        poll()

    def save():
        new = collect()
        if new is None:
            return
        save_config(new)
        on_saved(new)
        win.destroy()

    def reset_prompt():
        prompt_t.delete("1.0", "end")
        prompt_t.insert("1.0", DEFAULT_CFG["prompt"])

    row += 1
    btns = ttk.Frame(frm)
    btns.grid(row=row, column=0, columnspan=3, sticky="e", **pad)
    ttk.Button(btns, text="Default prompt", command=reset_prompt).pack(side="left", padx=4)
    ttk.Button(btns, text="Test", command=test).pack(side="left", padx=4)
    ttk.Button(btns, text="Save", command=save).pack(side="left", padx=4)
    ttk.Button(btns, text="Cancel", command=win.destroy).pack(side="left", padx=4)

    win.bind("<Escape>", lambda _e: win.destroy())
    win.mainloop()
