@echo off
title SIH26261 - Backend Server (FastAPI)
cd /d "C:\Users\shivaram tunguri\.gemini\antigravity\scratch\sih26261-prototype\backend"
echo ===================================================
echo Starting SIH26261 Backend Server on http://127.0.0.1:8000
echo ===================================================
"C:\Users\shivaram tunguri\anaconda3\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pause
