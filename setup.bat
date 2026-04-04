@echo off
echo ============================================
echo   Tailor App - First Time Setup
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo Please download Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo Installing required packages...
pip install flask
echo.
echo Setup complete!
echo.
echo Now run "run.bat" to start the app.
pause
