@echo off
setlocal

:: Define venv name
set VENV_NAME=venv_build_win

:: Check if venv exists
if not exist "%VENV_NAME%" (
    echo Creating virtual environment (%VENV_NAME%)...
    python -m venv %VENV_NAME%
)

:: Activate venv
echo Activating virtual environment...
call %VENV_NAME%\Scripts\activate.bat

:: Install requirements
echo Installing dependencies...
python -m pip install --upgrade pip
if exist "requirements.txt" (
    pip install -r requirements.txt
    pip install jinja2 python-multipart email-validator
) else (
    echo Warning: requirements.txt not found. Installing manually...
    pip install fastapi uvicorn sqlalchemy pydantic jinja2 python-multipart email-validator
)
pip install pyinstaller

echo Building BakeryManager for Windows...
:: --onedir: Create a directory containing the executable
:: --add-data: bundling templates and static files (Use ; for Windows separator)
:: --collect-all: grab all dependencies

pyinstaller --noconfirm --onedir --console --clean ^
    --name "BakeryManager" ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --collect-all "uvicorn" ^
    --collect-all "fastapi" ^
    --collect-all "sqlalchemy" ^
    --collect-all "jinja2" ^
    --collect-all "python-multipart" ^
    --hidden-import "uvicorn.logging" ^
    --hidden-import "uvicorn.loops" ^
    --hidden-import "uvicorn.loops.auto" ^
    --hidden-import "uvicorn.protocols" ^
    --hidden-import "uvicorn.protocols.http" ^
    --hidden-import "uvicorn.protocols.http.auto" ^
    --hidden-import "uvicorn.protocols.websockets" ^
    --hidden-import "uvicorn.protocols.websockets.auto" ^
    --hidden-import "uvicorn.lifespan.on" ^
    --hidden-import "engineio.async_drivers.threading" ^
    --hidden-import "api" ^
    --hidden-import "sql_model" ^
    launcher.py

echo ----------------------------------------------------------------
echo Build Complete!
echo The executable is located at: dist\BakeryManager\BakeryManager.exe
echo You can move the 'dist\BakeryManager' folder anywhere and run it.
echo ----------------------------------------------------------------

pause
