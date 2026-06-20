#!/bin/bash

# 注意:makemigrations 不在這裡執行。
# migration 檔應在開發時於本機產生並 commit 進版控,
# 不該在容器啟動時動態生成,否則各環境 schema 可能不一致。

# Apply database migrations (冪等,每次啟動執行沒問題)
echo "Apply database migrations"
python manage.py migrate

# 初始化 sys-options:只在資料庫為空(首次啟動)時載入。
# fixture 使用固定 pk,若每次啟動都 loaddata,會把 admin 後台改過的設定還原成預設值。
if python manage.py shell -c "import sys; from app_management.models import MySysOptions; sys.exit(0 if MySysOptions.objects.exists() else 1)"; then
    echo "Sys-options already exist, skip loaddata"
else
    echo "Initialize sys-options (first run)"
    python manage.py loaddata app_management/my-initial-sys-options.json
fi

# Collect static files
# 不加 --clear:避免每次重啟先刪光再重收(拖慢啟動、多容器共用 volume 時易有競態)。
# 此步驟留在 runtime 而非 Dockerfile build 階段,因為 staticfiles 是與 nginx 共用的 named volume,
# 只有 runtime 掛載後重收,nginx 才能拿到最新 static。
echo "Collect static files......"
python manage.py collectstatic --no-input
chmod -R 775 /app/staticfiles

# Create superuser(已存在時 createsuperuser 會回非零,用 || 吸收避免噴錯中斷)
# Django's createsuperuser script takes the password from DJANGO_SUPERUSER_PASSWORD by default.
if [ "$DJANGO_SUPERUSER_USERNAME" ]
then
    echo "Create superuser (skip if already exists)"
    python manage.py createsuperuser \
        --noinput \
        --username $DJANGO_SUPERUSER_USERNAME \
        --email $DJANGO_SUPERUSER_EMAIL \
        || echo "Superuser already exists, skip"
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
