import json
from typing import Dict

from config import MAX_ITERATIONS
from critic import DevilAdvocateCritic
from refiner import Refiner
from anomaly_logger import log_anomaly


class AuditPipeline:
    def __init__(self):
        self.critic = DevilAdvocateCritic()
        self.refiner = Refiner()

    def evaluate(self, code: str, persona: str = "", prompt: str = "") -> Dict:
        """Evaluates code with the critic and optionally refines on FAIL.

        Returns a dict with keys: final_code (str) and audit (dict)
        """
        current_code = code
        last_output: Dict = {}

        for iteration in range(1, MAX_ITERATIONS + 1):
            output_json = self.critic.evaluate_json(current_code, persona, prompt)
            last_output = json.loads(output_json)

            # Log anomalies detected by critic
            issues = last_output.get('issues', [])
            if issues:
                try:
                    log_anomaly(
                        severity='Major' if len(issues) > 0 else 'Minor',
                        description='; '.join(issues),
                        root_cause='Automatic critic detection',
                        fix='Refiner attempted automated fixes',
                        verified_by='AuditPipeline'
                    )
                except Exception:
                    pass

            if last_output.get("verdict") == "PASS":
                return {"final_code": current_code, "audit": last_output, "iterations": iteration}

            # Attempt refinement
            current_code = self.refiner.refine(current_code, last_output)

        return {"final_code": current_code, "audit": last_output, "iterations": MAX_ITERATIONS}


if __name__ == "__main__":
    sample_code = """// CNC kontroler
// GPIO input without debouncing
if (gpio_read(pin)) {
    spi_flash_write(data);
}
"""
    prompt = "Una# Edge AI kontrola"
    pipeline = AuditPipeline()
    print(pipeline.evaluate(sample_code, persona="critic", prompt=prompt))
