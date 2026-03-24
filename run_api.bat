@echo off
cd /d "D:\UNIVERSIDAD\DulceMomentAPI\backend-fastapi"
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8002
pause
