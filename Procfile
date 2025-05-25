web: cd reto-cuc-main/asset_management && python manage.py migrate && python manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:$PORT asset_management.wsgi:application
