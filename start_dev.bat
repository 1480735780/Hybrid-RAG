@echo off
REM Enterprise Ops Assistant - Development Start Script

echo ========================================
echo Enterprise Ops Assistant - Dev Mode
echo ========================================

REM Check if .env file exists
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo Please edit .env file with your API Key
    pause
    exit /b 1
)

REM Create necessary directories
if not exist logs\app mkdir logs\app
if not exist logs\access mkdir logs\access
if not exist knowledge_base\uploads mkdir knowledge_base\uploads
if not exist knowledge_base\processed mkdir knowledge_base\processed
if not exist chroma_db mkdir chroma_db

echo.
echo Starting Backend (Port 8000)...
start "Backend" cmd /k "uvicorn backend.app.main:app --reload --port 8000"

echo Waiting for backend to start...
timeout /t 5 /nobreak > nul

echo.
echo Starting Frontend (Port 8501)...
start "Frontend" cmd /k "streamlit run frontend/app.py --server.port 8501"

echo.
echo ========================================
echo Services Started!
echo ========================================
echo.
echo Frontend:  http://localhost:8501
echo Backend:   http://localhost:8000
echo API Docs:  http://localhost:8000/docs
echo.
echo Press any key to stop all services...
pause > nul

echo Stopping services...
taskkill /FI "WindowTitle eq Backend*" /F > nul 2>&1
taskkill /FI "WindowTitle eq Frontend*" /F > nul 2>&1
echo Done!
