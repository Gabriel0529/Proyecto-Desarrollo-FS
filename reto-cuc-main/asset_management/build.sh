set -o errexit

pip install -r requirements.txt

cd reto-cuc-main/asset_management

python manage.py collectstatic --no-input

python manage.py migrate
