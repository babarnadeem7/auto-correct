import pytest
import requests

from grammarfixer import providers
from grammarfixer.config import DEFAULT_CFG, PRESETS


class FakeResponse:
    def __init__(self, status=200, data=None, text=""):
        self.status_code = status
        self._data = data
        self.text = text
        self.reason = "reason"

    def json(self):
        if self._data is None:
            raise ValueError
        return self._data


class FakeSession:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def cfg(provider="gemini", **kw):
    preset = PRESETS[provider]
    return {**DEFAULT_CFG, "provider": provider, "api_key": "k",
            "base_url": preset["base_url"], "model": preset["model"], **kw}


def gemini_ok(text):
    return FakeResponse(data={"candidates": [{"content": {"parts": [{"text": text}]}}]})


def openai_ok(text):
    return FakeResponse(data={"choices": [{"message": {"content": text}}]})


# ---------- clean_output ----------
@pytest.mark.parametrize("original, model_out, expected", [
    ("i has a apple", "I have an apple.", "I have an apple."),
    ("i has a apple\n", "I have an apple.", "I have an apple.\n"),
    ("  hi there", "Hi there.", "  Hi there."),
    ("i has a apple", "```\nI have an apple.\n```", "I have an apple."),
    ("i has a apple", '"I have an apple."', "I have an apple."),
    ('"hi" he say', '"Hi," he said.', '"Hi," he said.'),
])
def test_clean_output(original, model_out, expected):
    assert providers.clean_output(original, model_out) == expected


# ---------- gemini ----------
def test_gemini_request_shape():
    s = FakeSession(gemini_ok("Fixed."))
    assert providers.correct("fixd", cfg(), session=s) == "Fixed."
    url, kw = s.calls[0]
    assert url.endswith("/models/gemini-2.5-flash:generateContent")
    assert kw["headers"] == {"x-goog-api-key": "k"}
    assert kw["json"]["contents"][0]["parts"][0]["text"] == "fixd"
    assert kw["json"]["systemInstruction"]["parts"][0]["text"] == DEFAULT_CFG["prompt"]
    assert kw["json"]["generationConfig"]["thinkingConfig"] == {"thinkingBudget": 0}


def test_gemini_retries_without_thinking_config_on_400():
    s = FakeSession(FakeResponse(400, {"error": {"message": "bad thinking"}}), gemini_ok("Ok."))
    assert providers.correct("ok", cfg(), session=s) == "Ok."
    assert "thinkingConfig" not in s.calls[1][1]["json"]["generationConfig"]


def test_gemini_skips_thought_parts():
    data = {"candidates": [{"content": {"parts": [
        {"text": "thinking...", "thought": True}, {"text": "Answer."}]}}]}
    assert providers.correct("x", cfg(), session=FakeSession(FakeResponse(data=data))) == "Answer."


def test_gemini_blocked_prompt():
    s = FakeSession(FakeResponse(data={"promptFeedback": {"blockReason": "SAFETY"}}))
    with pytest.raises(providers.ProviderError, match="SAFETY"):
        providers.correct("x", cfg(), session=s)


def test_http_error_message_is_surfaced():
    s = FakeSession(FakeResponse(403, {"error": {"message": "API key not valid"}}))
    with pytest.raises(providers.ProviderError, match=r"403.*API key not valid"):
        providers.correct("x", cfg(model="gemini-2.5-pro"), session=s)


def test_timeout():
    s = FakeSession(requests.Timeout())
    with pytest.raises(providers.ProviderError, match="timed out"):
        providers.correct("x", cfg(), session=s)


def test_missing_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GRAMMARFIXER_API_KEY", raising=False)
    with pytest.raises(providers.ProviderError, match="API key"):
        providers.correct("x", cfg(api_key=""), session=FakeSession())


# ---------- openai-compatible ----------
def test_openai_request_shape():
    s = FakeSession(openai_ok("Fixed."))
    assert providers.correct("fixd", cfg("openai"), session=s) == "Fixed."
    url, kw = s.calls[0]
    assert url == "https://api.openai.com/v1/chat/completions"
    assert kw["headers"] == {"Authorization": "Bearer k"}
    assert [m["role"] for m in kw["json"]["messages"]] == ["system", "user"]


def test_ollama_needs_no_key():
    s = FakeSession(openai_ok("Fixed."))
    assert providers.correct("fixd", cfg("ollama", api_key=""), session=s) == "Fixed."
    assert s.calls[0][1]["headers"] == {}


def test_openai_bad_response():
    s = FakeSession(FakeResponse(data={"weird": True}))
    with pytest.raises(providers.ProviderError, match="Unexpected"):
        providers.correct("x", cfg("openai"), session=s)
