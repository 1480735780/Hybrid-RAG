@echo off
REM Enterprise Ops Assistant - Start Script for Windows

echo ========================================
echo Enterprise Ops Assistant - Starting
echo ========================================

REM Check if .env file exists
if not exist .env (
    echo Error: .env file not found
    echo Please run: python scripts\setup.py
    exit /b 1
)

REM Create necessary directories
if not exist logs\app mkdir logs\app
if not exist logs\access mkdir logs\access
if not exist knowledge_base\uploads mkdir knowledge_base\uploads
if not exist knowledge_base\processed mkdir knowledge_base\processed
if not exist chroma_db mkdir chroma_db

REM Start backend
echo.
echo Starting backend...
start "Backend" cmd /c "uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for backend to start
timeout /t 5 /nobreak > nul

echo Backend started successfully

REM Start frontend
echo.
echo Starting frontend...
start "Frontend" cmd /c "streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0"

echo.
echo ========================================
echo Services started!
echo ========================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:8501
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to stop all services
pause > nul

REM Stop services
echo Stopping services...
taskkill /FI "WindowTitle eq Backend*" /F > nul 2>&1
taskkill /FI "WindowTitle eq Frontend*" /F > nul 2>&1
echo Services stopped
