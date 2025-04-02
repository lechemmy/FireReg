#!/bin/sh

# Create database directory if it doesn't exist
mkdir -p /app/db_data

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Create superuser
echo "Creating superuser..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FireReg.settings')
django.setup()
exec(open('create_superuser.py').read())
"

# Start server
echo "Starting server..."
python manage.py runserver 0.0.0.0:8000
