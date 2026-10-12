#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/backend"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
echo "Collabify démarre sur http://localhost:8000  (Ctrl+C pour arrêter)"
exec uvicorn app.main:app --reload
