@echo off
REM MedAssist AI - Windows Stop Script
echo ========================================
echo Stopping MedAssist AI Platform
echo ========================================

echo.
echo Stopping Python processes (Backend)...
taskkill /F /IM python.exe 2>nul
if %errorlevel% equ 0 (
    echo Backend stopped successfully
) else (
    echo No backend processes found
)

echo.
echo Stopping Node processes (Frontend)...
taskkill /F /IM node.exe 2>nul
if %errorlevel% equ 0 (
    echo Frontend stopped successfully
) else (
    echo No frontend processes found
)

echo.
echo Stopping infrastructure services...
cd infrastructure
docker-compose down
cd ..

echo.
echo ========================================
echo MedAssist AI stopped
echo ========================================
pause
