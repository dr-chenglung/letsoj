from django.urls import path
from . import views

urlpatterns = [
    path("", views.browse, name="materials_browse"),
    # 檔名放在網址路徑最後一段，讓瀏覽器分頁標題顯示檔名而非 "file"
    path("file/<path:rel_path>", views.serve_file, name="materials_file"),
]
