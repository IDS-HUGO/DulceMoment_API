Set-Location "D:\UNIVERSIDAD\DulceMomentAPI\backend-fastapi"
Write-Host "Iniciando API FastAPI en puerto 8001..."
& ".\.venv\Scripts\python" -m uvicorn app.main:app --host 127.0.0.1 --port 8001
