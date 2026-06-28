from pathlib import Path
from urllib.parse import quote

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import render


def materials_root() -> Path:
    return Path(settings.COURSE_MATERIALS_ROOT).resolve()


def resolve_within_root(rel_path: str) -> Path:
    """把使用者給的相對路徑安全接到教材根目錄底下；逸出根目錄則 404。"""
    base = materials_root()
    target = (base / rel_path).resolve()
    if not target.is_relative_to(base):
        raise Http404("Not found")
    return target


def browse(request):
    return HttpResponse("")  # 由 Task 3 以 TDD 取代


def serve_file(request):
    return HttpResponse("")  # 由 Task 2 以 TDD 取代
