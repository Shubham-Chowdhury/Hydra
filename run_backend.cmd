@echo off
title Hydra Backend - FastAPI
cd /d "%~dp0\backend"
echo ========================================================
echo        HYDRA DECISION SUPPORT - BACKEND SERVICE
echo ========================================================
"..\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause

