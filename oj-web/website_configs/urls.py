from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("", include("app_oj.urls")),
    path("account/", include("app_account.urls")), # for login, register
    path("accounts/logout/", include("app_account.urls")),  # 為了相容 {% url 'logout' %} 模板標籤
    # path('accounts/', include('django.contrib.auth.urls')), # 已改用自訂的 logout，避免路由衝突
    path("manage/", include("app_management.urls")),
    path("admin/", admin.site.urls),
]
