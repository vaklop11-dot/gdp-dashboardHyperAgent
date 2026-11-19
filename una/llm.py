"""LLM sloj: Cloudflare Workers AI preko REST API-ja (bez Geminija), uz DEMO zamjenu bez pristupnih podataka.

Glavna verzija asistenta je Cloudflare Worker u folderu `cloudflare/` (tamo nema ključa — koristi env.AI).
Ovaj Python sloj služi za lokalni terminal/Streamlit i traži:
  CLOUDFLARE_ACCOUNT_ID  i  CLOUDFLARE_API_TOKEN (Workers AI token iz Cloudflare dashboarda).
Endpoint: POST https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}
"""
from __future__ import annotations

import os
import time
from typing import Optional

import requests

MODEL_MAIN = os.environ.get("UNA_MODEL_MAIN", "@cf/meta/llama-3.3-70b-instruct-fp8-fast")
MODEL_CRITIC = os.environ.get("UNA_MODEL_CRITIC", "@cf/meta/llama-3.1-8b-instruct-fast")
API = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{model}"


class LLMError(RuntimeError):
    """Poziv modela nije uspio."""


class DemoLLM:
    """Radi bez pristupnih podataka i bez mreže. Odgovori su jasno označeni kao DEMO."""

    available = False
    model = "demo"

    def generate(self, prompt: str, system: Optional[str] = None,
                 json_mode: bool = False, temperature: float = 0.2, critic: bool = False) -> str:
        if json_mode:
            return ('{"accuracy": 0.5, "completeness": 0.5, "safety": 0.95, '
                    '"issues": ["DEMO mod: model nije povezan, ništa nije provjereno."], '
                    '"verdict": "FAIL"}')
        return "[DEMO] Model nije povezan (nema Cloudflare pristupa). NEMAM POTVRDU."


def _extract(result) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        if isinstance(result.get("response"), str):
            return result["response"]
        choices = result.get("choices") or []
        if choices and isinstance(choices[0].get("message", {}).get("content"), str):
            return choices[0]["message"]["content"]
    raise LLMError("Nepoznat format odgovora modela.")


class CloudflareLLM:
    available = True

    def __init__(self, account_id: str, api_token: str, model: str = MODEL_MAIN,
                 critic_model: str = MODEL_CRITIC, retries: int = 2, timeout: int = 90):
        self.account_id = account_id
        self.api_token = api_token
        self.model = model
        self.critic_model = critic_model
        self.retries = retries
        self.timeout = timeout

    def generate(self, prompt: str, system: Optional[str] = None,
                 json_mode: bool = False, temperature: float = 0.2, critic: bool = False) -> str:
        # Kritičar ide na DRUGI model, da greške ne budu korelirane.
        model = self.critic_model if (critic or json_mode) else self.model
        messages = ([{"role": "system", "content": system}] if system else []) + \
            [{"role": "user", "content": prompt}]
        url = API.format(account=self.account_id, model=model)
        last: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                r = requests.post(url, timeout=self.timeout,
                                  headers={"Authorization": f"Bearer {self.api_token}"},
                                  json={"messages": messages, "max_tokens": 1024, "temperature": temperature})
                data = r.json()
                if r.status_code != 200 or not data.get("success", False):
                    raise LLMError(f"HTTP {r.status_code}: {data.get('errors')}")
                text = _extract(data.get("result"))
                if not text.strip():
                    raise LLMError("Model je vratio prazan odgovor.")
                return text
            except Exception as exc:
                last = exc
                if attempt < self.retries:
                    time.sleep(2 * (attempt + 1))
        raise LLMError(f"Cloudflare Workers AI poziv nije uspio: {last}")


def find_credentials(account_id: Optional[str] = None, api_token: Optional[str] = None) -> tuple[str, str]:
    return ((account_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID") or "").strip(),
            (api_token or os.environ.get("CLOUDFLARE_API_TOKEN") or "").strip())


def make_llm(account_id: Optional[str] = None, api_token: Optional[str] = None):
    acc, tok = find_credentials(account_id, api_token)
    if not (acc and tok):
        return DemoLLM()
    return CloudflareLLM(acc, tok)
