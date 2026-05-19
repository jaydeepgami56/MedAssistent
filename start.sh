#!/bin/bash
# MedAssist AI - Unix/Linux/Mac Startup Script

echo "========================================"
echo "Starting MedAssist AI Platform"
echo "========================================"

# Start infrastructure services (optional)
echo ""
echo "Starting infrastructure services (PostgreSQL, Qdrant, Orthanc, Neo4j)..."
cd infrastructure
docker-compose up -d
cd ..

# Wait for services to initialize
sleep 3

# Start backend
echo ""
echo "Starting Backend API Server..."
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
echo ""
echo "Starting Frontend Development Server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================"
echo "MedAssist AI is running!"
echo "========================================"
echo ""
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Frontend: http://localhost:5173 (check terminal for actual port)"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "To stop all services, run: ./stop.sh"
echo ""

# Keep script running
wait
