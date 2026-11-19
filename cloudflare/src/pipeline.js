// Una# Asistent — logika (UnaRevolucija agenti + HyperAgent Đavolji advokat/Refiner).
// Čista logika: model se ubacuje kao `run(model, messages) -> Promise<string>`, pa se testira bez Cloudflarea.

export const NEMAM = "NEMAM POTVRDU";
export const NENADLEZAN = "NENADLEŽAN";
export const MAX_REFINE = 2;
export const THRESHOLDS = { accuracy: 0.85, completeness: 0.8, safety: 0.9 };
export const DEFAULT_RULES = `Nikad ne pretpostavljaj. Traži potvrdu. Ako nešto ne znaš, piši: ${NEMAM}.`;
export const DEFAULT_AGENTS = [{ name: "Una", domain: "opšta pitanja, tehnika, poslovanje", rules: DEFAULT_RULES }];

export const CRITIC_SYSTEM = `Ti si Đavolji advokat i auditor. Ne odgovaraš na pitanje — samo ocjenjuješ dati odgovor.
Traži: netačnosti, neprovjerene tvrdnje predstavljene kao činjenice (brojke, procenti, datumi, imena bez izvora),
kontradikcije, izostavljene bitne dijelove pitanja, nesigurne savjete.
Odgovor koji za neprovjerenu tvrdnju piše "${NEMAM}" je ISPRAVAN i ne kažnjava se.
Vrati ISKLJUČIVO JSON bez ikakvog drugog teksta:
{"accuracy": 0.0-1.0, "completeness": 0.0-1.0, "safety": 0.0-1.0, "issues": ["konkretna mana"], "verdict": "PASS" ili "FAIL"}`;

export const REFINER_SYSTEM = `Ti si Refiner. Prepravi odgovor tako da otkloniš SVAKU navedenu manu.
Ne dodaji nove neprovjerene tvrdnje. Tvrdnju koju ne možeš potvrditi izvorom ukloni ili označi sa "${NEMAM}".
Vrati samo popravljeni odgovor, bez komentara o popravkama. Piši direktno, bez fraza ljubaznosti.`;

export const SYNTH_SYSTEM =
  "Ti si orkestrator Una# asistenta. Sintetizuj odgovore specijalizovanih agenata u jedan jasan odgovor. " +
  `Zadrži izvore. Tvrdnju bez izvora označi sa ${NEMAM}. Odgovaraj direktno, sažeto, bez kurtoazije. ` +
  "Ne spominji agente ni internu arhitekturu.";

export function agentSystem(a) {
  return `Ti si ${a.name}.\nOblast: ${a.domain}\n\n` +
    `Odgovaraj ISKLJUČIVO iz svoje oblasti. Ako pitanje nije u tvojoj oblasti, odgovori samo riječju: ${NENADLEZAN}\n\n` +
    `PRAVILA I STANDARDI (primjenjuj uvijek):\n${a.rules || DEFAULT_RULES}\n\n` +
    `Odgovaraj na jeziku pitanja, direktno i sažeto. Ako nešto ne znaš, piši: ${NEMAM}.`;
}

// ── Deterministička pravila (iz critic.py / quality.py) ─────────────────────
const INDUSTRIAL = ["gpio", "cnc", "embedded", "spi", "freertos", "firmware", "esp32", "rp2040", "plc",
  "mikrokontroler", "microcontroller"];
