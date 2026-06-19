from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", include("app_oj.urls")),
    path("account/", include("app_account.urls")), # for login, register
    path("accounts/logout/", include("app_account.urls")),  # 為了相容 {% url 'logout' %} 模板標籤
    # path('accounts/', include('django.contrib.auth.urls')), # 已改用自訂的 logout，避免路由衝突
    path("manage/", include("app_management.urls")),
    path("admin/", admin.site.urls),
]

# 在開發環境中，由 Django 提供靜態文件服務
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else None)
