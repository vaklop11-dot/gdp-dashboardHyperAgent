"""LLM sloj: Gemini preko zvaničnog `google-genai` SDK-a, uz DEMO zamjenu bez ključa.

`google-generativeai` (stari SDK iz UnaRevolucija v1) je zastario; Google preporučuje
`google-genai` (https://ai.google.dev/gemini-api/docs/libraries).
"""
from __future__ import annotations

import os
import time
from typing import Optional

DEFAULT_MODEL = os.environ.get("UNA_MODEL", "gemini-2.5-flash")


class LLMError(RuntimeError):
    """Poziv modela nije uspio."""


class DemoLLM:
    """Radi bez ključa i bez mreže. Odgovori su jasno označeni kao DEMO."""

    available = False
    model = "demo"

    def generate(self, prompt: str, system: Optional[str] = None,
                 json_mode: bool = False, temperature: float = 0.2) -> str:
        if json_mode:
            # Kritičar u DEMO modu ne smije dati PASS — ništa nije provjereno.
            return ('{"accuracy": 0.5, "completeness": 0.5, "safety": 0.95, '
                    '"issues": ["DEMO mod: model nije povezan, ništa nije provjereno."], '
                    '"verdict": "FAIL"}')
        return "[DEMO] Model nije povezan (nema GEMINI_API_KEY). NEMAM POTVRDU."


class GeminiLLM:
    available = True

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, retries: int = 2):
        from google import genai  # uvoz ovdje da DEMO radi i bez paketa
        from google.genai import types

        self._types = types
        self._client = genai.Client(api_key=api_key)
        self.model = model
        self.retries = retries

    def generate(self, prompt: str, system: Optional[str] = None,
                 json_mode: bool = False, temperature: float = 0.2) -> str:
        cfg = self._types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            response_mime_type="application/json" if json_mode else None,
        )
        last_exc: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                resp = self._client.models.generate_content(
                    model=self.model, contents=prompt, config=cfg)
                text = resp.text or ""
                if not text.strip():
                    raise LLMError("Model je vratio prazan odgovor.")
                return text
            except Exception as exc:  # mreža, 429 rate limit, blokiran sadržaj...
                last_exc = exc
                if attempt < self.retries:
                    time.sleep(2 * (attempt + 1))
        raise LLMError(f"Gemini poziv nije uspio: {last_exc}")


def find_api_key(explicit: Optional[str] = None) -> str:
    return (explicit or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY") or "").strip()


def make_llm(api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
    key = find_api_key(api_key)
    if not key:
        return DemoLLM()
    try:
        return GeminiLLM(key, model=model)
    except ImportError:
        return DemoLLM()
