@echo off
setlocal enabledelayedexpansion
title SHUBHAM NX - Tailor App
color 0A

echo.
echo  ============================================================
echo    SHUBHAM NX  -  Tailor Shop Management App
echo  ============================================================
echo.

REM ── STEP 1: Check Python ─────────────────────────────────────
echo  [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] Python is NOT installed on this computer.
    echo.
    echo  Please do the following:
    echo    1. Open your browser and go to: https://www.python.org/downloads/
    echo    2. Download Python 3.x (latest version)
    echo    3. Run the installer
    echo    4. IMPORTANT: Check "Add Python to PATH" before clicking Install
    echo    5. After installation, run this file again.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  [OK] %%v is installed.

REM ── STEP 2: Install Flask ────────────────────────────────────
echo  [2/5] Installing Flask (internet required first time)...
pip install flask -q --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo  [ERROR] Failed to install Flask.
    echo  Make sure you are connected to the internet and try again.
    echo.
    pause
    exit /b 1
)
echo  [OK] Flask is ready.

REM ── STEP 3: Kill old processes ───────────────────────────────
echo  [3/5] Clearing old processes...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5000 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)
taskkill /IM cloudflared.exe /F >nul 2>&1
if exist cloudflared.log del cloudflared.log >nul 2>&1
echo  [OK] Port 5000 is free.

REM ── STEP 4: Start Flask app ──────────────────────────────────
echo  [4/5] Starting the Tailor App...
start "SHUBHAM NX - Server" /MIN cmd /c "color 0B && echo Tailor App Server && echo Do NOT close this window && echo. && python app.py & echo. & echo Server stopped. & pause"

REM Wait for Flask to be ready
set /a flask_wait=0
:flask_check
timeout /t 1 /nobreak >nul
set /a flask_wait+=1
if !flask_wait! gtr 15 (
    echo  [ERROR] Flask did not start in time. Check for errors in the server window.
    pause
    exit /b 1
)
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:5000' -TimeoutSec 1 -UseBasicParsing; exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 goto :flask_check
echo  [OK] Tailor App is running.

REM ── STEP 5: Start Cloudflare Tunnel ─────────────────────────
echo  [5/5] Starting Cloudflare tunnel for remote access...

if not exist cloudflared.exe (
    echo  [SKIP] cloudflared.exe not found - remote access unavailable.
    echo         Download it from: https://github.com/cloudflare/cloudflared/releases
    goto :show_summary
)

start "Cloudflare Tunnel" /MIN cmd /c "cloudflared.exe tunnel --url http://localhost:5000 --logfile cloudflared.log 2>&1"

REM Wait for tunnel URL
echo  [..] Fetching public URL (please wait up to 20 seconds)...
set TUNNEL_URL=
set /a cf_wait=0

:cf_check
timeout /t 2 /nobreak >nul
set /a cf_wait+=1
if !cf_wait! gtr 15 (
    echo  [WARNING] Could not auto-detect tunnel URL.
    echo           Open cloudflared.log to find your public URL.
    set TUNNEL_URL=See cloudflared.log
    goto :show_summary
)
if not exist cloudflared.log goto :cf_check
findstr /c:"trycloudflare.com" cloudflared.log >nul 2>&1
if errorlevel 1 goto :cf_check

for /f "delims=" %%u in ('powershell -NoProfile -Command "try { (Select-String -Path 'cloudflared.log' -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com').Matches[0].Value } catch { '' }" 2^>nul') do (
    if not "%%u"=="" set TUNNEL_URL=%%u
)

REM ── Get local IP ─────────────────────────────────────────────
:show_summary
set LOCAL_IP=
for /f "tokens=2 delims=:" %%a in ('ipconfig 2^>nul ^| findstr /c:"IPv4 Address"') do (
    set _ip=%%a
    set _ip=!_ip: =!
    if not "!_ip!"=="127.0.0.1" (
        set LOCAL_IP=!_ip!
        goto :ip_done
    )
)
:ip_done

echo.
echo  ============================================================
echo    APP IS LIVE!
echo  ============================================================
echo.
echo    Open on THIS computer:
echo      http://localhost:5000
echo.
if defined LOCAL_IP (
    if not "!LOCAL_IP!"=="" (
        echo    Open on same Wi-Fi network:
        echo      http://!LOCAL_IP!:5000
        echo.
    )
)
if defined TUNNEL_URL (
    if not "!TUNNEL_URL!"=="" (
        echo    Open ANYWHERE (share this link):
        echo      !TUNNEL_URL!
        echo.
    )
)
echo  ============================================================
echo.
echo  IMPORTANT NOTES:
echo   - Keep this window open while using the app
echo   - The Cloudflare link changes every time you restart
echo   - Your data is saved in tailor.db in this folder
echo.
echo  Press any key to open the app in your browser...
pause >nul

start http://localhost:5000

echo.
echo  App is open. This window will stay open.
echo  Close this window only when you want to shut down the app.
echo.
pause
