#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Creating uploads directory..."
mkdir -p uploads

echo "Initializing database tables..."
python -c "from app import app; from models import db; app.app_context().push(); db.create_all(); print('✓ Database initialized')"

echo "Build completed successfully!"
