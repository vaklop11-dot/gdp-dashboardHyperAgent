# :earth_americas: Una# Revolucija

Una# Revolucija je data-driven Streamlit aplikacija i sistem za analizu GDP/indikatora sa automatskim auditom.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://gdp-dashboard-template.streamlit.app/)

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the landing page / HyperAgent UI

   ```
   $ streamlit run app.py --server.port 8503
   ```

3. Run the test orchestrator

   ```
   $ python test_orchestrator.py
   ```

   If `ollama` is installed, the script will use the configured model routing and actual generation calls. If `ollama` is not available, it will fall back to a placeholder generation while still exercising the audit and self-correction logic.

4. Alternative data dashboard

   ```
   $ streamlit run streamlit_app.py
   ```

5. Industry CNC Controller spec

   ```
   $ cat INDUSTRY_CNC_CONTROLLER_SPEC.md
   ```

## Immediate run scripts

Use the included helper scripts for one-command startup.

```bash
$ ./run_hyperagent.sh
$ ./run_test.sh

## Additional tools and testing

- Terms of Use PDF: `TERMS_OF_USE.pdf` (generated from `TERMS_OF_USE.md`).
- Anomaly log: `data/anomaly_log.jsonl` — automated anomalies are appended here per project pravilnik.
- CLI runner: `python run_agent_cli.py "Describe task here"`

## CI / Deployment

1. The repository includes a GitHub Actions workflow `.github/workflows/una_revolucija.yml` which can run the Streamlit app on push or manual dispatch. To enable Anthropic usage set a repository secret named `ANTHROPIC_API_KEY` under Settings → Secrets → Actions.

## Tests

Run tests with `pytest`:

```bash
pip install pytest
pytest -q
```
```
