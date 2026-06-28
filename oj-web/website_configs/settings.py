from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
# 預設 false，正式環境務必維持關閉；開發時在 .env 設 DJANGO_DEBUG=true
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"

# 容忍逗號前後的空白，並濾掉空項目，避免 .env 排版造成 DisallowedHost
ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

# 是否啟用 HTTPS 相關安全設定。
# 正式機（HTTPS 由上游/外部代理處理）設 true；臨時的純 HTTP 伺服器設 false。
# 預設 false，確保在沒有 HTTPS 的環境程式仍可正常運作。
USE_HTTPS = os.environ.get("USE_HTTPS", "false").lower() == "true"

if USE_HTTPS:
    # 上游代理解密後，靠這個 header 讓 Django 知道原始請求是 HTTPS
    # （需搭配 nginx 轉發 X-Forwarded-Proto，見 nginx/nginx.conf）
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # 把 HTTP 轉到 HTTPS（HTTP-only 環境若開啟會無限轉址，所以放在開關內）
    SECURE_SSL_REDIRECT = True
    # cookie 只在 HTTPS 送出（HTTP-only 環境若開啟會導致登入失敗）
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # HSTS：要求瀏覽器之後只走 HTTPS
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# 依 USE_HTTPS 自動帶入正確 scheme，從 ALLOWED_HOSTS 推導，免得另外維護一份清單。
# Django 4.0+ 對跨來源 POST 需要這份名單含 scheme，否則可能出現 403 CSRF。
CSRF_TRUSTED_ORIGINS = [
    f"{'https' if USE_HTTPS else 'http'}://{host}" for host in ALLOWED_HOSTS
]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "import_export",
    # Restful API
    "rest_framework",
    "app_oj.apps.AppOjConfig",
    "app_management.apps.AppManagementConfig",
    "app_account.apps.AppLoginConfig",
    "app_materials.apps.AppMaterialsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "website_configs.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "website_configs.wsgi.application"

# the environ variables are defined in the oj-web yaml 用容器資料庫
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        #'HOST': 'oj-postgres', # defined in docker-compose.yaml, 資料庫容器名稱
        "HOST": os.environ.get("OJDB_HOST"),
        "PORT": os.environ.get(
            "OJDB_PORT"
        ),  # 5432, #default port you don't need to mention in docker-compose
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

# Time zone
TIME_ZONE = os.getenv("TZ", "UTC")
USE_TZ = True

# Internationalization
USE_I18N = True
USE_L10N = True

# Static files (CSS, JavaScript, Images)
# 網頁端會用到{%  load static %}
STATIC_URL = "/static/"

# 靜態檔案的搜尋路徑 搜尋根目錄static，也會搜尋各app底下的 static卷夾
# 若有新的檔案，需要重新製作新的容器，才會再去更新python manage.py collectstaticfiles
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
    # BASE_DIR / 'static', # 這種寫法也可以
]

# STATIC_ROOT只有在部署網站時才會需要用到
# Production階段用到的設定，Nginx的靜態路徑需與此路徑配合
STATIC_ROOT = BASE_DIR / "staticfiles"
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# 自訂使用者
#AUTH_USER_MODEL = "app_oj.User"
AUTH_USER_MODEL = "app_account.User"

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(asctime)s - %(levelname)s - %(module)s - %(message)s"},
    },
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "./django-logfile.log",
            "formatter": "simple",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "root": {  # means "root logger"
            "handlers": ["file", "console"],  # use the above "console" handler
            "level": "DEBUG",  # logging level
        },
        "logger": {
            "handlers": ["file", "console"],
            "level": "DEBUG",
        },
    },
}

# 'filename': './logsfiles/debug.log'

# 瀏覽器cookie生存時間與瀏覽器關閉session不失效
# Default session settings
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 1209600  # 2 weeks

# 課堂教材根目錄（老師手動放檔，不進版控）。詳見 app_materials。
COURSE_MATERIALS_ROOT = BASE_DIR / "course_materials"
