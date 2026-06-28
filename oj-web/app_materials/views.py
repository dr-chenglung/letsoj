import os
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import markdown as markdown_lib
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


# 伺服器端轉成 HTML 再渲染的格式
MARKDOWN_EXTS = {".md", ".markdown"}

# 只顯示/送出這些教材相關格式（白名單），其餘（.ini、.exe、暫存檔等）一律過濾
ALLOWED_DISPLAY_EXTS = {
    ".pdf",
    ".doc", ".docx",
    ".ppt", ".pptx",
    ".xls", ".xlsx",
    ".txt", ".csv", ".rtf", ".odt", ".ods", ".odp",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp",
    ".html", ".htm",
    *MARKDOWN_EXTS,
}

# 在瀏覽器內開啟（新分頁）的格式；其餘白名單格式則下載
INLINE_EXTS = {
    ".pdf",
    ".txt", ".csv",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp",
    ".html", ".htm",
    *MARKDOWN_EXTS,
}


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
                ext = os.path.splitext(entry.name)[1].lower()
                if ext not in ALLOWED_DISPLAY_EXTS:
                    continue
                st = entry.stat()
                files.append({
                    "name": entry.name,
                    "path": entry_rel,
                    "size": st.st_size,
                    "mtime": datetime.fromtimestamp(st.st_mtime),
                    "ext": ext,
                    "inline": ext in INLINE_EXTS,
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


def serve_file(request, rel_path):
    target = resolve_within_root(rel_path)
    if not target.is_file():
        raise Http404("Not a file")
    ext = target.suffix.lower()
    if ext not in ALLOWED_DISPLAY_EXTS:
        raise Http404("File type not allowed")

    if ext in MARKDOWN_EXTS:
        # 伺服器端把 Markdown 轉成 HTML 再套版型顯示
        content_html = markdown_lib.markdown(
            target.read_text(encoding="utf-8"),
            extensions=["fenced_code", "tables"],
        )
        return render(request, "app_materials/markdown.html", {
            "title": target.name,
            "content_html": content_html,
        })

    # .html/.htm 由 FileResponse 依副檔名自帶 text/html，inline 時瀏覽器會渲染
    disposition = "inline" if ext in INLINE_EXTS else "attachment"
    response = FileResponse(open(target, "rb"))
    response["Content-Disposition"] = (
        f"{disposition}; filename*=UTF-8''{quote(target.name)}"
    )
    return response
