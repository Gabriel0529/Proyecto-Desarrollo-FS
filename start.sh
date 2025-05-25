set -e

cd /app/reto-cuc-main/asset_management

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

PORT=${PORT:-8000}

echo "Starting Gunicorn on port $PORT..."
exec gunicorn --bind 0.0.0.0:$PORT --workers 2 asset_management.wsgi:application
