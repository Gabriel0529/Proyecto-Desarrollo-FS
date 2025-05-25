cd /app/reto-cuc-main/asset_management

python manage.py migrate --noinput

python manage.py collectstatic --noinput

exec gunicorn --bind 0.0.0.0:8000 --workers 2 asset_management.wsgi:application
