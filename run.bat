@echo off
setlocal

cd /d "%~dp0"

echo =====================================
echo   NVMe QoS Simulator
echo =====================================

echo [1] Checking Python...
where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python not found.
    pause
    exit /b 1
)

echo [2] Creating venv if not exists...
if not exist ".venv\Scripts\activate.bat" (
    python -m venv .venv
)

echo [3] Activating venv...
call .venv\Scripts\activate.bat

echo [4] Upgrading pip...
python -m pip install --upgrade pip

echo [5] Installing dependencies...
if exist requirements.txt (
    python -m pip install -r requirements.txt
) else (
    echo No requirements.txt found. Standard library project.
)

echo [6] Generating 60 workload scenario...
python generate_samples.py

echo [7] Starting web dashboard...
start "NVMe QoS Backend" cmd /k "cd /d "%~dp0" && call .venv\Scripts\activate.bat && python server.py"

timeout /t 2 >nul
start http://127.0.0.1:8001/

echo.
echo Project is running at http://127.0.0.1:8001/
echo.

pause
endlocal

