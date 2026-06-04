import json
import time
from dataclasses import dataclass

from backend import AuditPipeline
from config import MAX_ITERATIONS
from models import LocalLM


@dataclass
class HyperAgentResult:
    iterations: int
    duration_sec: float
    final_output: str
    verdict: str
    audit: dict


class HyperAgent:
    def __init__(self):
        self.audit_pipeline = AuditPipeline()
        # initialize a local open-source model wrapper (falls back to stub if unavailable)
        self.model = LocalLM()

    def solve(self, task: str) -> HyperAgentResult:
        start_time = time.perf_counter()
        executor_output = self._execute(task)
        # Run the audit pipeline which may refine the executor output
        iterations = 0
        audit_result = {}
        final_code = executor_output

        pipeline_output = self.audit_pipeline.evaluate(executor_output, persona="critic", prompt=task)
        audit_result = pipeline_output.get("audit", {})
        final_code = pipeline_output.get("final_code", executor_output)
        verdict = audit_result.get("verdict", "FAIL")
        iterations = pipeline_output.get("iterations", 0)

        duration_sec = round(time.perf_counter() - start_time, 2)
        return HyperAgentResult(
            iterations=iterations,
            duration_sec=duration_sec,
            final_output=final_code,
            verdict=verdict,
            audit=audit_result,
        )

    def _execute(self, task: str) -> str:
        prompt = (
            f"Generiraj sažeti, tehnički izvještaj i primjer koda za zadatak:\n{task}\n\n"
            "Format: Kratki opis, ključne točke, i blok koda (označen kao comment ili python/c).")

        try:
            generated = self.model.generate(prompt, max_length=512)
            header = f"# Una# HyperAgent generisani rezultat za zadatak:\n# {task}\n\n"
            return header + generated
        except Exception:
            return (
                f"# Una# HyperAgent generisani rezultat za zadatak:\n# {task}\n\n"
                "# [Fallback simulirani izlaz: model nije dostupan.]\n"
            )
