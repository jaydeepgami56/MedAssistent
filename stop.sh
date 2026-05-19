#!/bin/bash
# MedAssist AI - Unix/Linux/Mac Stop Script

echo "========================================"
echo "Stopping MedAssist AI Platform"
echo "========================================"

echo ""
echo "Stopping Python processes (Backend)..."
pkill -f "uvicorn main:app" && echo "Backend stopped successfully" || echo "No backend processes found"

echo ""
echo "Stopping Node processes (Frontend)..."
pkill -f "vite" && echo "Frontend stopped successfully" || echo "No frontend processes found"

echo ""
echo "Stopping infrastructure services..."
cd infrastructure
docker-compose down
cd ..

echo ""
echo "========================================"
echo "MedAssist AI stopped"
echo "========================================"