const IMPLEMENT_ASK = /(napi[sš]i|dizajniraj|projektuj|implementiraj|isprogramiraj|\bkod\b|\bcode\b|\bwrite\b|\bdesign\b|\bimplement|\bbuild\b|napravi)/i;
const CODE_IN_ANSWER = /```|#include|\bvoid\s+\w+\s*\(|\bdef\s+\w+\(|digitalRead|gpio_|while\s*\(/i;
const SAFETY = ["e-stop", "fail-safe", "fail safe", "emergency stop"];
const NUMBER_CLAIM = /\d+(?:[.,]\d+)?\s*(?:%|posto|procen)/i;
const SOURCE_HINT = new RegExp(`(izvor|source|https?://|prema\\s+\\S+|world bank|eurostat|${NEMAM})`, "i");

const hasWord = (text, w) => new RegExp(`\\b${w}\\b`, "i").test(text);
const verdictOf = (a, c, s) =>
  a >= THRESHOLDS.accuracy && c >= THRESHOLDS.completeness && s >= THRESHOLDS.safety ? "PASS" : "FAIL";

export function deterministicAudit(question, answer) {
  const q = question.toLowerCase(), t = answer.toLowerCase();
  const issues = [];
  // Industrijska pravila važe samo kad se traži rješenje/kod (ne za objašnjenje pojma, npr. "šta je PLC").
  const industrial = INDUSTRIAL.some((k) => hasWord(q, k)) && (IMPLEMENT_ASK.test(q) || CODE_IN_ANSWER.test(answer));
  if (industrial) {
    if (!t.includes("debounc"))
      issues.push("Kritična mana: ulazi nemaju hardverski ili softverski debouncing.");
    if (t.includes("flash") && !t.includes("ring_buffer") && !t.includes("ring-buffer") && !t.includes("ring buffer"))
      issues.push("Rizik habanja: upis u flash bez ring-buffera.");
  }
  let completeness = issues.length ? 0.7 : 0.9;
  if (NUMBER_CLAIM.test(answer) && !SOURCE_HINT.test(answer)) {
    issues.push(`Procenti/brojke bez navedenog izvora i bez oznake ${NEMAM}.`);
    completeness = Math.min(completeness, 0.7);
  }
  const accuracy = Math.max(0.5, 1 - issues.length * 0.15);
  const safety = industrial ? (SAFETY.some((k) => t.includes(k)) ? 0.95 : 0.6) : 0.95;
  return { accuracy, completeness, safety, issues, verdict: verdictOf(accuracy, completeness, safety) };
}

export function parseJson(text) {
  const clean = String(text).replace(/```(?:json)?/g, "").trim();
  const s = clean.indexOf("{"), e = clean.lastIndexOf("}");
  if (s < 0 || e <= s) throw new Error("nema JSON objekta");
  return JSON.parse(clean.slice(s, e + 1));
}

export async function llmAudit(run, model, question, answer) {
  try {
    const raw = await run(model, [
      { role: "system", content: CRITIC_SYSTEM },
      { role: "user", content: `PITANJE:\n${question}\n\nODGOVOR ZA OCJENU:\n${answer}` },
    ]);
    const d = parseJson(raw);
    const c = (v) => {
      const n = Number(v);
      if (!Number.isFinite(n)) throw new Error("ocjena nije broj");
      return Math.max(0, Math.min(1, n));
    };
    const a = c(d.accuracy), co = c(d.completeness), s = c(d.safety);
    const issues = (Array.isArray(d.issues) ? d.issues : []).map(String).filter((x) => x.trim());
    return { accuracy: a, completeness: co, safety: s, issues, verdict: verdictOf(a, co, s) };
  } catch (err) {
    // Kritičar koji ne radi ne smije propustiti odgovor.
    return { accuracy: 0, completeness: 0, safety: 0, issues: [`Kritičar nije vratio validan JSON: ${err.message}`], verdict: "FAIL" };
  }
}

export async function combinedAudit(run, model, question, answer) {
  const d = deterministicAudit(question, answer);
  const m = await llmAudit(run, model, question, answer);
  const r2 = (x) => Math.round(x * 100) / 100;
  const a = r2(Math.min(d.accuracy, m.accuracy)), c = r2(Math.min(d.completeness, m.completeness)),
    s = r2(Math.min(d.safety, m.safety));
  const issues = [...new Set([...d.issues, ...m.issues])];
  let verdict = verdictOf(a, c, s);
  if (verdict === "PASS" && d.issues.length) verdict = "FAIL"; // deterministički nalaz pobjeđuje
  return { accuracy: a, completeness: c, safety: s, issues, verdict };
}

const outOfScope = (t) => t.trim().replace(/\.+$/, "").toUpperCase() === NENADLEZAN;

function historyContext(history) {
  if (!Array.isArray(history) || !history.length) return "";
  return history.slice(-3)
    .map((h) => `P: ${String(h.question || "").slice(0, 600)}\nO: ${String(h.answer || "").slice(0, 600)}`)
    .join("\n\n");
}

/**
 * @param {{run: Function, models: {main: string, critic: string}, agents?: Array, log?: Function}} deps
 */
export async function ask(deps, question, history = []) {
  const { run, models } = deps;
  const log = deps.log || (() => {});
  const agents = deps.agents && deps.agents.length ? deps.agents : DEFAULT_AGENTS;
  const start = Date.now();
  const trace = [];
  const ctx = historyContext(history);
  const prompt = ctx ? `KONTEKST PRETHODNIH RAZMJENA:\n${ctx}\n\nNOVO PITANJE:\n${question}` : question;

  const outputs = await Promise.all(agents.map(async (a) => {
    try {
      const text = await run(models.main, [{ role: "system", content: agentSystem(a) }, { role: "user", content: prompt }]);
      return { agent: a.name, ok: true, text };
    } catch (err) {
      return { agent: a.name, ok: false, text: String(err.message || err) };
    }
  }));
  outputs.filter((o) => !o.ok).forEach((o) => trace.push(`Agent ${o.agent}: greška — ${o.text}`));
  const valid = outputs.filter((o) => o.ok && !outOfScope(o.text));

  const finish = (answer, audit, passes) => ({
    question, answer, verdict: audit.verdict, audit, refinePasses: passes,
    agentsUsed: valid.map((o) => o.agent), durationMs: Date.now() - start, trace,
    models,
  });

  if (!valid.length) {
    const msg = outputs.every((o) => o.ok)
      ? "Nijedan agent nije nadležan za ovo pitanje."
      : `Model trenutno nije dostupan (moguće da je potrošena dnevna kvota). ${NEMAM}.`;
    return finish(msg, { accuracy: 0, completeness: 0, safety: 1, issues: [msg], verdict: "FAIL" }, 0);
  }

  let answer;
  if (valid.length === 1) {
    answer = valid[0].text;
  } else {
    const joined = valid.map((o) => `=== ${o.agent} ===\n${o.text}`).join("\n\n");
    try {
      answer = await run(models.main, [
        { role: "system", content: SYNTH_SYSTEM },
        { role: "user", content: `Pitanje: ${question}\n\nOdgovori:\n${joined}\n\nSintetizuj u jedan odgovor.` },
      ]);
    } catch (err) {
      trace.push(`Sinteza nije uspjela: ${err.message}`);
      answer = joined;
    }
  }

  let audit = await combinedAudit(run, models.critic, question, answer);
  trace.push(`Audit 0: ${audit.verdict} ${JSON.stringify(audit.issues)}`);
  let passes = 0;
  while (audit.verdict === "FAIL" && passes < MAX_REFINE) {
    passes++;
    try {
      const issues = audit.issues.map((i) => `- ${i}`).join("\n") || "- (nema konkretnih nalaza)";
      answer = await run(models.main, [
        { role: "system", content: REFINER_SYSTEM },
        { role: "user", content: `PITANJE:\n${question}\n\nTRENUTNI ODGOVOR:\n${answer}\n\nMANE ZA OTKLANJANJE:\n${issues}` },
      ]);
    } catch (err) {
      trace.push(`Refiner nije uspio: ${err.message}`);
      break;
    }
    audit = await combinedAudit(run, models.critic, question, answer);
    trace.push(`Audit ${passes}: ${audit.verdict} ${JSON.stringify(audit.issues)}`);
  }

  if (audit.verdict === "FAIL") {
    answer += `\n\n---\n⚠ ${NEMAM} — odgovor nije prošao provjeru kvaliteta.\n` +
      audit.issues.map((i) => `- ${i}`).join("\n");
    log({ type: "anomaly", severity: "Major", description: audit.issues.join("; "), fix: `Označeno ${NEMAM}`,
      date: new Date().toISOString() });
  }
  return finish(answer, audit, passes);
}
