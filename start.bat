@echo off
chcp 65001 >nul
echo ========================================
echo   Enterprise Ops Assistant
echo   基于 Hybrid RAG 的企业智能运维知识库
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

REM Check .env
if not exist .env (
    echo [INFO] Creating .env from template...
    copy .env.example .env >nul
    echo [WARN] Please edit .env and add your API Key before starting!
    echo.
    pause
)

REM Create directories
if not exist logs\app mkdir logs\app
if not exist logs\access mkdir logs\access
if not exist knowledge_base\uploads mkdir knowledge_base\uploads
if not exist knowledge_base\processed mkdir knowledge_base\processed
if not exist chroma_db mkdir chroma_db

echo [1/2] Starting Backend (Port 8000)...
start "Backend" cmd /k "title Backend - Port 8000 && uvicorn backend.app.main:app --reload --port 8000"

echo [2/2] Starting Frontend (Port 8501)...
timeout /t 3 /nobreak >nul
start "Frontend" cmd /k "title Frontend - Port 8501 && streamlit run frontend/app.py --server.port 8501"

echo.
echo ========================================
echo   Services Started!
echo ========================================
echo.
echo   Frontend:  http://localhost:8501
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo.
echo   Press any key to stop all services...
echo ========================================
pause >nul

echo Stopping services...
taskkill /FI "WindowTitle eq Backend*" /F >nul 2>&1
taskkill /FI "WindowTitle eq Frontend*" /F >nul 2>&1
echo Done!
