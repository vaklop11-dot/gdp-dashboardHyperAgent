#!/usr/bin/env python3
"""UNA# ASISTENT — terminal verzija (nasljednik UnaRevolucija main.py).

Pokretanje: python una_cli.py   (ili start.bat / start.sh)
Komande u chatu: agenti | historija | kraj
"""
import json
import os
import sys

from una.llm import find_credentials

AGENTS_FILE = "agenti.json"
ENV_FILE = ".env"


def ucitaj_env() -> None:
    if not os.path.exists(ENV_FILE):
        return
    with open(ENV_FILE, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def provjeri_kljuc() -> None:
    acc, tok = find_credentials()
    if acc and tok:
        return
    print("\n  CLOUDFLARE PRISTUP NIJE PRONAĐEN")
    print("  Cloudflare dashboard → Workers AI → Use REST API: Account ID + Create Workers AI API Token")
    acc = input("  CLOUDFLARE_ACCOUNT_ID (Enter = DEMO mod): ").strip()
    tok = input("  CLOUDFLARE_API_TOKEN: ").strip() if acc else ""
    if not (acc and tok):
        print("  [!] DEMO mod — nema AI odgovora.\n")
        return
    os.environ["CLOUDFLARE_ACCOUNT_ID"], os.environ["CLOUDFLARE_API_TOKEN"] = acc, tok
    with open(ENV_FILE, "w", encoding="utf-8") as fh:
        fh.write(f"CLOUDFLARE_ACCOUNT_ID={acc}\nCLOUDFLARE_API_TOKEN={tok}\n")
    print("  [✓] Sačuvano u .env (taj fajl ne dijeli i ne commitaj).\n")


def ucitaj_agente() -> list:
    if os.path.exists(AGENTS_FILE):
        with open(AGENTS_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    return []


def postavi_agente() -> list:
    n_raw = input("  Koliko agenata (1-5, Enter = 3): ").strip()
    n = int(n_raw) if n_raw.isdigit() and 1 <= int(n_raw) <= 5 else 3
    agenti = []
    for i in range(1, n + 1):
        print(f"\n  AGENT {i}")
        ime = input("  Ime: ").strip() or f"Agent{i}"
        oblast = input("  Oblast: ").strip() or "opšta pitanja"
        pravila = input("  Pravila (Enter = default NEMAM POTVRDU): ").strip()
        agenti.append({"name": ime, "domain": oblast, "rules": pravila})
    with open(AGENTS_FILE, "w", encoding="utf-8") as fh:
        json.dump(agenti, fh, ensure_ascii=False, indent=2)
    print("\n  [✓] Agenti sačuvani u agenti.json\n")
    return agenti


def prikazi(agenti) -> None:
    for i, a in enumerate(agenti, 1):
        print(f"  [{i}] {a['name']} — {a['domain']}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ucitaj_env()
    print("\n" + "═" * 56 + "\n  UNA# ASISTENT — agenti · Đavolji advokat · memorija\n" + "═" * 56)
    provjeri_kljuc()

    from una import UnaAssistant

    agenti = ucitaj_agente()
    if agenti:
        prikazi(agenti)
        if input("  Koristiti postojeće agente? (Enter = da / n = novi): ").strip().lower() == "n":
            agenti = postavi_agente()
    elif input("  Prva sesija. Definisati svoje agente? (d/Enter = default Una): ").strip().lower() == "d":
        agenti = postavi_agente()

    asistent = UnaAssistant(agents=agenti or None)
    if asistent.memory.load_error:
        print(f"  [!] {asistent.memory.load_error}")
    print(f"  Memorija: {len(asistent.memory.history)} zapisa. Mod: {'DEMO' if asistent.demo else asistent.llm.model}")
    print("  Komande: agenti | historija | kraj\n" + "─" * 56)

    while True:
        try:
            pitanje = input("\n  Ti → ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n  [✓] Kraj. Memorija sačuvana.")
            break
        if not pitanje:
            continue
        cmd = pitanje.lower()
        if cmd in ("kraj", "exit", "quit", "q"):
            print("  [✓] Kraj. Memorija sačuvana.")
            break
        if cmd == "agenti":
            prikazi([{"name": a.name, "domain": a.domain} for a in asistent.agents])
            continue
        if cmd == "historija":
            for h in asistent.memory.history[-5:]:
                print(f"  [{h['timestamp'][:16]}] {h.get('verdict', '?')}\n  P: {h['question'][:80]}\n"
                      f"  O: {h['answer'][:120]}...\n")
            continue
        print("  … agenti rade, Đavolji advokat provjerava …")
        r = asistent.ask(pitanje)
        print("─" * 56 + f"\n  UNA# [{r.verdict} · {r.refine_passes} popravki · {r.duration_sec}s]\n\n{r.answer}\n" + "─" * 56)


if __name__ == "__main__":
    main()
