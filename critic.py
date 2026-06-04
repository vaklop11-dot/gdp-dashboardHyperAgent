import json
from typing import Dict, List

from config import THRESHOLD_ACCURACY, THRESHOLD_COMPLETENESS, THRESHOLD_SAFETY


class DevilAdvocateCritic:
    """Đavolji advokat: striktna automatska evaluacija industrijskog koda."""

    def evaluate(self, code: str, persona: str = "", prompt: str = "") -> Dict:
        issues: List[str] = []
        c = code.lower() if code else ""
        p = prompt.lower() if prompt else ""

        self._evaluate_embedded(code=c, issues=issues)
        self._evaluate_una_edge(prompt=p, code=c, issues=issues)

        accuracy = max(0.5, 1.0 - len(issues) * 0.15)
        completeness = 0.90 if not issues else 0.70
        safety = 0.95 if self._has_safety_feature(c) else 0.60
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
            if "nemam potvrdu" in code:
                issues.append(
                    "Nedostatak izvora: Tvrdnja o potrošnji ili performansama bez jasnog benchmarka ili egzaktnog izvora."
                )
            if any(token in code for token in ["%", "x manja", "procen", "percent", "times smaller"]):
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
