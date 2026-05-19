@echo off
REM MedAssist AI - Windows Startup Script
echo ========================================
echo Starting MedAssist AI Platform
echo ========================================

REM Start infrastructure services (optional)
echo.
echo Starting infrastructure services (PostgreSQL, Qdrant, Orthanc, Neo4j)...
cd infrastructure
start "Infrastructure" cmd /k "docker-compose up"
cd ..

REM Wait a moment for services to initialize
timeout /t 3 /nobreak >nul

REM Start backend
echo.
echo Starting Backend API Server...
start "Backend" cmd /k "python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend
echo.
echo Starting Frontend Development Server...
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo MedAssist AI is starting up!
echo ========================================
echo.
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Frontend: http://localhost:5173 (check terminal for actual port)
echo.
echo Press any key to exit this window (services will keep running)
pause >nul
