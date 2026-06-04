import json
import shutil
import subprocess
import sys
import time
from typing import Dict, Tuple

from backend import AuditPipeline
from critic import DevilAdvocateCritic

MODEL_KEYWORDS = {
    "qwen2.5:7b": ["audit", "review", "explain", "analysis", "critic", "verify"],
    "deepseek-coder:6.7b": ["code", "embedded", "firmware", "spi", "gpio", "cnc", "flash"],
    "mistral:7b": ["design", "architecture", "strategy", "workflow", "project", "plan"],
    "nomic-embed-text": ["embed", "semantic", "search", "similarity", "vector"],
}

CONFIDENCE_THRESHOLD = 0.75
MAX_RETRIES = 3


def route_task(task: str) -> Tuple[str, float]:
    lowered = task.lower()
    scores = {}
    for model, keywords in MODEL_KEYWORDS.items():
        matches = sum(1 for keyword in keywords if keyword in lowered)
        scores[model] = matches / len(keywords)

    selected_model, confidence = max(scores.items(), key=lambda item: item[1])
    return selected_model, confidence


def is_ollama_available() -> bool:
    return shutil.which("ollama") is not None


def generate_with_ollama(model: str, prompt: str, temperature: float = 0.2) -> str:
    if not is_ollama_available():
        raise FileNotFoundError("Ollama CLI nije instaliran u ovom okruženju.")

    command = ["ollama", "run", model, "--prompt", prompt, "--temp", str(temperature)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Ollama model call failed")
    return result.stdout.strip()


def audit_answer(answer: str, prompt: str) -> Dict:
    critic = DevilAdvocateCritic()
    return critic.evaluate(answer, persona="qwen-audit", prompt=prompt)


def self_correct(task: str, model: str, initial_answer: str) -> Dict:
    answer = initial_answer
    audit = audit_answer(answer, task)
    retries = 0

    while audit["verdict"] == "FAIL" and retries < MAX_RETRIES:
        retries += 1
        injection = (
            "\n\n# SELF-CORRECTION INJECTION:\n"
            "Address the audit issues directly and improve the answer with safer, more complete details."
        )
        updated_prompt = task + "\n\nAudit issues: " + "; ".join(audit["issues"]) + injection

        try:
            answer = generate_with_ollama(model, updated_prompt)
        except FileNotFoundError:
            break
        except Exception as exc:
            print(f"[WARNING] Self-correction generation failed: {exc}")
            break

        audit = audit_answer(answer, task)

    return {
        "final_answer": answer,
        "audit": audit,
        "retries": retries,
        "fallback": audit["verdict"] == "FAIL",
    }


def run_test(task: str) -> None:
    print("=== Test Orchestrator ===")
    print(f"Task: {task}\n")

    model, confidence = route_task(task)
    print(f"Router selected model: {model}")
    print(f"Router confidence: {confidence:.2f}")

    if confidence < CONFIDENCE_THRESHOLD:
        print("[FAIL] Router confidence below threshold (0.75).")
        return
    print("[PASS] Router confidence is sufficient.")

    if is_ollama_available():
        print("[INFO] Ollama CLI found.")
        try:
            answer = generate_with_ollama(model, task)
            print("[PASS] Generation produced output from Ollama.")
        except Exception as exc:
            print(f"[FAIL] Generation failed: {exc}")
            answer = ""
    else:
        print("[WARN] Ollama CLI not available; using placeholder generation.")
        answer = f"Simulated output for task: {task}\n(Model: {model})"

    if not answer:
        print("[FAIL] No generation output available.")
        return

    audit = audit_answer(answer, task)
    print(f"[INFO] Devil's Advocate audit verdict: {audit['verdict']}")
    if audit["verdict"] == "PASS":
        print("[PASS] Audit accepted the answer on first pass.")
    else:
        print("[WARN] Audit rejected the answer on first pass.")

    correction = self_correct(task, model, answer)
    print(f"[INFO] Self-correction retries: {correction['retries']}")
    print(f"[INFO] Final verdict: {correction['audit']['verdict']}")

    if correction["fallback"]:
        print("[FAIL] Fallback triggered after 3 retries with DA rejection.")
    else:
        print("[PASS] Answer accepted after self-correction.")

    print("\n=== Final Output ===")
    print(correction["final_answer"])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        task = (
            "Dizajniraj embedded sistem za CNC kontrolu sa E-Stop, SPI flash logging i fail-safe logikom."
        )
    run_test(task)
