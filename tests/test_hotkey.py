from grammarfixer.hotkey import VK_A, ComboDetector

CTRL, VK_O, X = 0xA2, ord("O"), ord("X")
P, S, T = ComboDetector.PASS, ComboDetector.SUPPRESS, ComboDetector.TRIGGER


def feed(d, events):
    return [d.feed(vk, down) for vk, down in events]


def test_ctrl_a_letter_triggers_and_swallows_letter():
    d = ComboDetector("O")
    out = feed(d, [(CTRL, True), (VK_A, True), (VK_O, True), (VK_O, True),  # auto-repeat
                   (VK_O, False), (VK_A, False), (CTRL, False)])
    assert out == [P, P, T, S, S, P, P]
    assert d.idle


def test_needs_ctrl():
    assert feed(ComboDetector("O"), [(VK_A, True), (VK_O, True)]) == [P, P]


def test_needs_a():
    assert feed(ComboDetector("O"), [(CTRL, True), (VK_O, True)]) == [P, P]


def test_other_letters_pass():
    assert feed(ComboDetector("O"), [(CTRL, True), (VK_A, True), (X, True)]) == [P, P, P]


def test_disabled_passes_everything():
    d = ComboDetector("O")
    d.enabled = False
    assert feed(d, [(CTRL, True), (VK_A, True), (VK_O, True), (VK_O, False)]) == [P, P, P, P]


def test_letter_change():
    d = ComboDetector("O")
    d.vk = ord("G")
    assert feed(d, [(CTRL, True), (VK_A, True), (ord("G"), True)])[-1] == T


def test_wait_idle_clears_stuck_keys():
    d = ComboDetector("O")
    d.feed(VK_A, True)
    d.wait_idle(timeout=0.05)
    assert d.idle
