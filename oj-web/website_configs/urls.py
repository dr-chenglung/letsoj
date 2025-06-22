from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("", include("app_oj.urls")),
    path("account/", include("app_account.urls")), # for login, register
    path('accounts/', include('django.contrib.auth.urls')), # for logout
    path("manage/", include("app_management.urls")),
    path("admin/", admin.site.urls),
]
