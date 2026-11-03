"""Global Ctrl + A + <letter> hotkey.

The letter key press is swallowed so the focused app never sees e.g. Ctrl+O
(which would otherwise pop up an "Open file" dialog).
"""
import threading
import time

VK_A = 0x41
VK_CTRL = {0x11, 0xA2, 0xA3}
WM_KEYDOWN, WM_KEYUP, WM_SYSKEYDOWN, WM_SYSKEYUP = 0x100, 0x101, 0x104, 0x105
LLKHF_INJECTED = 0x10 | 0x02


class ComboDetector:
    """Pure state machine: feed key events, get back what to do with them."""

    PASS, SUPPRESS, TRIGGER = "pass", "suppress", "trigger"

    def __init__(self, letter: str = "O"):
        self.vk = ord(letter.upper())
        self.enabled = True
        self.held = set()
        self._swallowed = set()

    @property
    def idle(self) -> bool:
        return not self.held

    def feed(self, vk: int, down: bool) -> str:
        if down:
            if vk in self._swallowed:  # auto-repeat of a swallowed key
                return self.SUPPRESS
            combo = (self.enabled and vk == self.vk
                     and VK_A in self.held and self.held & VK_CTRL)
            self.held.add(vk)
            if combo:
                self._swallowed.add(vk)
                return self.TRIGGER
            return self.PASS
        self.held.discard(vk)
        if vk in self._swallowed:
            self._swallowed.discard(vk)
            return self.SUPPRESS
        return self.PASS

    def wait_idle(self, timeout: float = 2.0):
        end = time.monotonic() + timeout
        while time.monotonic() < end and not self.idle:
            time.sleep(0.02)
        self.held.clear()  # recover from key-ups we never saw (e.g. after Win+L)


class HotkeyListener:
    def __init__(self, letter: str, on_trigger):
        self.detector = ComboDetector(letter)
        self.on_trigger = on_trigger
        self._listener = None

    @property
    def enabled(self) -> bool:
        return self.detector.enabled

    @enabled.setter
    def enabled(self, value: bool):
        self.detector.enabled = value

    def set_letter(self, letter: str):
        self.detector.vk = ord(letter.upper())

    def _filter(self, msg, data):
        if data.flags & LLKHF_INJECTED:  # our own simulated keystrokes
            return False
        down = msg in (WM_KEYDOWN, WM_SYSKEYDOWN)
        if not down and msg not in (WM_KEYUP, WM_SYSKEYUP):
            return False
        action = self.detector.feed(data.vkCode, down)
        if action == ComboDetector.TRIGGER:
            threading.Thread(target=self.on_trigger, daemon=True).start()
        if action != ComboDetector.PASS:
            self._listener.suppress_event()  # raises; stops the event system-wide
        return False  # we don't use pynput's own callbacks

    def start(self):
        from pynput import keyboard

        self._listener = keyboard.Listener(win32_event_filter=self._filter)
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()
