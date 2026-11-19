"""Kompresovana lokalna memorija (zlib) sa 30-dnevnom higijenom — iz UnaRevolucija v1.

Popravke u odnosu na v1:
- higijena ne puca kad timestamp nema mikrosekunde (str(datetime) ih tada izostavi);
- zapis ide preko privremenog fajla, pa prekid ne ošteti memoriju;
- historija se zaista koristi kao kontekst (v1 ju je samo čuvao).
"""
from __future__ import annotations

import json
import os
import zlib
from datetime import datetime, timedelta
from typing import Dict, List

RETENTION_DAYS = 30


def _parse_ts(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


class Memory:
    def __init__(self, path: str = "trenutno_stanje.una"):
        self.path = path
        self.data: Dict = {"id": "PROJ_UNA_REVOLUCIJA", "history": [], "last_updated": None}
        self.load_error: str | None = None
        self.load()

    @property
    def history(self) -> List[Dict]:
        return self.data.setdefault("history", [])

    def load(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "rb") as fh:
                self.data = json.loads(zlib.decompress(fh.read()).decode("utf-8"))
        except Exception as exc:
            self.load_error = f"Memorija oštećena, počinjem novu: {exc}"

    def save(self) -> None:
        self.data["last_updated"] = datetime.now().isoformat()
        raw = json.dumps(self.data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        tmp = self.path + ".tmp"
        with open(tmp, "wb") as fh:
            fh.write(zlib.compress(raw, level=9))
        os.replace(tmp, self.path)

    def hygiene(self, now: datetime | None = None) -> int:
        now = now or datetime.now()
        limit = now - timedelta(days=RETENTION_DAYS)
        before = len(self.history)
        self.data["history"] = [
            r for r in self.history
            if (_parse_ts(r.get("timestamp", "")) or now) >= limit
        ]
        return before - len(self.history)

    def add(self, question: str, answer: str, verdict: str) -> None:
        self.history.append({
            "question": question,
            "answer": answer,
            "verdict": verdict,
            "timestamp": datetime.now().isoformat(),
        })

    def context(self, last_n: int = 3, max_chars: int = 600) -> str:
        if not self.history:
            return ""
        parts = []
        for h in self.history[-last_n:]:
            parts.append(f"P: {h['question'][:max_chars]}\nO: {h['answer'][:max_chars]}")
        return "\n\n".join(parts)
