@echo off
cd /d "%~dp0"

echo ============================================
echo   SHUBHAM NX - Public Access Mode
echo ============================================
echo.

:: Kill any existing process on port 5000
echo Clearing port 5000...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5000 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)

:: Kill any existing cloudflared process
taskkill /IM cloudflared.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul

:: Download cloudflared if not present
if not exist "cloudflared.exe" (
    echo Downloading Cloudflare Tunnel (one time only)...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'cloudflared.exe'"
    echo Download complete.
    echo.
)

:: Start Flask in background (minimized window)
echo Starting app server...
start /min "TailorFlask" cmd /c "cd /d %~dp0 && python app.py"
timeout /t 3 /nobreak >nul

:: Start Cloudflare Tunnel (prints the public URL here)
echo.
echo ============================================
echo   Your PUBLIC link will appear below.
echo   Share it with ANY device, anywhere.
echo   (Link changes each time you run this)
echo   Close this window to stop everything.
echo ============================================
echo.
cloudflared.exe tunnel --url http://localhost:5000
pause
