#!/bin/bash
set -e

# Define venv name
VENV_NAME="venv_build"

# Check if venv exists
if [ ! -d "$VENV_NAME" ]; then
    echo "Creating virtual environment ($VENV_NAME)..."
    python3 -m venv $VENV_NAME
fi

# Activate venv
echo "Activating virtual environment..."
# Note: We use source to activate in the current shell script execution context
source $VENV_NAME/bin/activate

# Install requirements
echo "Installing dependencies..."
# Upgrade pip to avoid warnings
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    pip install jinja2 python-multipart email-validator
else
    echo "Warning: requirements.txt not found. Installing manually..."
    pip install fastapi uvicorn sqlalchemy pydantic jinja2 python-multipart email-validator
fi
pip install pyinstaller

echo "Building BakeryManager..."
# --onedir: Create a directory containing the executable (easier for debugging and static files)
# --add-data: bundling templates and static files
# --collect-all: grab all dependencies for uvicorn, fastapi, sqlalchemy to avoid missing modules
# --name: Name of the output executable/folder

pyinstaller --noconfirm --onedir --console --clean \
    --name "BakeryManager" \
    --add-data "templates:templates" \
    --add-data "static:static" \
    --collect-all "uvicorn" \
    --collect-all "fastapi" \
    --collect-all "sqlalchemy" \
    --collect-all "jinja2" \
    --collect-all "python-multipart" \
    --hidden-import "uvicorn.logging" \
    --hidden-import "uvicorn.loops" \
    --hidden-import "uvicorn.loops.auto" \
    --hidden-import "uvicorn.protocols" \
    --hidden-import "uvicorn.protocols.http" \
    --hidden-import "uvicorn.protocols.http.auto" \
    --hidden-import "uvicorn.protocols.websockets" \
    --hidden-import "uvicorn.protocols.websockets.auto" \
    --hidden-import "uvicorn.lifespan.on" \
    --hidden-import "engineio.async_drivers.threading" \
    --hidden-import "api" \
    --hidden-import "sql_model" \
    launcher.py

echo "----------------------------------------------------------------"
echo "Build Complete!"
echo "The executable is located at: dist/BakeryManager/BakeryManager"
echo "You can move the 'dist/BakeryManager' folder anywhere and run it."
echo "----------------------------------------------------------------"
