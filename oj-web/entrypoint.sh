#!/bin/bash

# 下載 CDN 資源到本地（檢查目錄是否存在且非空）
if [ ! -d "/app/static/vendor" ] || [ -z "$(ls -A /app/static/vendor)" ]; then
    echo "=========================================="
    echo "首次啟動或資源遺失：下載 CDN 資源到本地..."
    echo "=========================================="
    bash /app/download-cdn-resources.sh
fi

# Make migrations
echo "Make migrations"
python manage.py makemigrations

# # Apply database migrations
echo "Apply database migrations"
python manage.py migrate

# 每次重啟都會初始化，容器建立之後，也可以移除此步驟
echo "Initialize sys-options"
python manage.py loaddata app_management/my-initial-sys-options.json

# Collect static files
echo "Collect static files......"
python manage.py collectstatic --no-input --clear
chmod -R 775 /app/staticfiles

echo "Create superuser"
# Django's createsuperuser script takes that from DJANGO_SUPERUSER_PASSWORD by default.
if [ "$DJANGO_SUPERUSER_USERNAME" ]
then
    python manage.py createsuperuser \
        --noinput \
        --username $DJANGO_SUPERUSER_USERNAME \
        --email $DJANGO_SUPERUSER_EMAIL
fi

# 啟用gunicorn，透過nginx做proxy，讓外部可以透過nginx的port 80連線
# 若不啟動gunicorn則必須啟動Django development server
if [ "$DEV_SERVER" = "true" ]; then
    echo "Running Django development server..."
    python manage.py runserver 0.0.0.0:8000
else
    echo "Starting Gunicorn..."
    exec gunicorn website_configs.wsgi:application \
        --name agency \
        --bind 0.0.0.0:8000 \
        --reload \
        --workers 10 \
        --worker-class=gthread \
        --threads 8 \
        --max-requests 1000
fi

exec "$@"