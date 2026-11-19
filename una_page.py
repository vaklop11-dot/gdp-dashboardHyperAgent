"""Streamlit stranica 'Una Asistent' (chat). Koristi se iz app.py."""
import os
import tempfile
import uuid

import streamlit as st

from una import UnaAssistant


def _secret(name: str) -> str:
    try:
        return str(st.secrets.get(name, ""))
    except Exception:  # nema secrets.toml
        return ""


def render_una_assistant() -> None:
    st.header("Una# Asistent")
    st.caption("Agenti → sinteza → Đavolji advokat → Refiner. Neprovjereno = NEMAM POTVRDU.")

    with st.expander("Podešavanja", expanded=False):
        acc_in = st.text_input("CLOUDFLARE_ACCOUNT_ID (samo za ovu sesiju)")
        tok_in = st.text_input("CLOUDFLARE_API_TOKEN (samo za ovu sesiju, ne snima se)", type="password")
        agents_raw = st.text_area(
            "Agenti — jedan po redu: ime | oblast | pravila (prazno = jedan opšti agent)",
            value=st.session_state.get("una_agents_raw", ""), height=100)
        if st.button("Primijeni"):
            st.session_state["una_agents_raw"] = agents_raw
            st.session_state.pop("una_assistant", None)
            if acc_in and tok_in:
                st.session_state["una_cf"] = (acc_in, tok_in)

    if "una_assistant" not in st.session_state:
        agents = []
        for line in st.session_state.get("una_agents_raw", "").splitlines():
            parts = [p.strip() for p in line.split("|")]
            if parts and parts[0]:
                agents.append({"name": parts[0], "domain": parts[1] if len(parts) > 1 else "opšte",
                               "rules": parts[2] if len(parts) > 2 else ""})
        acc, tok = st.session_state.get("una_cf") or (
            _secret("CLOUDFLARE_ACCOUNT_ID") or os.environ.get("CLOUDFLARE_ACCOUNT_ID", ""),
            _secret("CLOUDFLARE_API_TOKEN") or os.environ.get("CLOUDFLARE_API_TOKEN", ""))
        # Web: svaka sesija ima svoju memoriju, da se razgovori korisnika ne miješaju.
        sid = st.session_state.setdefault("una_sid", uuid.uuid4().hex)
        mem_path = os.path.join(tempfile.gettempdir(), f"una_{sid}.una")
        st.session_state["una_assistant"] = UnaAssistant(agents=agents or None, account_id=acc, api_token=tok,
                                                         memory_path=mem_path)
        st.session_state.setdefault("una_chat", [])

    asistent: UnaAssistant = st.session_state["una_assistant"]
    if asistent.demo:
        st.warning("DEMO mod: nema Cloudflare pristupa. Dodaj Account ID i token u Podešavanja ili u Streamlit secrets.")

    for msg in st.session_state["una_chat"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("meta"):
                st.caption(msg["meta"])

    pitanje = st.chat_input("Postavi pitanje…")
    if pitanje:
        st.session_state["una_chat"].append({"role": "user", "content": pitanje})
        with st.chat_message("user"):
            st.markdown(pitanje)
        with st.chat_message("assistant"):
            with st.spinner("Agenti rade, Đavolji advokat provjerava…"):
                r = asistent.ask(pitanje)
            meta = (f"{r.verdict} · tačnost {r.audit['accuracy']} · kompletnost {r.audit['completeness']} · "
                    f"sigurnost {r.audit['safety']} · popravki {r.refine_passes} · {r.duration_sec}s")
            st.markdown(r.answer)
            st.caption(meta)
            if r.trace:
                with st.expander("Trag provjere"):
                    st.code("\n".join(r.trace), language="text")
        st.session_state["una_chat"].append({"role": "assistant", "content": r.answer, "meta": meta})
