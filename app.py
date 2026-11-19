import streamlit as st
from gdp_dashboard import render_gdp_dashboard
from pipeline import HyperAgent
from una_page import render_una_assistant
import json
from pathlib import Path

st.set_page_config(
    page_title='Una# Revolucija',
    page_icon=':rocket:',
    layout='wide',
    initial_sidebar_state='expanded',
)


def inject_css():
    st.markdown(
        """
        <style>
        .main { background-color: #f4f5f9; }
        .hero { background: linear-gradient(135deg, #1f2937 0%, #111827 55%, #0f172a 100%); padding: 40px 40px 35px 40px; border-radius: 24px; color: #f8fafc; margin-bottom: 30px; box-shadow: 0 20px 60px rgba(15, 23, 42, 0.25); }
        .hero-title { font-size: 44px; line-height: 1.05; margin-bottom: 10px; font-weight: 800; }
        .hero-subtitle { color: #cbd5e1; font-size: 18px; margin-bottom: 24px; max-width: 720px; }
        .hero-highlight { color: #f97316; font-weight: 700; }
        .stButton>button { background-color: #ff6f1c; color: white; font-size: 20px; font-weight: 800; padding: 18px 28px; border-radius: 14px; border: none; width: 100%; transition: transform 0.18s ease, background-color 0.18s ease; box-shadow: 0 12px 25px rgba(255, 111, 28, 0.28); }
        .stButton>button:hover { background-color: #ff8c38; transform: translateY(-1px); }
        .hero-card { background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 18px; padding: 24px; margin-bottom: 18px; }
        .hero-card h4 { margin-bottom: 12px; color: #ffffff; }
        .hero-card p { margin: 0; color: #cbd5e1; }
        .agent-card { background-color: white; padding: 20px; border-radius: 16px; box-shadow: 0 15px 40px rgba(15, 23, 42, 0.12); border: 1px solid #e5e7eb; margin-bottom: 16px; }
        .section-label { color: #475569; text-transform: uppercase; letter-spacing: 1.6px; font-size: 12px; margin-bottom: 12px; }
        .app-card { background-color: white; padding: 24px; border-radius: 18px; border: 1px solid #e5e7eb; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def run_hyperagent_task(task: str):
    if 'last_result' not in st.session_state:
        st.session_state['last_result'] = None
    hyper = HyperAgent()
    result = hyper.solve(task)
    st.session_state['last_result'] = result
    return result


def display_result(rezultat, upit):
    st.markdown("<div class='section-label'>Rezultati procesa</div>", unsafe_allow_html=True)
    cols = st.columns(3)
    with cols[0]:
        st.markdown(
            """<div class=\"agent-card\"><b style=\"color:#e65c00;\">1. ANALYZER & STRATEGIST</b><br>Domain mapping, zahtjevi i plan izvršenja.</div>""",
            unsafe_allow_html=True,
        )
        if st.button('Run Analyzer', key='run_analyzer'):
            run_hyperagent_task(f'Analyzer: {upit}')

    with cols[1]:
        st.markdown(
            """<div class=\"agent-card\"><b style=\"color:#0f172a;\">2. EXECUTOR</b><br>Izvršenje zadatka i generisanje industrijskog izlaza.</div>""",
            unsafe_allow_html=True,
        )
        if st.button('Run Executor', key='run_executor'):
            run_hyperagent_task(f'Executor: {upit}')

    with cols[2]:
        st.markdown(
            """<div class=\"agent-card\"><b style=\"color:#059669;\">3. ĐAVOLJI ADVOKAT</b><br>Kritika, verifikacija i konačna presuda.</div>""",
            unsafe_allow_html=True,
        )
        if st.button('Run Critic', key='run_critic'):
            run_hyperagent_task(f'Critic: {upit}')

    verdict = rezultat.verdict if rezultat else 'N/A'
    if verdict == 'PASS':
        st.success(f'Završeno za {rezultat.duration_sec} sekundi! Iteracija: {rezultat.iterations}')
    else:
        st.error(f'Završeno za {rezultat.duration_sec} sekundi, verdict: {verdict}. Iteracija: {rezultat.iterations}')

    if getattr(rezultat, 'audit', None):
        audit = rezultat.audit
        st.markdown('### 🧠 Đavolji advokat audit')
        cols_audit = st.columns(3)
        cols_audit[0].metric(label='Accuracy', value=f"{audit.get('accuracy', 0):.0%}")
        cols_audit[1].metric(label='Completeness', value=f"{audit.get('completeness', 0):.0%}")
        cols_audit[2].metric(label='Safety', value=f"{audit.get('safety', 0):.0%}")
        st.markdown('**Pronađene greške / napomene:**')
        if audit.get('issues'):
            for issue in audit['issues']:
                st.write(f'- {issue}')
        else:
            st.write('Nema problema identifikovanih u trenutnoj reviziji.')

    st.markdown('### 📦 Finalni proizvod')
    st.code(rezultat.final_output if rezultat else '', language='python' if rezultat and 'import' in rezultat.final_output else 'text')


