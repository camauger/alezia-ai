@echo off
echo Démarrage de l'API Alezia AI...
cd backend
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
pause