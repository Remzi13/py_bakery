@echo off
REM Bakery Manager - FastAPI Server Launcher for Windows CMD
REM Запускает uvicorn сервер и открывает браузер

setlocal enabledelayedexpansion

set HOST=127.0.0.1
set PORT=8000
set URL=http://%HOST%:%PORT%

echo.
echo ========================================
echo   Bakery Manager - FastAPI Server
echo ========================================
echo.

REM Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python.
    pause
    exit /b 1
)

echo OK: Python found: 
python --version

echo.
echo Checking dependencies...

REM Проверяем FastAPI
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo Installing FastAPI...
    pip install fastapi uvicorn -q
    echo OK: FastAPI installed
) else (
    echo OK: FastAPI found
)

REM Проверяем Uvicorn
python -c "import uvicorn" >nul 2>&1
if errorlevel 1 (
    echo Installing Uvicorn...
    pip install uvicorn -q
    echo OK: Uvicorn installed
) else (
    echo OK: Uvicorn found
)

echo.
echo Starting server...
echo Address: %URL%
echo.

REM Открываем браузер
start "" "%URL%"

echo.
echo OK: Server is running
echo Press Ctrl+C to stop server
echo.

REM Запускаем Uvicorn
uvicorn main:app --host %HOST% --port %PORT% --reload

pause
