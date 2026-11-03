"""LLM backends. Each one takes text and returns the corrected text."""
import re

import requests

from .config import PRESETS, api_key


class ProviderError(Exception):
    """A user-presentable error from the LLM backend."""


_FENCE = re.compile(r"^```[\w-]*\n(.*?)\n?```$", re.DOTALL)


def clean_output(original: str, fixed: str) -> str:
    """Strip artifacts models like to add and keep the original's outer whitespace."""
    fixed = fixed.strip()
    m = _FENCE.match(fixed)
    if m:
        fixed = m.group(1).strip()
    for q in ('"', "'", "“”"):
        open_q, close_q = q[0], q[-1]
        if (len(fixed) >= 2 and fixed[0] == open_q and fixed[-1] == close_q
                and original.strip()[:1] != open_q):
            fixed = fixed[1:-1].strip()
    lead = original[: len(original) - len(original.lstrip())]
    trail = original[len(original.rstrip()):]
    return lead + fixed + trail


def _post(session, url, timeout, **kwargs) -> dict:
    try:
        r = session.post(url, timeout=timeout, **kwargs)
    except requests.Timeout:
        raise ProviderError("The request timed out.") from None
    except requests.RequestException as e:
        host = url.split("/")[2]
        raise ProviderError(f"Could not reach {host}: {e.__class__.__name__}") from None
    if r.status_code >= 400:
        try:
            detail = r.json().get("error", {})
            detail = detail.get("message", "") if isinstance(detail, dict) else str(detail)
        except ValueError:
            detail = r.text[:200]
        raise ProviderError(f"HTTP {r.status_code}: {detail or r.reason}")
    try:
        return r.json()
    except ValueError:
        raise ProviderError("The server returned invalid JSON.") from None


def _gemini(text: str, cfg: dict, session) -> str:
    url = f"{cfg['base_url'].rstrip('/')}/models/{cfg['model']}:generateContent"
    body = {
        "systemInstruction": {"parts": [{"text": cfg["prompt"]}]},
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        "generationConfig": {"temperature": cfg["temperature"]},
    }
    if "flash" in cfg["model"]:
        # Thinking only adds latency for a task like this.
        body["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 0}
    headers = {"x-goog-api-key": api_key(cfg)}
    try:
        data = _post(session, url, cfg["timeout"], headers=headers, json=body)
    except ProviderError as e:
        if "thinkingConfig" not in body["generationConfig"] or not str(e).startswith("HTTP 400"):
            raise
        del body["generationConfig"]["thinkingConfig"]
        data = _post(session, url, cfg["timeout"], headers=headers, json=body)

    candidates = data.get("candidates") or []
    if not candidates:
        reason = (data.get("promptFeedback") or {}).get("blockReason", "no candidates")
        raise ProviderError(f"Gemini returned no result ({reason}).")
    parts = (candidates[0].get("content") or {}).get("parts") or []
    out = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    if not out.strip():
        reason = candidates[0].get("finishReason")
        raise ProviderError(f"Gemini returned an empty result ({reason}).")
    return out


def _openai(text: str, cfg: dict, session) -> str:
    url = f"{cfg['base_url'].rstrip('/')}/chat/completions"
    headers = {}
    key = api_key(cfg)
    if key:
        headers["Authorization"] = f"Bearer {key}"
    body = {
        "model": cfg["model"],
        "temperature": cfg["temperature"],
        "messages": [
            {"role": "system", "content": cfg["prompt"]},
            {"role": "user", "content": text},
        ],
    }
    data = _post(session, url, cfg["timeout"], headers=headers, json=body)
    try:
        out = data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        raise ProviderError("Unexpected response from the server.") from None
    if not out.strip():
        raise ProviderError("The model returned an empty result.")
    return out


def correct(text: str, cfg: dict, session=requests) -> str:
    if PRESETS[cfg["provider"]]["needs_key"] and not api_key(cfg):
        raise ProviderError("No API key set. Open Settings from the tray icon.")
    backend = _gemini if cfg["provider"] == "gemini" else _openai
    return clean_output(text, backend(text, cfg, session))
