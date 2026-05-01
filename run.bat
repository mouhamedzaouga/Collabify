@echo off
echo Starting Collabify API Backend...
start cmd /k "cd backend && python -m pip install -r requirements.txt && python -m uvicorn main:app --reload"

echo Starting Collabify Frontend...
timeout /t 3 /nobreak
start "" "frontend\projectflow_app.html"

echo Application launched! The backend terminal will stay open.
