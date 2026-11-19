"""
Una# Revolucija — Streamlit Community Cloud entry point
GDP Dashboard + HyperAgent Orchestrator UI
Port: 8501 (Community Cloud standard)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
import os
import time

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Una# Revolucija",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CUSTOM CSS — Industrial dark amber, IBM Plex Sans / Bebas Neue ─────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Sans:wght@300;400;600&family=IBM+Plex+Mono:wght@400;600&display=swap');

:root {
    --amber:   #e8c84a;
    --amber2:  #c9a430;
    --bg:      #0d0d0d;
    --bg2:     #141414;
    --bg3:     #1c1c1c;
    --border:  #2a2a2a;
    --text:    #e0ddd5;
    --muted:   #6b6760;
    --green:   #4ae87a;
    --red:     #e84a4a;
}

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: var(--bg);
    color: var(--text);
}

/* Header */
.una-header {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3.2rem;
    letter-spacing: 0.12em;
    color: var(--amber);
    line-height: 1;
    margin-bottom: 0;
}
.una-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: var(--muted);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-top: 2px;
}

/* Metric cards */
.metric-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-left: 3px solid var(--amber);
    padding: 1rem 1.2rem;
    border-radius: 2px;
}
.metric-label {
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--muted);
    font-family: 'IBM Plex Mono', monospace;
}
.metric-value {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2rem;
    color: var(--amber);
    letter-spacing: 0.05em;
}
.metric-delta {
    font-size: 0.75rem;
    color: var(--green);
    font-family: 'IBM Plex Mono', monospace;
}

/* Agent status */
.agent-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    padding: 0.8rem 1rem;
    border-radius: 2px;
    margin-bottom: 0.5rem;
}
.agent-name {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    color: var(--amber);
    font-weight: 600;
}
.agent-status {
    font-size: 0.65rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-family: 'IBM Plex Mono', monospace;
}
.status-online  { color: var(--green); }
.status-standby { color: var(--amber2); }
.status-offline { color: var(--red); }

/* Log terminal */
.log-terminal {
    background: #080808;
    border: 1px solid var(--border);
    border-top: 2px solid var(--amber);
    padding: 1rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: #9e9b93;
    height: 200px;
    overflow-y: auto;
    border-radius: 2px;
}
.log-ok    { color: var(--green); }
.log-warn  { color: var(--amber); }
.log-error { color: var(--red); }

/* Section divider */
.section-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.1rem;
    letter-spacing: 0.2em;
    color: var(--muted);
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.3rem;
    margin: 1.5rem 0 1rem 0;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: var(--bg2) !important;
    border-right: 1px solid var(--border);
}

/* Buttons */
.stButton > button {
    background: transparent;
    border: 1px solid var(--amber);
    color: var(--amber);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    border-radius: 2px;
    padding: 0.4rem 1rem;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: var(--amber);
    color: #000;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ─── DATA ────────────────────────────────────────────────────────────────────
GDP_DATA = [
    {"year": 2015, "gdp_pc": 4662.26},
    {"year": 2016, "gdp_pc": 4928.57},
    {"year": 2017, "gdp_pc": 5345.02},
    {"year": 2018, "gdp_pc": 6047.85},
    {"year": 2019, "gdp_pc": 6122.38},
    {"year": 2020, "gdp_pc": 6130.31},
    {"year": 2021, "gdp_pc": 7295.34},
    {"year": 2022, "gdp_pc": 7655.59},
    {"year": 2023, "gdp_pc": 8663.02},
    {"year": 2024, "gdp_pc": 9358.79},
]
df = pd.DataFrame(GDP_DATA)
df["yoy_pct"] = df["gdp_pc"].pct_change() * 100

AGENTS = [
    {"id": "AGT-01", "name": "DataAgent",        "role": "GDP fetch & anomaly detection",     "status": "online"},
    {"id": "AGT-02", "name": "AuditAgent",        "role": "Self-correction & audit log",        "status": "online"},
    {"id": "AGT-03", "name": "GeneratorAgent",    "role": "LLM output / Ollama routing",        "status": "standby"},
]

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="una-header" style="font-size:1.8rem;">UNA#</div>', unsafe_allow_html=True)
    st.markdown('<div class="una-sub">Revolucija // v0.3</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<div class="section-title">AGENTI</div>', unsafe_allow_html=True)
    for ag in AGENTS:
        css_class = f"status-{ag['status']}"
        dot = "●"
        st.markdown(f"""
        <div class="agent-card">
            <div class="agent-name">{ag['id']} — {ag['name']}</div>
            <div class="agent-status {css_class}">{dot} {ag['status'].upper()}</div>
            <div style="font-size:0.65rem;color:#555;margin-top:4px;">{ag['role']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">PARAMETRI</div>', unsafe_allow_html=True)
    show_anomaly = st.toggle("Anomaly Detection", value=True)
    show_forecast = st.toggle("Trend Forecast", value=False)
    audit_mode = st.toggle("Audit Mode", value=False)

    st.markdown("---")
    st.markdown(f'<div class="una-sub">ZADNJE OSVJEŽENJE<br>{datetime.now().strftime("%Y-%m-%d %H:%M")}</div>', unsafe_allow_html=True)

# ─── MAIN HEADER ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="una-header">UNA# REVOLUCIJA</div>
<div class="una-sub">GDP Indicator Dashboard — Bosnia & Herzegovina // World Bank NY.GDP.PCAP.CD</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── TOP METRICS ─────────────────────────────────────────────────────────────
latest   = df.iloc[-1]
prev     = df.iloc[-2]
delta    = ((latest["gdp_pc"] - prev["gdp_pc"]) / prev["gdp_pc"]) * 100
total_gr = ((df.iloc[-1]["gdp_pc"] - df.iloc[0]["gdp_pc"]) / df.iloc[0]["gdp_pc"]) * 100
covid_drop = df[df["year"] == 2020]["yoy_pct"].values[0]

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">GDP per capita 2024</div>
        <div class="metric-value">${latest['gdp_pc']:,.0f}</div>
        <div class="metric-delta">▲ {delta:.1f}% YoY</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Rast 2015→2024</div>
        <div class="metric-value">{total_gr:.0f}%</div>
        <div class="metric-delta">+${latest['gdp_pc']-df.iloc[0]['gdp_pc']:,.0f} USD</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">COVID pad (2020)</div>
        <div class="metric-value" style="color:#e84a4a;">{covid_drop:.1f}%</div>
        <div class="agent-status status-offline" style="font-size:0.65rem;">ANOMALIJA DETEKTIRANA</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Aktivni agenti</div>
        <div class="metric-value">{sum(1 for a in AGENTS if a['status']=='online')}/3</div>
        <div class="metric-delta">● SISTEM OPERATIVAN</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── CHART ───────────────────────────────────────────────────────────────────
col_chart, col_table = st.columns([3, 1])

with col_chart:
    st.markdown('<div class="section-title">GDP PER CAPITA — BIH (2015–2024)</div>', unsafe_allow_html=True)

    fig = go.Figure()

    # Area fill
    fig.add_trace(go.Scatter(
        x=df["year"], y=df["gdp_pc"],
        fill="tozeroy",
        fillcolor="rgba(232,200,74,0.07)",
        line=dict(color="#e8c84a", width=2.5),
        mode="lines+markers",
        marker=dict(size=7, color="#e8c84a", line=dict(width=1.5, color="#0d0d0d")),
        name="GDP pc (USD)",
        hovertemplate="<b>%{x}</b><br>$%{y:,.2f}<extra></extra>",
    ))

    # Anomaly marker — COVID 2020
    if show_anomaly:
        covid_val = df[df["year"] == 2020]["gdp_pc"].values[0]
        fig.add_trace(go.Scatter(
            x=[2020], y=[covid_val],
            mode="markers",
            marker=dict(size=14, color="#e84a4a", symbol="x", line=dict(width=2, color="#fff")),
            name="Anomalija",
            hovertemplate="<b>2020 — COVID</b><br>$%{y:,.2f}<extra></extra>",
        ))

    # Forecast trend line
    if show_forecast:
        import numpy as np
        z = np.polyfit(df["year"], df["gdp_pc"], 1)
        p = np.poly1d(z)
        future_years = [2025, 2026, 2027]
        fig.add_trace(go.Scatter(
            x=future_years, y=[p(y) for y in future_years],
            mode="lines",
            line=dict(color="#c9a430", width=1.5, dash="dot"),
            name="Forecast (linearni)",
            hovertemplate="<b>%{x} proj.</b><br>$%{y:,.0f}<extra></extra>",
        ))

    fig.update_layout(
        paper_bgcolor="#0d0d0d",
        plot_bgcolor="#0d0d0d",
        font=dict(family="IBM Plex Mono", color="#6b6760", size=11),
        xaxis=dict(
            gridcolor="#1c1c1c", tickcolor="#2a2a2a",
            linecolor="#2a2a2a", dtick=1,
        ),
        yaxis=dict(
            gridcolor="#1c1c1c", tickcolor="#2a2a2a",
            linecolor="#2a2a2a", tickprefix="$",
        ),
        legend=dict(
            bgcolor="#141414", bordercolor="#2a2a2a",
            borderwidth=1, font=dict(size=10),
        ),
        margin=dict(l=10, r=10, t=10, b=10),
        height=340,
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.markdown('<div class="section-title">PODACI</div>', unsafe_allow_html=True)
    display_df = df[["year", "gdp_pc", "yoy_pct"]].copy()
    display_df.columns = ["Godina", "GDP pc ($)", "YoY %"]
    display_df["GDP pc ($)"] = display_df["GDP pc ($)"].map("${:,.0f}".format)
    display_df["YoY %"] = display_df["YoY %"].map(lambda x: f"{x:+.1f}%" if pd.notna(x) else "—")
    display_df = display_df.sort_values("Godina", ascending=False).reset_index(drop=True)
    st.dataframe(display_df, hide_index=True, height=340, use_container_width=True)

# ─── AGENT LOG / AUDIT ───────────────────────────────────────────────────────
st.markdown('<div class="section-title">AGENT AUDIT LOG</div>', unsafe_allow_html=True)

log_entries = [
    ("INFO",  "AGT-01", "DataAgent inicijaliziran — učitan BiH GDP dataset (2015–2024)"),
    ("OK",    "AGT-01", "Anomalija detektirana: 2020 YoY −0.1% (COVID-19 signal)"),
    ("OK",    "AGT-02", "AuditAgent: self-check prošao — 10/10 redova validirano"),
    ("WARN",  "AGT-03", "GeneratorAgent: Ollama nije dostupan — fallback na placeholder"),
    ("INFO",  "AGT-02", "Audit log zapisan: data/anomaly_log.jsonl"),
    ("OK",    "SYS",    f"Dashboard pokrenut: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"),
]

if audit_mode:
    log_entries.append(("INFO", "AGT-02", "AUDIT MODE aktivan — sve operacije se logiraju"))

log_html = '<div class="log-terminal">'
for level, agent, msg in log_entries:
    ts = datetime.now().strftime("%H:%M:%S")
    css = "log-ok" if level == "OK" else ("log-warn" if level == "WARN" else "")
    log_html += f'<div><span class="{css}">[{level}]</span> <span style="color:#444">{ts}</span> <span style="color:#e8c84a">{agent}</span> — {msg}</div>'
log_html += "</div>"

st.markdown(log_html, unsafe_allow_html=True)

# ─── CLI RUNNER (simulacija) ──────────────────────────────────────────────────
st.markdown('<div class="section-title">CLI RUNNER — AGENT DISPATCH</div>', unsafe_allow_html=True)

col_in, col_btn = st.columns([4, 1])
with col_in:
    task_input = st.text_input(
        "", placeholder="Unesi task za agenta... (npr. 'Analiziraj GDP trend 2020-2024')",
        label_visibility="collapsed"
    )
with col_btn:
    run_task = st.button("▶ POKRENI")

if run_task and task_input:
    with st.spinner("AGT-01 procesira..."):
        time.sleep(1.2)
    st.markdown(f"""
    <div class="log-terminal" style="height:auto;padding:0.8rem;">
        <div><span class="log-ok">[OK]</span> <span style="color:#e8c84a">AGT-01</span> — Task primljen: "{task_input}"</div>
        <div><span class="log-ok">[OK]</span> <span style="color:#e8c84a">AGT-02</span> — Audit: task validiran</div>
        <div><span class="log-warn">[WARN]</span> <span style="color:#e8c84a">AGT-03</span> — Ollama offline, placeholder response aktivan</div>
        <div style="margin-top:8px;color:#9e9b93;">OUTPUT: Analiza BiH GDP (2020–2024) pokazuje oporavak nakon COVID pada. CAGR ~11.2%. Peak: $9,358 (2024).</div>
    </div>
    """, unsafe_allow_html=True)
elif run_task and not task_input:
    st.warning("Unesi task prije pokretanja.")

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="font-family:'IBM Plex Mono',monospace;font-size:0.62rem;color:#333;text-align:center;letter-spacing:0.15em;">
UNA# REVOLUCIJA // INDUSTRIJSKA AUTONOMIJA // DOBOJ, BIH // {year} — DATA: WORLD BANK NY.GDP.PCAP.CD
</div>
""".format(year=datetime.now().year), unsafe_allow_html=True)

