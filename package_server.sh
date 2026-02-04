#!/bin/bash

# Exit on error
set -e

# Get version from python
# We use python to import the version variable directly
VERSION=$(python3 -c "from api.version import APP_VERSION; print(APP_VERSION)")

APP_NAME="bakery_app"
# Create the directory name using the version
DIR_NAME="${APP_NAME}_v${VERSION}"
ARCHIVE_NAME="${DIR_NAME}.tar.gz"

echo "=========================================="
echo "Starting packaging for ${APP_NAME}"
echo "Version: ${VERSION}"
echo "Output Directory: ${DIR_NAME}"
echo "Output Archive: ${ARCHIVE_NAME}"
echo "=========================================="

# Create temporary working directory for packaging
# Clean up previous temp dir if it exists (though we normally clean up at the end)
rm -rf pkg_temp
mkdir -p "pkg_temp/${DIR_NAME}"

# Create the data directory structure
# This ensures the volume mount in docker-compose has a target
mkdir -p "pkg_temp/${DIR_NAME}/data"

# Copy root configuration and entry files
echo "Copying configuration files..."
cp Dockerfile "pkg_temp/${DIR_NAME}/"
cp docker-compose.yml "pkg_temp/${DIR_NAME}/"
cp requirements.txt "pkg_temp/${DIR_NAME}/"
cp main.py "pkg_temp/${DIR_NAME}/"
cp nginx.conf "pkg_temp/${DIR_NAME}/"
cp alembic.ini "pkg_temp/${DIR_NAME}/"

# Copy the documentation
if [ -f "DOCKER_README.md" ]; then
    cp DOCKER_README.md "pkg_temp/${DIR_NAME}/README.md"
else
    echo "Files needed for deployment." > "pkg_temp/${DIR_NAME}/README.txt"
fi

# Copy source code directories
echo "Copying source directories..."
# We explicitly copy only what is needed to avoid picking up temp files or .git
cp -r api "pkg_temp/${DIR_NAME}/"
cp -r sql_model "pkg_temp/${DIR_NAME}/"
cp -r repositories "pkg_temp/${DIR_NAME}/"
cp -r templates "pkg_temp/${DIR_NAME}/"
cp -r static "pkg_temp/${DIR_NAME}/"
cp -r alembic "pkg_temp/${DIR_NAME}/"

# Verify size
SIZE=$(du -sh "pkg_temp/${DIR_NAME}" | cut -f1)
echo "Package size before compression: ${SIZE}"

# Create the archive
echo "Creating archive..."
# -C changes to pkg_temp so the stored paths start with bakery_app_vX.X.X
tar -czvf "${ARCHIVE_NAME}" -C pkg_temp "${DIR_NAME}"

# Clean up temporary directory
rm -rf pkg_temp

echo ""
echo "=========================================="
echo "Packaging Complete!"
echo "Archive created: ${ARCHIVE_NAME}"
echo "To deploy:"
echo "1. Upload ${ARCHIVE_NAME} to your server"
echo "2. Run: tar -xzvf ${ARCHIVE_NAME}"
echo "3. Enter directory: cd ${DIR_NAME}"
echo "4. Start: docker-compose up -d --build"
echo "=========================================="
