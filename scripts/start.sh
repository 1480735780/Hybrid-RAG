#!/bin/bash

# Enterprise Ops Assistant - Start Script

set -e

echo "========================================"
echo "Enterprise Ops Assistant - Starting"
echo "========================================"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    echo "Please run: python scripts/setup.py"
    exit 1
fi

# Create necessary directories
mkdir -p logs/app logs/access knowledge_base/uploads knowledge_base/processed chroma_db

# Start backend in background
echo ""
echo "Starting backend..."
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "Error: Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "Backend started successfully"

# Start frontend
echo ""
echo "Starting frontend..."
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0 &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "Services started!"
echo "========================================"
echo ""
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:8501"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

wait
