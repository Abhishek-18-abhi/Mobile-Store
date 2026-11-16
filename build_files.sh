#!/bin/bash
echo "Installing dependencies..."
python3 -m pip install -r requirements.txt

echo "Collecting static files..."
python3 manage.py collectstatic --noinput --clear

echo "Copying media files..."
mkdir -p staticfiles_build/media
cp -r media/* staticfiles_build/media/ 2>/dev/null || true
echo "Build completed successfully!"
