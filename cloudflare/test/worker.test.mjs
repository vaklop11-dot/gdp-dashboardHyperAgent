import { test } from "node:test";
import assert from "node:assert/strict";
import worker, { extractText } from "../src/index.js";
import { CRITIC_SYSTEM, REFINER_SYSTEM, deterministicAudit } from "../src/pipeline.js";

const crit = (verdict = "PASS", s = 0.95, issues = []) =>
  JSON.stringify({ accuracy: s, completeness: s, safety: s, issues, verdict });

function fakeEnv({ agent = "Odgovor.", critic = [crit()], refined = "Popravljeno. Izvor: World Bank.", fail = false,
  extra = {} } = {}) {
  const calls = [];
  const seq = [...critic];
  return {
    calls,
    env: {
      MODEL_MAIN: "@cf/main", MODEL_CRITIC: "@cf/critic", ...extra,
      AI: {
        async run(model, input) {
          calls.push({ model, input });
          const sys = input.messages[0].content;
          if (sys === CRITIC_SYSTEM) return { response: seq.length > 1 ? seq.shift() : seq[0] };
          if (sys === REFINER_SYSTEM) return { response: refined };
          if (sys.startsWith("Ti si orkestrator")) return { response: "Sinteza." };
          if (fail) throw new Error("3036: daily free allocation exceeded");
          const m = sys.match(/^Ti si (.+?)\./);
          return { response: typeof agent === "function" ? agent(m[1]) : agent };
        },
      },
    },
  };
}

const post = (body, headers = {}) => new Request("https://x/api/ask", {
  method: "POST", headers: { "content-type": "application/json", ...headers }, body: JSON.stringify(body) });

test("GET / vraća chat stranicu", async () => {
  const r = await worker.fetch(new Request("https://x/"), fakeEnv().env);
  assert.equal(r.status, 200);
  assert.match(await r.text(), /UNA# ASISTENT/);
});

test("PASS iz prve; kritičar koristi drugi model", async () => {
  const { env, calls } = fakeEnv();
  const d = await (await worker.fetch(post({ question: "Šta je GDP?" }), env)).json();
  assert.equal(d.verdict, "PASS");
  assert.equal(d.refinePasses, 0);
  assert.ok(calls.some((c) => c.model === "@cf/critic" && c.input.messages[0].content === CRITIC_SYSTEM));
  assert.ok(calls.filter((c) => c.input.messages[0].content !== CRITIC_SYSTEM).every((c) => c.model === "@cf/main"));
});

test("Refiner popravlja, pa PASS", async () => {
  const { env } = fakeEnv({ critic: [crit("FAIL", 0.4, ["netačno"]), crit()] });
  const d = await (await worker.fetch(post({ question: "q" }), env)).json();
  assert.equal(d.verdict, "PASS");
  assert.equal(d.refinePasses, 1);
  assert.match(d.answer, /^Popravljeno/);
});

test("Nakon 2 popravke i dalje FAIL -> NEMAM POTVRDU", async () => {
  const { env } = fakeEnv({ critic: [crit("FAIL", 0.4, ["izmišljen broj"])] });
  const d = await (await worker.fetch(post({ question: "q" }), env)).json();
  assert.equal(d.verdict, "FAIL");
  assert.equal(d.refinePasses, 2);
  assert.match(d.answer, /NEMAM POTVRDU/);
});

test("Kritičar vrati smeće -> FAIL (fail-closed)", async () => {
  const { env } = fakeEnv({ critic: ["nije json"] });
  const d = await (await worker.fetch(post({ question: "q" }), env)).json();
  assert.equal(d.verdict, "FAIL");
});

test("Deterministički nalaz nadglasava kritičara", async () => {
  const { env } = fakeEnv({ agent: "Rast je 42% godišnje.", critic: [crit()], refined: "Rast: NEMAM POTVRDU." });
  const d = await (await worker.fetch(post({ question: "rast?" }), env)).json();
  assert.equal(d.refinePasses, 1);
  assert.equal(d.verdict, "PASS");
});

test("Više agenata: NENADLEŽAN se izbacuje, ostali se sintetizuju", async () => {
  const agents = JSON.stringify([{ name: "A", domain: "x" }, { name: "B", domain: "y" }, { name: "C", domain: "z" }]);
  const { env } = fakeEnv({ agent: (n) => (n === "A" ? "NENADLEŽAN." : `${n} odgovor`), extra: { AGENTS: agents } });
  const d = await (await worker.fetch(post({ question: "q" }), env)).json();
  assert.deepEqual(d.agentsUsed.sort(), ["B", "C"]);
  assert.equal(d.answer, "Sinteza.");
});

test("Kvota potrošena -> jasna poruka, ne pad", async () => {
  const { env } = fakeEnv({ fail: true });
  const r = await worker.fetch(post({ question: "q" }), env);
  const d = await r.json();
  assert.equal(r.status, 200);
  assert.equal(d.verdict, "FAIL");
  assert.match(d.answer, /kvota/);
});

test("Historija ide kao kontekst", async () => {
  const { env, calls } = fakeEnv();
  await worker.fetch(post({ question: "drugo", history: [{ question: "prvo pitanje", answer: "x" }] }), env);
  assert.match(calls[0].input.messages[1].content, /prvo pitanje/);
});

test("ACCESS_CODE štiti API", async () => {
  const { env, calls } = fakeEnv({ extra: { ACCESS_CODE: "tajna" } });
  assert.equal((await worker.fetch(post({ question: "q" }), env)).status, 401);
  assert.equal(calls.length, 0);
  assert.equal((await worker.fetch(post({ question: "q" }, { "x-access-code": "tajna" }), env)).status, 200);
});

test("Validacija ulaza", async () => {
  const { env } = fakeEnv();
  assert.equal((await worker.fetch(post({ question: "  " }), env)).status, 400);
  assert.equal((await worker.fetch(post({ question: "a".repeat(5000) }), env)).status, 413);
  assert.equal((await worker.fetch(new Request("https://x/api/ask"), env)).status, 405);
});

test("Oblici odgovora modela", () => {
  assert.equal(extractText({ response: "a" }), "a");
  assert.equal(extractText({ choices: [{ message: { content: "b" } }] }), "b");
  assert.throws(() => extractText({}));
});

test("Pravila: industrijska samo za industrijska pitanja; 'flash' ne okida", () => {
  assert.equal(deterministicAudit("Koji model?", "Gemini Flash je model.").verdict, "PASS");
  assert.equal(deterministicAudit("Napiši CNC firmware", "gpio read").verdict, "FAIL");
  assert.equal(deterministicAudit("Napiši CNC firmware", "gpio read, debouncing, E-Stop").verdict, "PASS");
});
