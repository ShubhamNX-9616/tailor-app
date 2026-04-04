@echo off
cd /d "%~dp0"

echo ============================================
echo   SHUBHAM NX - Tailor App
echo ============================================
echo.

:: Kill any existing process on port 5000 (prevents stale processes)
echo Clearing port 5000...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5000 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 1 /nobreak >nul

:: Find and display local IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4 Address"') do (
    set RAW_IP=%%a
    goto :found
)
:found
for /f "tokens=* delims= " %%b in ("%RAW_IP%") do set LOCAL_IP=%%b

echo   Local (this PC):  http://localhost:5000
echo   On same WiFi:     http://%LOCAL_IP%:5000
echo   (Share WiFi link with phones/tablets on the same network)
echo.
echo   Press Ctrl+C or close this window to stop.
echo ============================================
echo.

start "" "http://localhost:5000"
python app.py
pause
