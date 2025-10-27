#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Create necessary directories
mkdir -p staticfiles
mkdir -p media

# Collect static files (isso vai copiar de STATICFILES_DIRS para STATIC_ROOT)
python manage.py collectstatic --no-input --clear

echo "✅ Build completed successfully!"
