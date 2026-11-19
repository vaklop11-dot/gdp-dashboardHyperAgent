import json
from datetime import datetime, timedelta

import pytest

from una.assistant import UnaAssistant
from una.llm import DemoLLM, LLMError
from una.memory import Memory
from una.quality import CRITIC_SYSTEM, REFINER_SYSTEM


def crit(verdict="PASS", score=0.95, issues=None):
    return json.dumps({"accuracy": score, "completeness": score, "safety": score,
                       "issues": issues or [], "verdict": verdict})


class FakeLLM:
    """Odgovara po ulozi (system promptu); bilježi sve pozive."""
    available = True
    model = "fake"

    def __init__(self, agent_answers=None, critic_seq=None, refined="Popravljen odgovor. Izvor: World Bank.",
                 fail_agents=False):
        self.agent_answers = agent_answers or {}
        self.critic_seq = list(critic_seq or [crit()])
        self.refined = refined
        self.fail_agents = fail_agents
        self.calls = []

    def generate(self, prompt, system=None, json_mode=False, temperature=0.2):
        self.calls.append((system, prompt))
        if system == CRITIC_SYSTEM:
            return self.critic_seq.pop(0) if len(self.critic_seq) > 1 else self.critic_seq[0]
        if system == REFINER_SYSTEM:
            return self.refined
        if system and system.startswith("Ti si orkestrator"):
            return "Sintetizovan odgovor."
        if self.fail_agents:
            raise LLMError("429")
        for name, ans in self.agent_answers.items():
            if system and system.startswith(f"Ti si {name}."):
                return ans
        return "Odgovor."


@pytest.fixture
def mem(tmp_path, monkeypatch):
    monkeypatch.setattr("anomaly_logger.LOG_PATH", tmp_path / "log.jsonl")
    return str(tmp_path / "m.una")


def test_pass_first_try(mem):
    a = UnaAssistant(llm=FakeLLM(), memory_path=mem)
    r = a.ask("Šta je GDP?")
    assert r.verdict == "PASS" and r.refine_passes == 0 and "NEMAM POTVRDU" not in r.answer


def test_refiner_fixes(mem):
    llm = FakeLLM(critic_seq=[crit("FAIL", 0.5, ["netačno"]), crit()])
    r = UnaAssistant(llm=llm, memory_path=mem).ask("pitanje")
    assert r.verdict == "PASS" and r.refine_passes == 1 and r.answer.startswith("Popravljen")
    assert any(s == REFINER_SYSTEM and "netačno" in p for s, p in llm.calls)


def test_fail_after_max_refines_marked(mem, tmp_path):
    llm = FakeLLM(critic_seq=[crit("FAIL", 0.5, ["izmišljen broj"])])
    r = UnaAssistant(llm=llm, memory_path=mem).ask("pitanje")
    assert r.verdict == "FAIL" and r.refine_passes == 2
    assert "NEMAM POTVRDU" in r.answer and "izmišljen broj" in r.answer
    assert (tmp_path / "log.jsonl").exists()


def test_deterministic_overrides_llm(mem):
    # Model kaže PASS, ali odgovor ima procenat bez izvora -> FAIL, pa refiner.
    llm = FakeLLM(agent_answers={"Una": "Rast je 42% godišnje."}, critic_seq=[crit()])
    r = UnaAssistant(llm=llm, memory_path=mem).ask("rast?")
    assert r.refine_passes == 1 and r.verdict == "PASS"


def test_out_of_scope_filtered_and_synthesis(mem):
    agents = [{"name": "A", "domain": "x"}, {"name": "B", "domain": "y"}, {"name": "C", "domain": "z"}]
    llm = FakeLLM(agent_answers={"A": "NENADLEŽAN", "B": "b odgovor", "C": "c odgovor"})
    r = UnaAssistant(agents=agents, llm=llm, memory_path=mem).ask("q")
    assert sorted(r.agents_used) == ["B", "C"] and r.answer == "Sintetizovan odgovor."


def test_all_out_of_scope(mem):
    llm = FakeLLM(agent_answers={"Una": "NENADLEŽAN."})
    r = UnaAssistant(llm=llm, memory_path=mem).ask("q")
    assert r.verdict == "FAIL" and "nadležan" in r.answer


def test_model_down(mem):
    r = UnaAssistant(llm=FakeLLM(fail_agents=True), memory_path=mem).ask("q")
    assert r.verdict == "FAIL" and "NEMAM POTVRDU" in r.answer


def test_demo_never_passes(mem):
    r = UnaAssistant(llm=DemoLLM(), memory_path=mem).ask("q")
    assert r.demo and r.verdict == "FAIL" and r.refine_passes == 0


def test_memory_persist_context_and_hygiene(mem):
    llm = FakeLLM()
    UnaAssistant(llm=llm, memory_path=mem).ask("prvo pitanje")
    a2 = UnaAssistant(llm=llm, memory_path=mem)
    assert len(a2.memory.history) == 1
    a2.ask("drugo")
    assert any("prvo pitanje" in p for _, p in llm.calls[-6:])
    m = Memory(mem)
    m.history.append({"question": "staro", "answer": "x", "timestamp": (datetime.now() - timedelta(days=40)).isoformat()})
    m.history.append({"question": "bez mikrosekundi", "answer": "x", "timestamp": "2026-11-19 10:00:00"})
    assert m.hygiene(now=datetime(2026, 11, 20)) == 1


def test_corrupt_memory(tmp_path):
    p = tmp_path / "bad.una"
    p.write_bytes(b"not zlib")
    m = Memory(str(p))
    assert m.load_error and m.history == []


def test_cloudflare_request_shape(monkeypatch):
    from una import llm as L
    seen = []

    class R:
        status_code = 200
        def json(self):
            return {"success": True, "result": {"response": "ok"}}

    def fake_post(url, **kw):
        seen.append((url, kw))
        return R()

    monkeypatch.setattr(L.requests, "post", fake_post)
    c = L.CloudflareLLM("ACC", "TOK", model="@cf/main", critic_model="@cf/critic")
    assert c.generate("pitanje", system="sys") == "ok"
    assert c.generate("ocijeni", system="k", json_mode=True) == "ok"
    assert seen[0][0] == "https://api.cloudflare.com/client/v4/accounts/ACC/ai/run/@cf/main"
    assert seen[1][0].endswith("/ai/run/@cf/critic")
    assert seen[0][1]["headers"]["Authorization"] == "Bearer TOK"
    assert seen[0][1]["json"]["messages"][0] == {"role": "system", "content": "sys"}


def test_cloudflare_error_raises(monkeypatch):
    from una import llm as L

    class R:
        status_code = 429
        def json(self):
            return {"success": False, "errors": [{"message": "limit"}]}

    monkeypatch.setattr(L.requests, "post", lambda url, **kw: R())
    with pytest.raises(L.LLMError):
        L.CloudflareLLM("A", "T", retries=0).generate("x")


def test_no_credentials_is_demo(monkeypatch):
    from una import llm as L
    monkeypatch.delenv("CLOUDFLARE_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
    assert isinstance(L.make_llm(), L.DemoLLM)
