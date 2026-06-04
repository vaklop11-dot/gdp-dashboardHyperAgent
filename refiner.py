from typing import Dict
from anomaly_logger import log_anomaly


class Refiner:
    """A simple refiner stub for the Đavolji advokat feedback loop."""

    def refine(self, code: str, critique: Dict) -> str:
        issues = critique.get("issues", [])
        if not issues:
            return code

        # Attempt simple automated fixes for common embedded issues
        fixed = code
        fixes_applied = []

        for issue in issues:
            if 'debounc' in issue.lower():
                # append a debounce suggestion block
                debounce_snippet = (
                    "\n// Refiner Suggestion: add software debouncing for buttons\n"
                    "// Example (pseudo):\n// static uint32_t last_press_time = 0;\n// if (millis() - last_press_time > 50) { /* accept */ }\n"
                )
                fixed += debounce_snippet
                fixes_applied.append('debounce')
            if 'ring-buffer' in issue.lower() or 'ring buffer' in issue.lower() or 'flash' in issue.lower():
                ring_snippet = (
                    "\n// Refiner Suggestion: use ring buffer for flash writes to avoid wear\n"
                    "// Example: buffer data in RAM and flush in larger aligned blocks.\n"
                )
                fixed += ring_snippet
                fixes_applied.append('ring-buffer')

        # If no automated fixes, just annotate issues
        if not fixes_applied:
            comments = "\n".join(f"// ISSUE: {issue}" for issue in issues)
            fixed = f"{code}\n\n/* Refiner: address the following issues */\n{comments}"

        # Log the anomaly per project pravilnik
        try:
            log_anomaly(
                severity='Major',
                description='; '.join(issues),
                root_cause='Automated critic detection',
                fix='; '.join(fixes_applied) if fixes_applied else 'Manual review required',
                verified_by='Refiner'
            )
        except Exception:
            pass

        return fixed
