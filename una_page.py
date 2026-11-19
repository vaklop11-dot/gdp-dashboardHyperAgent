"""Streamlit stranica 'Una Asistent' (chat). Koristi se iz app.py."""
import os

import streamlit as st

from una import UnaAssistant


def _secret_key() -> str:
    try:
        return str(st.secrets.get("GEMINI_API_KEY", ""))
    except Exception:  # nema secrets.toml
        return ""


def render_una_assistant() -> None:
    st.header("Una# Asistent")
    st.caption("Agenti → sinteza → Đavolji advokat → Refiner. Neprovjereno = NEMAM POTVRDU.")

    with st.expander("Podešavanja", expanded=False):
        key_in = st.text_input("GEMINI_API_KEY (samo za ovu sesiju, ne snima se)", type="password")
        agents_raw = st.text_area(
            "Agenti — jedan po redu: ime | oblast | pravila (prazno = jedan opšti agent)",
            value=st.session_state.get("una_agents_raw", ""), height=100)
        if st.button("Primijeni"):
            st.session_state["una_agents_raw"] = agents_raw
            st.session_state.pop("una_assistant", None)
            if key_in:
                st.session_state["una_key"] = key_in

    if "una_assistant" not in st.session_state:
        agents = []
        for line in st.session_state.get("una_agents_raw", "").splitlines():
            parts = [p.strip() for p in line.split("|")]
            if parts and parts[0]:
                agents.append({"name": parts[0], "domain": parts[1] if len(parts) > 1 else "opšte",
                               "rules": parts[2] if len(parts) > 2 else ""})
        key = st.session_state.get("una_key") or _secret_key() or os.environ.get("GEMINI_API_KEY", "")
        st.session_state["una_assistant"] = UnaAssistant(agents=agents or None, api_key=key)
        st.session_state.setdefault("una_chat", [])

    asistent: UnaAssistant = st.session_state["una_assistant"]
    if asistent.demo:
        st.warning("DEMO mod: nema GEMINI_API_KEY. Dodaj ključ u Podešavanja ili u Streamlit secrets.")

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
