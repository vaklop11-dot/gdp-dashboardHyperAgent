# Deployment (free options)

This project can be run locally and deployed for free using Streamlit Community or Hugging Face Spaces. Below are minimal, copy-paste steps.

Local (quick test)

1. Create a virtualenv and install requirements:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the landing page / HyperAgent UI:

```bash
streamlit run app.py
```

Or run the GDP dashboard:

```bash
streamlit run streamlit_app.py
```

Streamlit Community (share.streamlit.io)

1. Push this repository to GitHub.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click "New app", connect the repository and select the branch and the file to run (choose `streamlit_app.py` or `app.py`).
4. Provide any required secrets via the Streamlit Cloud settings.

Hugging Face Spaces (streamlit runtime)

1. Create a new Space: https://huggingface.co/spaces/new
2. Choose "Streamlit" as the SDK and set the repo visibility (public is free).
3. Push the repository files to the newly created HF Space (or upload `streamlit_app.py`, `requirements.txt`, and `data/` directory).
   - Example using git:

```bash
# on your machine
git remote add hf https://huggingface.co/spaces/<your-username>/<space-name>.git
git push hf main
```

4. If your app needs secrets (API keys), set them in the Space settings (Secrets section).

Notes

- Streamlit Community and Hugging Face Spaces both have free tiers suitable for prototypes and small demos.
- For Hugging Face, public spaces are free; private spaces may require a paid tier.
- If you want continuous automated deployment from this repository, make sure the target platform has access to the repo or use a mirror.
