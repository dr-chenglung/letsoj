from django.contrib import admin
from django.contrib import auth
from django.urls import path, include
from django.contrib.auth.decorators import login_required

from . import views

# app_name = "app_account"

urlpatterns = [
    path("user_login/", views.user_login, name="user_login"),
    # path("logout/", auth.view.logout_then_login, name="logout"),
    # path('logout/', auth.views.LogoutView.as_view(), name='logout'),
    path(
        "custom-change-password/",
        login_required(views.custom_change_password),
        name="custom_change_password",
    ),
    path("user_register/", views.user_register, name="user_register"),
]
