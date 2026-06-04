import os
from typing import Optional

try:
    from transformers import pipeline
except Exception:
    pipeline = None


class LocalLM:
    """Light wrapper around Hugging Face transformers pipeline.

    Uses a small default model suitable for CPU inference. If `transformers`
    is unavailable, methods fall back to a deterministic stub.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or os.environ.get("LOCAL_LM_MODEL", "google/flan-t5-small")
        self._pipe = None
        if pipeline is not None:
            try:
                # Use text2text generation for instruction-style prompts
                self._pipe = pipeline("text2text-generation", model=self.model_name)
            except Exception:
                self._pipe = None

    def generate(self, prompt: str, max_length: int = 256) -> str:
        if self._pipe is None:
            # Fallback deterministic stub
            header = "# [LocalLM stub output]"
            body = "Simulirani odgovor modela: " + (prompt[:200] + "..." if len(prompt) > 200 else prompt)
            return f"{header}\n{body}\n"

        # Use the transformer pipeline to generate text
        try:
            out = self._pipe(prompt, max_length=max_length, do_sample=False)
            if isinstance(out, list) and out:
                text = out[0].get("generated_text") or out[0].get("text") or str(out[0])
                return text
            return str(out)
        except Exception:
            return "# [LocalLM generation failed]\n"
