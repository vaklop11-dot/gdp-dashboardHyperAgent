import json
import re
from typing import Dict, List

from config import THRESHOLD_ACCURACY, THRESHOLD_COMPLETENESS, THRESHOLD_SAFETY


class DevilAdvocateCritic:
    """Đavolji advokat: striktna automatska evaluacija industrijskog koda."""

    def evaluate(self, code: str, persona: str = "", prompt: str = "") -> Dict:
        issues: List[str] = []
        c = code.lower() if code else ""
        p = prompt.lower() if prompt else ""

        # Industrijska pravila važe samo kad je ZADATAK industrijski/embedded
        # (ranije je npr. "Gemini Flash" u odgovoru okidao flash-memory pravila).
        # Samo kad se traži rješenje/kod, ne za objašnjenje pojma (npr. "šta je PLC").
        industrial = self._is_industrial(p if p else c) and (
            not p or bool(self.IMPLEMENT_ASK.search(p)) or bool(self.CODE_IN_ANSWER.search(code or "")))
        if industrial:
            self._evaluate_embedded(code=c, issues=issues)
        self._evaluate_una_edge(prompt=p, code=c, issues=issues)

        accuracy = max(0.5, 1.0 - len(issues) * 0.15)
        completeness = 0.90 if not issues else 0.70
        # Ranije: 0.60 za SVAKI zadatak bez E-Stop -> svako obično pitanje je bilo FAIL.
        if industrial:
            safety = 0.95 if self._has_safety_feature(c) else 0.60
        else:
            safety = 0.95
        verdict = self._compute_verdict(accuracy, completeness, safety)

        return {
            "accuracy": round(accuracy, 2),
            "completeness": round(completeness, 2),
            "safety": round(safety, 2),
            "issues": issues,
            "verdict": verdict,
        }

    def evaluate_json(self, code: str, persona: str = "", prompt: str = "") -> str:
        result = self.evaluate(code, persona, prompt)
        return json.dumps(result, ensure_ascii=False)

    INDUSTRIAL_KEYWORDS = ("gpio", "cnc", "embedded", "spi", "freertos", "firmware",
                           "esp32", "rp2040", "plc", "mikrokontroler", "microcontroller")

    IMPLEMENT_ASK = re.compile(r"(napi[sš]i|dizajniraj|projektuj|implementiraj|isprogramiraj|\bkod\b|\bcode\b|"
                               r"\bwrite\b|\bdesign\b|\bimplement|\bbuild\b|napravi)", re.IGNORECASE)
    CODE_IN_ANSWER = re.compile(r"```|#include|\bvoid\s+\w+\s*\(|\bdef\s+\w+\(|digitalRead|gpio_|while\s*\(",
                                re.IGNORECASE)

    @classmethod
    def _is_industrial(cls, text: str) -> bool:
        return any(re.search(rf"\b{k}\b", text) for k in cls.INDUSTRIAL_KEYWORDS)

    @staticmethod
    def _has_safety_feature(code: str) -> bool:
        return any(token in code for token in ["e-stop", "fail-safe", "fail safe", "emergency stop"])

    @staticmethod
    def _evaluate_embedded(code: str, issues: List[str]) -> None:
        if any(keyword in code for keyword in ["gpio", "cnc", "embedded", "spi", "flash", "freertos"]):
            if "debouncing" not in code:
                issues.append(
                    "Kritična mana: Tasteri nemaju hardverski ili softverski debouncing. Šum na liniji će okinuti lažni prekid!"
                )
            if "flash" in code and "ring_buffer" not in code and "ring-buffer" not in code:
                issues.append(
                    "Rizik habanja memorije: Direktno pisanje u flash memoriju bez ring-buffera će uništiti sektore!"
                )

    @staticmethod
    def _evaluate_una_edge(prompt: str, code: str, issues: List[str]) -> None:
        if "una#" in prompt or "edge" in prompt or "energy" in prompt or "potrošnja" in prompt:
            # "NEMAM POTVRDU" je ispravno ponašanje po pravilniku i više se ne kažnjava.
            if "nemam potvrdu" not in code and any(
                    token in code for token in ["%", "x manja", "procen", "percent", "times smaller"]):
                issues.append(
                    "Neprovjerena tvrdnja o procentima/efikasnosti bez referentnog benchmarka ili mjerenja."
                )

    @staticmethod
    def _compute_verdict(accuracy: float, completeness: float, safety: float) -> str:
        if (
            accuracy < THRESHOLD_ACCURACY
            or completeness < THRESHOLD_COMPLETENESS
            or safety < THRESHOLD_SAFETY
        ):
            return "FAIL"
        return "PASS"
