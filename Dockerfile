FROM python:3.12-slim


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


WORKDIR /app


RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt


COPY . .


WORKDIR /app/reto-cuc-main/asset_management


RUN python manage.py collectstatic --noinput


EXPOSE 8000


CMD ["gunicorn", "--bind", "0.0.0.0:8000", "asset_management.wsgi:application"]
