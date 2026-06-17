@echo off
echo Starting ConvictAI...

start "ConvictAI Backend" cmd /k "venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000"
start "ConvictAI Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Backend  ^-^> http://localhost:8000
echo Frontend ^-^> http://localhost:5173
echo.
echo Make sure Ollama is running: ollama serve
