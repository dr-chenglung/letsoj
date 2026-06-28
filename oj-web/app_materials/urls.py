from django.urls import path
from . import views

urlpatterns = [
    path("", views.browse, name="materials_browse"),
    path("file", views.serve_file, name="materials_file"),
]
