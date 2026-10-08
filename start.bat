@echo off
chcp 65001 >nul
title KHunter - Start

cd /d "%~dp0"

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)

:: Use system Python
echo Using system Python...

:: Install dependencies
if exist "requirements.txt" (
    echo Installing dependencies...
    pip install -r requirements.txt -q
)

<<<<<<< HEAD
:: Start server
echo.
echo Starting KHunter...
=======
:: Start scheduler (daemon mode)
echo.
echo Starting scheduler daemon...
:: start "KHunter Scheduler" python main.py schedule

:: Start server
echo.
echo Starting KHunter Web Server...
>>>>>>> 9b2e8f0b179c4c897fac899673bf9c0751b5507e
python web_server.py

pause
