#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ -f requirements.txt ]; then
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
fi

python test_orchestrator.py
