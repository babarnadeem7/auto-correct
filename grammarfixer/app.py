"""System tray application entry point."""
import logging
import os
import threading
import webbrowser
from logging.handlers import RotatingFileHandler

import pystray
from PIL import Image, ImageDraw

from . import APP_NAME, __version__, winapi
from .config import CFG_DIR, LOG_FILE, load_config, needs_setup
from .fixer import Fixer
from .hotkey import HotkeyListener

REPO_URL = "https://github.com/YOUR_USERNAME/grammarfixer"

log = logging.getLogger(__name__)

COLORS = {
    "enabled": (26, 115, 232, 255),
    "disabled": (130, 130, 130, 255),
    "busy": (242, 153, 0, 255),
}


def make_icon(state: str) -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((4, 4, 60, 60), radius=14, fill=COLORS[state])
    d.line([(18, 34), (28, 44), (47, 22)], fill="white", width=7, joint="curve")
    return img


def setup_logging():
    os.makedirs(CFG_DIR, exist_ok=True)
    handler = RotatingFileHandler(LOG_FILE, maxBytes=256_000, backupCount=1, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler])


class App:
    def __init__(self):
        cfg = load_config()
        self.settings_open = False
        self.hotkey = HotkeyListener(cfg["letter"], self.on_hotkey)
        self.fixer = Fixer(self.hotkey.detector, self.notify, self.on_busy)
        self.tray = pystray.Icon(APP_NAME, make_icon("enabled"), "GrammarFixer", self.menu())

    # ---------- callbacks ----------
    def notify(self, msg: str):
        try:
            self.tray.notify(msg, "GrammarFixer")
        except Exception:
            log.debug("notify failed", exc_info=True)

    def refresh_icon(self):
        if self.fixer.busy:
            state = "busy"
        else:
            state = "enabled" if self.hotkey.enabled else "disabled"
        self.tray.icon = make_icon(state)

    def on_busy(self, _busy: bool):
        self.refresh_icon()

    def on_hotkey(self):
        if needs_setup(load_config()):
            self.notify("Set your API key in Settings first.")
            self.open_settings()
            return
        self.fixer.run()

    def on_saved(self, cfg: dict):
        self.hotkey.set_letter(cfg["letter"])
        self.tray.update_menu()

    # ---------- menu actions ----------
    def open_settings(self, *_):
        if self.settings_open:
            return
        self.settings_open = True

        def run():
            from .settings_ui import settings_window

            try:
                settings_window(self.on_saved)
            except Exception:
                log.exception("settings window failed")
            finally:
                self.settings_open = False

        threading.Thread(target=run, daemon=True).start()

    def toggle_enabled(self, *_):
        self.hotkey.enabled = not self.hotkey.enabled
        self.refresh_icon()

    def toggle_autostart(self, *_):
        try:
            winapi.set_autostart(not winapi.is_autostart())
        except OSError as e:
            log.exception("autostart failed")
            self.notify(f"Could not change autostart: {e}")

    def open_log(self, *_):
        if os.path.exists(LOG_FILE):
            os.startfile(LOG_FILE)

    def quit(self, *_):
        self.hotkey.stop()
        self.tray.stop()

    def menu(self) -> pystray.Menu:
        Item = pystray.MenuItem
        return pystray.Menu(
            Item(lambda _: f"Enabled  (Ctrl+A+{chr(self.hotkey.detector.vk)})",
                 self.toggle_enabled, checked=lambda _: self.hotkey.enabled),
            Item("Settings…", self.open_settings, default=True),
            Item("Start with Windows", self.toggle_autostart,
                 checked=lambda _: winapi.is_autostart()),
            pystray.Menu.SEPARATOR,
            Item("Open log", self.open_log),
            Item(f"About (v{__version__})", lambda *_: webbrowser.open(REPO_URL)),
            Item("Quit", self.quit),
        )

    def run(self):
        def setup(icon):
            icon.visible = True
            if needs_setup(load_config()):
                self.open_settings()

        self.hotkey.start()
        self.tray.run(setup=setup)


def main():
    if not winapi.single_instance():
        return
    winapi.enable_dpi_awareness()
    setup_logging()
    log.info("GrammarFixer %s starting", __version__)
    App().run()
