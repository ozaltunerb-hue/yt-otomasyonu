"""
Kalıcı video arşivi (TUR 29): her üretim arsiv/<tarih>_<domain>_<task8>/ klasörüne video.mp4 + meta.json.

Kie linkleri ~2 haftada ölüyor; başarılı örneklerin prompt'unu bulmak bu yüzden zordu. meta.json task ID
Kie'ye gönderilmeden sonra ama polling başlamadan önce yazılır (restart'ta kurtarma için), video indirilince
tamamlanır. Railway diski geçicidir: orada kalıcı kopya Telegram file_id'dir (Notion "Telegram File ID").
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from datetime import datetime, timezone

from config import settings

log = logging.getLogger("Archive")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def current_commit() -> str:
    """Çalışan kodun commit'i (stil eki sürümü). Railway GitHub deploy'unda RAILWAY_GIT_COMMIT_SHA; yoksa yerel
    git; ikisi de yoksa 'doğrulanamadı'."""
    sha = os.environ.get("RAILWAY_GIT_COMMIT_SHA", "").strip()
    if sha:
        return sha[:7]
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=_ROOT, capture_output=True, text=True,
                             timeout=5)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return "doğrulanamadı"


def new_archive_dir(domain: str, task_id: str, root: str | None = None) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    path = os.path.join(root or settings.ARCHIVE_DIR, f"{stamp}_{domain or 'bilinmiyor'}_{(task_id or 'notask')[:8]}")
    os.makedirs(path, exist_ok=True)
    return path


def meta_path(archive_dir: str) -> str:
    return os.path.join(archive_dir, "meta.json")


def write_meta(archive_dir: str, meta: dict) -> str:
    """meta.json'u atomik yazar (yarım dosya kalmasın)."""
    path = meta_path(archive_dir)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2, default=str)
    os.replace(tmp, path)
    return path


def update_meta(archive_dir: str, **fields) -> dict:
    """meta.json'a alan ekler/günceller (dosya yoksa oluşturur)."""
    path = meta_path(archive_dir)
    meta = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            meta = json.load(f)
    meta.update(fields)
    write_meta(archive_dir, meta)
    return meta


def save_video(archive_dir: str, src_path: str) -> str:
    """Geçici videoyu arşive kopyalar; arşiv yolunu döndürür. Geçici dosyayı çağıran siler."""
    dst = os.path.join(archive_dir, "video.mp4")
    shutil.copy(src_path, dst)
    log.info(f"💾 Video arşive kaydedildi: {dst}")
    return dst
