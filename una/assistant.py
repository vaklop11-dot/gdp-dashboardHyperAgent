"""Una# Asistent — spoj UnaRevolucija (agenti + orkestrator + memorija) i HyperAgent (audit + refiner).

Tok jednog pitanja:
  1. Domenski agenti rade paralelno; nenadležni se izbacuju (UnaRevolucija).
  2. Orkestrator sintetizuje jedan odgovor (UnaRevolucija).
  3. Đavolji advokat: deterministička pravila + LLM kritičar (HyperAgent).
  4. FAIL -> Refiner popravlja, ponovni audit; najviše MAX_REFINE prolaza.
  5. I dalje FAIL -> odgovor se vraća sa oznakom NEMAM POTVRDU i nalazima; anomalija se loguje.
  6. Razmjena se čuva u kompresovanu memoriju.
"""
from __future__ import annotations

import concurrent.futures
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from anomaly_logger import log_anomaly

from .llm import LLMError, make_llm
from .memory import Memory
from .quality import NEMAM, Audit, combined_audit, refine

MAX_REFINE = 2
NENADLEZAN = "NENADLEŽAN"
DEFAULT_RULES = "Nikad ne pretpostavljaj. Traži potvrdu. Ako nešto ne znaš, piši: NEMAM POTVRDU."
DEFAULT_AGENTS = [
    {"name": "Una", "domain": "opšta pitanja, tehnika, poslovanje", "rules": DEFAULT_RULES},
]

SYNTH_SYSTEM = (
    "Ti si orkestrator Una# asistenta. Sintetizuj odgovore specijalizovanih agenata u jedan jasan odgovor. "
    "Zadrži izvore. Tvrdnju bez izvora označi sa NEMAM POTVRDU. "
    "Odgovaraj direktno, sažeto, bez kurtoazije. Ne spominji agente ni internu arhitekturu."
)


@dataclass
class Agent:
    name: str
    domain: str
    rules: str = DEFAULT_RULES

    @property
    def system(self) -> str:
        return (f"Ti si {self.name}.\nOblast: {self.domain}\n\n"
                f"Odgovaraj ISKLJUČIVO iz svoje oblasti. Ako pitanje nije u tvojoj oblasti, "
                f"odgovori samo riječju: {NENADLEZAN}\n\n"
                f"PRAVILA I STANDARDI (primjenjuj uvijek):\n{self.rules}\n\n"
                f"Odgovaraj direktno i sažeto. Ako nešto ne znaš, piši: {NEMAM}.")


@dataclass
class AssistantResult:
    question: str
    answer: str
    verdict: str
    audit: Dict
    refine_passes: int
    agents_used: List[str]
    duration_sec: float
    demo: bool
    trace: List[str] = field(default_factory=list)


def _is_out_of_scope(text: str) -> bool:
    return text.strip().strip(".").upper() == NENADLEZAN


class UnaAssistant:
    def __init__(self, agents: Optional[List[Dict]] = None, llm=None,
                 memory_path: str = "trenutno_stanje.una", api_key: Optional[str] = None):
        self.llm = llm or make_llm(api_key)
        self.agents = [Agent(a["name"], a["domain"], a.get("rules") or DEFAULT_RULES)
                       for a in (agents or DEFAULT_AGENTS)]
        self.memory = Memory(memory_path)

    @property
    def demo(self) -> bool:
        return not getattr(self.llm, "available", False)

    def _ask_agent(self, agent: Agent, prompt: str) -> Dict:
        try:
            return {"agent": agent.name, "ok": True, "text": self.llm.generate(prompt, system=agent.system)}
        except LLMError as exc:
            return {"agent": agent.name, "ok": False, "text": str(exc)}

    def ask(self, question: str) -> AssistantResult:
        start = time.perf_counter()
        trace: List[str] = []
        removed = self.memory.hygiene()
        if removed:
            trace.append(f"Higijena memorije: uklonjeno {removed} zapisa starijih od 30 dana.")

        ctx = self.memory.context()
        prompt = (f"KONTEKST PRETHODNIH RAZMJENA:\n{ctx}\n\nNOVO PITANJE:\n{question}" if ctx else question)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(self.agents))) as pool:
            outputs = list(pool.map(lambda a: self._ask_agent(a, prompt), self.agents))
        for o in outputs:
            if not o["ok"]:
                trace.append(f"Agent {o['agent']}: greška — {o['text']}")
        valid = [o for o in outputs if o["ok"] and not _is_out_of_scope(o["text"])]

        if not valid:
            msg = ("Nijedan agent nije nadležan za ovo pitanje." if all(o["ok"] for o in outputs)
                   else f"Model nije dostupan. {NEMAM}.")
            audit = Audit(0.0, 0.0, 1.0, [msg], "FAIL")
            return self._finish(question, msg, audit, 0, [], start, trace)

        if len(valid) == 1:
            answer = valid[0]["text"]
        else:
            joined = "\n\n".join(f"=== {o['agent']} ===\n{o['text']}" for o in valid)
            try:
                answer = self.llm.generate(
                    f"Pitanje: {question}\n\nOdgovori:\n{joined}\n\nSintetizuj u jedan odgovor.",
                    system=SYNTH_SYSTEM)
            except LLMError as exc:
                trace.append(f"Sinteza nije uspjela: {exc}")
                answer = joined

        audit = combined_audit(self.llm, question, answer)
        trace.append(f"Audit 0: {audit.verdict} {audit.issues}")
        passes = 0
        while audit.verdict == "FAIL" and passes < MAX_REFINE and not self.demo:
            passes += 1
            try:
                answer = refine(self.llm, question, answer, audit)
            except LLMError as exc:
                trace.append(f"Refiner nije uspio: {exc}")
                break
            audit = combined_audit(self.llm, question, answer)
            trace.append(f"Audit {passes}: {audit.verdict} {audit.issues}")

        if audit.verdict == "FAIL":
            answer = (f"{answer}\n\n---\n⚠ {NEMAM} — odgovor nije prošao provjeru kvaliteta.\n"
                      + "\n".join(f"- {i}" for i in audit.issues))
            try:
                log_anomaly("Major", "; ".join(audit.issues) or "FAIL bez nalaza",
                            "Audit nakon refinera", "Odgovor označen NEMAM POTVRDU",
                            verified_by="UnaAssistant")
            except Exception:
                pass

        return self._finish(question, answer, audit, passes, [o["agent"] for o in valid], start, trace)

    def _finish(self, question, answer, audit, passes, used, start, trace) -> AssistantResult:
        self.memory.add(question, answer, audit.verdict)
        try:
            self.memory.save()
        except OSError as exc:
            trace.append(f"Memorija nije sačuvana: {exc}")
        return AssistantResult(question, answer, audit.verdict, audit.as_dict(), passes, used,
                               round(time.perf_counter() - start, 2), self.demo, trace)
