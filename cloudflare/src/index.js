// Cloudflare Worker: chat stranica (GET /) + API (POST /api/ask). LLM = Workers AI preko env.AI (bez API ključa).
import { ask } from "./pipeline.js";
import { PAGE } from "./ui.js";

const MAX_QUESTION = 4000;

export function extractText(out) {
  if (out == null) throw new Error("Prazan odgovor modela.");
  if (typeof out === "string") return out;
  if (typeof out.response === "string") return out.response;
  if (out.response && typeof out.response === "object") return JSON.stringify(out.response);
  const c = out.choices?.[0]?.message?.content;
  if (typeof c === "string") return c;
  throw new Error("Nepoznat format odgovora modela.");
}

export function makeRun(env) {
  return async (model, messages) => {
    const out = await env.AI.run(model, { messages, max_tokens: 1024, temperature: 0.2 });
    const text = extractText(out);
    if (!text.trim()) throw new Error("Model je vratio prazan odgovor.");
    return text;
  };
}

function parseAgents(raw) {
  if (!raw) return null;
  try {
    const list = typeof raw === "string" ? JSON.parse(raw) : raw;
    return Array.isArray(list) ? list.filter((a) => a && a.name && a.domain).slice(0, 5) : null;
  } catch {
    return null;
  }
}

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json; charset=utf-8" } });

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/") {
      return new Response(PAGE, { headers: { "content-type": "text/html; charset=utf-8" } });
    }
    if (request.method === "GET" && url.pathname === "/api/health") {
      return json({ ok: true, models: { main: env.MODEL_MAIN, critic: env.MODEL_CRITIC }, access: !!env.ACCESS_CODE });
    }
    if (url.pathname !== "/api/ask") return json({ error: "Nije pronađeno." }, 404);
    if (request.method !== "POST") return json({ error: "Koristi POST." }, 405);

    // Beta zaštita: ako je postavljen ACCESS_CODE (wrangler secret), bez njega nema poziva modela.
    if (env.ACCESS_CODE && request.headers.get("x-access-code") !== env.ACCESS_CODE) {
      return json({ error: "Pogrešan ili nedostaje pristupni kod." }, 401);
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return json({ error: "Neispravan JSON." }, 400);
    }
    const question = String(body?.question || "").trim();
    if (!question) return json({ error: "Pitanje je prazno." }, 400);
    if (question.length > MAX_QUESTION) return json({ error: `Pitanje je duže od ${MAX_QUESTION} znakova.` }, 413);

    const result = await ask({
      run: makeRun(env),
      models: { main: env.MODEL_MAIN, critic: env.MODEL_CRITIC },
      agents: parseAgents(env.AGENTS),
      log: (entry) => console.log(JSON.stringify(entry)), // vidljivo u Workers Logs
    }, question, Array.isArray(body.history) ? body.history.slice(-3) : []);
    return json(result);
  },
};
