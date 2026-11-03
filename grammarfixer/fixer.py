"""The grab -> correct -> replace workflow."""
import logging
import time
import winsound

import pyperclip
from pynput import keyboard

from . import providers, winapi
from .config import load_config

log = logging.getLogger(__name__)
_kb = keyboard.Controller()


def _press_ctrl(key: str):
    with _kb.pressed(keyboard.Key.ctrl):
        _kb.press(key)
        _kb.release(key)


def _paste() -> str:
    try:
        return pyperclip.paste()
    except pyperclip.PyperclipException:
        return ""


def _wait_clipboard_change(sentinel: str, timeout: float = 1.0) -> str:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        text = _paste()
        if text != sentinel:
            return text
        time.sleep(0.03)
    return ""


class Fixer:
    def __init__(self, detector, notify, on_busy=lambda busy: None):
        self.detector = detector
        self.notify = notify
        self.on_busy = on_busy
        self.busy = False

    def run(self):
        if self.busy:
            return
        self.busy = True
        self.on_busy(True)
        try:
            self._run(load_config())
        except providers.ProviderError as e:
            log.warning("provider error: %s", e)
            winsound.MessageBeep(winsound.MB_ICONHAND)
            self.notify(str(e))
        except Exception as e:
            log.exception("unexpected error")
            winsound.MessageBeep(winsound.MB_ICONHAND)
            self.notify(f"Error: {e}")
        finally:
            self.busy = False
            self.on_busy(False)

    def _run(self, cfg: dict):
        # Our simulated Ctrl+A / Ctrl+C would mix with the keys the user still holds.
        self.detector.wait_idle()
        hwnd = winapi.foreground_window()
        if winapi.process_name(hwnd) in {a.lower() for a in cfg["excluded_apps"]}:
            return

        old = _paste()
        sentinel = f"__grammarfixer_{time.time_ns()}__"
        restore = True
        try:
            pyperclip.copy(sentinel)
            _press_ctrl("a")
            time.sleep(0.05)
            _press_ctrl("c")
            text = _wait_clipboard_change(sentinel)
            if not text.strip():
                winsound.MessageBeep(winsound.MB_ICONHAND)
                return
            if len(text) > cfg["max_chars"]:
                self.notify(f"Text too long ({len(text)} chars, limit {cfg['max_chars']}).")
                return

            started = time.monotonic()
            fixed = providers.correct(text, cfg)
            log.info("corrected %d chars in %.2fs", len(text), time.monotonic() - started)
            if fixed == text:
                winsound.MessageBeep(winsound.MB_OK)
                return

            if winapi.foreground_window() != hwnd:
                # The user switched windows while we waited; don't paste into the wrong place.
                pyperclip.copy(fixed)
                restore = False
                self.notify("Window changed - the corrected text is on your clipboard.")
                return

            pyperclip.copy(fixed)
            time.sleep(0.05)
            _press_ctrl("v")  # the selection is still active, so this replaces it
            time.sleep(0.4)  # give slow apps time to read the clipboard
            winsound.MessageBeep(winsound.MB_OK)
        finally:
            if restore:
                pyperclip.copy(old)
