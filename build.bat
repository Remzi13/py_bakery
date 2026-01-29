@echo off
setlocal

set VENV_NAME=venv_build_win

if exist %VENV_NAME% goto :activate
echo Creating virtual environment...
python -m venv %VENV_NAME%

:activate
echo Activating virtual environment...
call %VENV_NAME%\Scripts\activate.bat

echo Installing dependencies...
python -m pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy pydantic jinja2 python-multipart email-validator pyinstaller

echo ----------------------------------------------------------------
echo Starting PyInstaller Build...
echo ----------------------------------------------------------------

:: Запускаем сборку
pyinstaller --noconfirm --onedir --console --clean --name "BakeryManager" --add-data "templates;templates" --add-data "static;static" --collect-all "uvicorn" --collect-all "fastapi" --collect-all "sqlalchemy" --collect-all "jinja2" --collect-all "python-multipart" --hidden-import "uvicorn.logging" --hidden-import "uvicorn.loops" --hidden-import "uvicorn.loops.auto" --hidden-import "uvicorn.protocols" --hidden-import "uvicorn.protocols.http" --hidden-import "uvicorn.protocols.http.auto" --hidden-import "uvicorn.protocols.websockets" --hidden-import "uvicorn.protocols.websockets.auto" --hidden-import "uvicorn.lifespan.on" --hidden-import "engineio.async_drivers.threading" --hidden-import "api" --hidden-import "sql_model" launcher.py

echo ----------------------------------------------------------------
echo Checking for output...

if exist "dist\BakeryManager" (
    echo SUCCESS: Folder 'dist\BakeryManager' found! 
    dir "dist\BakeryManager\BakeryManager.exe"
) else (
    echo ERROR: Folder 'dist' was NOT created. Check PyInstaller logs above.
)
echo ----------------------------------------------------------------

pause