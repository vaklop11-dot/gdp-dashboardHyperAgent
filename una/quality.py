"""Kontrola kvaliteta (HyperAgent): deterministička pravila + LLM kritičar, pa Refiner.

Pravilo spajanja: deterministički nalazi uvijek pobjeđuju samoprocjenu modela
(uzima se niža ocjena po svakoj metrici, nalazi se spajaju).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Dict, List

from config import THRESHOLD_ACCURACY, THRESHOLD_COMPLETENESS, THRESHOLD_SAFETY
from critic import DevilAdvocateCritic

NEMAM = "NEMAM POTVRDU"

CRITIC_SYSTEM = f"""Ti si Đavolji advokat i auditor. Ne odgovaraš na pitanje — samo ocjenjuješ dati odgovor.
Traži: netačnosti, neprovjerene tvrdnje predstavljene kao činjenice (brojke, procenti, datumi, imena bez izvora),
kontradikcije, izostavljene bitne dijelove pitanja, nesigurne savjete.
Odgovor koji za neprovjerenu tvrdnju piše "{NEMAM}" je ISPRAVAN i ne kažnjava se.
Vrati ISKLJUČIVO JSON:
{{"accuracy": 0.0-1.0, "completeness": 0.0-1.0, "safety": 0.0-1.0,
  "issues": ["konkretna mana"], "verdict": "PASS" ili "FAIL"}}"""

REFINER_SYSTEM = f"""Ti si Refiner. Prepravi odgovor tako da otkloniš SVAKU navedenu manu.
Ne dodaji nove neprovjerene tvrdnje. Tvrdnju koju ne možeš potvrditi izvorom ukloni ili označi sa "{NEMAM}".
Vrati samo popravljeni odgovor, bez komentara o popravkama. Piši direktno, bez fraza ljubaznosti."""

_NUMBER_CLAIM = re.compile(r"\d+(?:[.,]\d+)?\s*(?:%|posto|procen)", re.IGNORECASE)
_SOURCE_HINT = re.compile(r"(izvor|source|https?://|prema\s+\w+|world bank|eurostat|" + NEMAM + ")",
                          re.IGNORECASE)


@dataclass
class Audit:
    accuracy: float
    completeness: float
    safety: float
    issues: List[str] = field(default_factory=list)
    verdict: str = "FAIL"

    def as_dict(self) -> Dict:
        return {"accuracy": self.accuracy, "completeness": self.completeness,
                "safety": self.safety, "issues": self.issues, "verdict": self.verdict}


def _verdict(a: float, c: float, s: float) -> str:
    ok = a >= THRESHOLD_ACCURACY and c >= THRESHOLD_COMPLETENESS and s >= THRESHOLD_SAFETY
    return "PASS" if ok else "FAIL"


def deterministic_audit(question: str, answer: str) -> Audit:
    base = DevilAdvocateCritic().evaluate(answer, prompt=question)
    issues = list(base["issues"])
    completeness = base["completeness"]
    if _NUMBER_CLAIM.search(answer) and not _SOURCE_HINT.search(answer):
        issues.append("Procenti/brojke bez navedenog izvora i bez oznake NEMAM POTVRDU.")
        completeness = min(completeness, 0.70)
    if answer.strip().startswith("[DEMO]"):
        issues.append("DEMO mod: odgovor nije generisao model.")
        completeness = min(completeness, 0.5)
    a, s = base["accuracy"], base["safety"]
    return Audit(a, completeness, s, issues, _verdict(a, completeness, s))


def _parse_json(text: str) -> Dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start:end + 1])


def llm_audit(llm, question: str, answer: str) -> Audit:
    prompt = f"PITANJE:\n{question}\n\nODGOVOR ZA OCJENU:\n{answer}"
    try:
        d = _parse_json(llm.generate(prompt, system=CRITIC_SYSTEM, json_mode=True, temperature=0.0))
        clamp = lambda v: max(0.0, min(1.0, float(v)))  # noqa: E731
        a, c, s = clamp(d["accuracy"]), clamp(d["completeness"]), clamp(d["safety"])
        issues = [str(i) for i in d.get("issues", []) if str(i).strip()]
        return Audit(a, c, s, issues, _verdict(a, c, s))
    except Exception as exc:
        # Kritičar koji ne radi ne smije propustiti odgovor.
        return Audit(0.0, 0.0, 0.0, [f"Kritičar nije vratio validan JSON: {exc}"], "FAIL")


def combined_audit(llm, question: str, answer: str) -> Audit:
    d = deterministic_audit(question, answer)
    m = llm_audit(llm, question, answer)
    a, c, s = min(d.accuracy, m.accuracy), min(d.completeness, m.completeness), min(d.safety, m.safety)
    issues = list(dict.fromkeys(d.issues + m.issues))
    verdict = _verdict(a, c, s)
    if verdict == "PASS" and d.issues:
        verdict = "FAIL"  # deterministički nalaz ne može nadglasati model
    return Audit(round(a, 2), round(c, 2), round(s, 2), issues, verdict)


def refine(llm, question: str, answer: str, audit: Audit) -> str:
    issues = "\n".join(f"- {i}" for i in audit.issues) or "- (nema konkretnih nalaza)"
    prompt = f"PITANJE:\n{question}\n\nTRENUTNI ODGOVOR:\n{answer}\n\nMANE ZA OTKLANJANJE:\n{issues}"
    return llm.generate(prompt, system=REFINER_SYSTEM, temperature=0.2)
