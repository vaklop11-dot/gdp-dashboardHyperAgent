#!/bin/bash
cd "$(dirname "$0")"
echo " UNA# ASISTENT — pokretanje..."
command -v python3 >/dev/null || { echo " [!] Python3 nije pronađen."; exit 1; }
[ -d venv ] || python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -q
if [ "$1" = "web" ]; then streamlit run app.py; else python3 una_cli.py; fi