def render_landing_page():
    st.markdown(
        """
        <div class='hero'>
            <div style='display:flex; flex-wrap:wrap; gap:20px; align-items:center; justify-content:space-between;'>
                <div style='flex:1; min-width:320px;'>
                    <div class='hero-title'>Una# Revolucija — jedinstveni portal.</div>
                    <div class='hero-subtitle'>
                        Jedno mjesto za HyperAgent, GDP dashboard i put do pune aplikacije.
                        Pokreni, testiraj i preuzmi bez prelaska u drugi repozitorij.
                    </div>
                </div>
                <div style='flex:0 0 320px;'>
                    <div class='hero-card'>
                        <h4>Centralni landing page</h4>
                        <p>Izaberi modul u sidebaru ili klikni na dugme za brzo pokretanje.</p>
                        <div class='stButton'><button type='button'>Jednostavan ulaz u aplikaciju</button></div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader('Odaberite aplikaciju')
        st.markdown(
            """
            - **HyperAgent**: pokretanje Đavoljeg advokata sa auditom i automatskim ispravkama.
            - **GDP Dashboard**: interaktivni pregled GDP podataka i performansi.
            """
        )

    with col2:
        if st.button('🚀 Otvori HyperAgent'):
            st.session_state['page'] = 'HyperAgent'
            st.experimental_rerun()
        if st.button('📈 Otvori GDP Dashboard'):
            st.session_state['page'] = 'GDP Dashboard'
            st.experimental_rerun()

    st.markdown('---')
    st.subheader('Preuzmi i pokreni')
    st.markdown(
        'Ključne komande za lokalno pokretanje aplikacije i rad u njoj.'
    )
    st.code(
        'git clone https://github.com/vaklop11-dot/gdp-dashboardHyperAgent.git\n'
        'cd gdp-dashboardHyperAgent\n'
        'pip install -r requirements.txt\n'
        'streamlit run app.py\n',
        language='bash',
    )
    st.info('Ovaj portal je jedinstveni ulaz: koristi `app.py` kao glavnu stranicu.')
    st.markdown('---')
    st.header('Glavna funkcionalnost')
    st.markdown(
        """
        * **Landing page** sa izborom modula.
        * **HyperAgent** sa auditom i refinerom.
        * **GDP Dashboard** integrisan direktno u aplikaciju.
        """
    )


def render_hyperagent_page():
    st.header('HyperAgent')
    st.markdown('Pokreni Đavoljeg advokata, proveri izlaze i dobiješ finalni kod uz ocenu.')
    col1, col2 = st.columns([1.2, 1])

    # Left: input + run
    with col1:
        st.subheader('Ulaz (input)')
        uploaded = st.file_uploader('Učitaj tekstualni fajl sa opisom zadatka (opcionalno)', type=['txt', 'md'])
        if uploaded is not None:
            try:
                raw = uploaded.read().decode('utf-8')
            except Exception:
                raw = uploaded.read().decode('latin-1')
            upit = st.text_area(
                'Šta mašina ili sistem treba da uradi?', value=raw, height=200
            )
        else:
            upit = st.text_area(
                'Šta mašina ili sistem treba da uradi?',
                value='Dizajniraj embedded sistem za CNC kontrolu (E-Stop, SPI flash log, dual-chip ESP32-S3 + RP2040)',
                height=200,
            )

        pokreni = st.button('🚀 POKRENI AGENTE NAJJAČE', key='main_run')

    # Right: log and help
    with col2:
        st.subheader('📌 Kako ovo radi')
        st.info('HyperAgent izvršava zadatak, audit proverava rezultat, a refiner ispravlja detektovane greške.')
        st.markdown(
            """
            - **Planer + Analizator** mapiraju zadatak.
            - **Executor** generiše tehnički izlaz.
            - **Critic** daje PASS/FAIL i predlaže poboljšanja.
            """
        )
        st.markdown('---')
        st.subheader('Log anomalija')
        # Read anomaly log file if present
        log_path = Path(__file__).parent / 'data' / 'anomaly_log.jsonl'
        log_entries = []
        if log_path.exists():
            try:
                with log_path.open('r', encoding='utf-8') as fh:
                    for line in fh:
                        if line.strip():
                            try:
                                log_entries.append(json.loads(line))
                            except Exception:
                                # skip malformed lines
                                pass
            except Exception:
                log_entries = []

        if log_entries:
            # Show latest 8 entries
            for entry in log_entries[-8:][::-1]:
                st.markdown(f"**{entry.get('ID','-')}** — {entry.get('Severity','-')} — {entry.get('Date','-')}")
                st.write(entry.get('Description',''))
                st.caption(f"Fix: {entry.get('Fix','')} — Verified: {entry.get('Verified By','')}")
                st.markdown('---')
            # Download log
            try:
                with log_path.open('r', encoding='utf-8') as fh:
                    content = fh.read()
            except Exception:
                content = ''
            st.download_button('Preuzmi log anomalija', data=content, file_name='anomaly_log.jsonl')
        else:
            st.write('Nema zabeleženih anomalija.')

    if pokreni:
        with st.spinner('Agenti obrađuju podatke...'):
            rezultat = run_hyperagent_task(upit)
            display_result(rezultat, upit)
            # Provide download for final output
            try:
                out_text = rezultat.final_output if rezultat and getattr(rezultat, 'final_output', None) else ''
            except Exception:
                out_text = ''
            if out_text:
                st.download_button('Preuzmi izlaz (finalni proizvod)', data=out_text, file_name='hyperagent_result.txt')
    elif 'last_result' in st.session_state and st.session_state['last_result'] is not None:
        st.info('Prikaz poslednjeg rezultata iz sesije.')
        display_result(st.session_state['last_result'], upit)
    else:
        st.warning('Unesi zadatak i pritisni POKRENI da bi HyperAgent počeo sa radom.')

    st.markdown('---')
    st.header('Kontrolni sažetak')
    st.markdown(
        'Ovdje možeš pratiti zajednički tok rada i vidjeti šta je Đavolji advokat otkrio tokom verifikacije.'
    )


def main():
    inject_css()
    if 'page' not in st.session_state:
        st.session_state['page'] = 'Landing'

    page = st.sidebar.radio('Navigacija', ['Landing', 'Una Asistent', 'HyperAgent', 'GDP Dashboard'], index=['Landing', 'Una Asistent', 'HyperAgent', 'GDP Dashboard'].index(st.session_state['page']))
    st.session_state['page'] = page

    st.sidebar.markdown('---')
    st.sidebar.markdown('### Info i preuzimanje')
    st.sidebar.markdown('[GitHub repo](https://github.com/vaklop11-dot/gdp-dashboardHyperAgent)')
    st.sidebar.markdown('```bash\ngit clone https://github.com/vaklop11-dot/gdp-dashboardHyperAgent.git\ncd gdp-dashboardHyperAgent\npip install -r requirements.txt\nstreamlit run app.py\n```')

    if page == 'Landing':
        render_landing_page()
    elif page == 'Una Asistent':
        render_una_assistant()
    elif page == 'HyperAgent':
        render_hyperagent_page()
    else:
        render_gdp_dashboard()


if __name__ == '__main__':
    main()
