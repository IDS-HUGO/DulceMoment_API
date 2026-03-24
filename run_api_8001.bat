@echo off
cd /d "D:\UNIVERSIDAD\DulceMomentAPI\backend-fastapi"
echo Iniciando API FastAPI en puerto 8001...
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
