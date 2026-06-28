import os
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from django.conf import settings
from django.http import FileResponse, Http404
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


INLINE_EXTS = {".pdf"}


def browse(request):
    rel_path = request.GET.get("path", "")
    target = resolve_within_root(rel_path)
    if not target.is_dir():
        raise Http404("Not a directory")

    base = materials_root()
    dirs, files = [], []
    with os.scandir(target) as it:
        for entry in it:
            if entry.name.startswith("."):
                continue
            entry_rel = os.path.relpath(entry.path, base).replace(os.sep, "/")
            if entry.is_dir():
                dirs.append({"name": entry.name, "path": entry_rel})
            elif entry.is_file():
                st = entry.stat()
                files.append({
                    "name": entry.name,
                    "path": entry_rel,
                    "size": st.st_size,
                    "mtime": datetime.fromtimestamp(st.st_mtime),
                    "ext": os.path.splitext(entry.name)[1].lower(),
                })
    dirs.sort(key=lambda e: e["name"])
    files.sort(key=lambda e: e["name"])

    crumbs = []
    if rel_path.strip("/"):
        accum = ""
        for part in rel_path.strip("/").split("/"):
            accum = f"{accum}/{part}" if accum else part
            crumbs.append({"name": part, "path": accum})

    return render(request, "app_materials/browse.html", {
        "dirs": dirs,
        "files": files,
        "crumbs": crumbs,
        "current": rel_path.strip("/"),
    })


def serve_file(request):
    rel_path = request.GET.get("path", "")
    target = resolve_within_root(rel_path)
    if not target.is_file():
        raise Http404("Not a file")
    disposition = "inline" if target.suffix.lower() in INLINE_EXTS else "attachment"
    response = FileResponse(open(target, "rb"))
    response["Content-Disposition"] = (
        f"{disposition}; filename*=UTF-8''{quote(target.name)}"
    )
    return response
