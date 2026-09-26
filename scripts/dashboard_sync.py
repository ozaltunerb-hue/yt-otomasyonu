# Dashboard için Notion video geçmişini lokale çeker (sadece OKUR, Notion'a yazmaz).
#
# Neden: üretim Railway'de (Telegram /uret) çalışıyor; ürettiği video/yükleme/hata kayıtları proje klasörüne
# düşmüyor, Notion'a düşüyor. Bu betik onları dashboard_data/notion_runs.json'a yazar,
# dashboard.html oradan okur. start_dashboard.bat açılışta ve 10 dakikada bir çalıştırır.
#
#   python scripts/dashboard_sync.py          -> tek sefer
#   python scripts/dashboard_sync.py --loop   -> 10 dk'da bir (Ctrl+C ile durur)
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.abspath(os.path.join(ROOT, "..", ".."))
OUT = os.path.join(ROOT, "dashboard_data", "notion_runs.json")
ENV_FILES = [os.path.join(REPO_ROOT, "_knowledge", "credentials", "master.env"), os.path.join(ROOT, ".env")]
LOOP_SECONDS = 600


def read_env(path: str) -> dict:
    out = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8", errors="ignore"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip("\"'")
    return out


def _text(prop: dict) -> str:
    items = prop.get("title") or prop.get("rich_text") or []
    return "".join(x.get("plain_text", "") for x in items)


def simplify(page: dict) -> dict:
    p = page.get("properties", {})
    sel = lambda k: ((p.get(k) or {}).get("select") or {}).get("name", "")
    date = ((p.get("Tarih") or {}).get("date") or {}).get("start") or page.get("created_time", "")
    return {
        "id": page.get("id", ""),
        "notion_url": page.get("url", ""),
        "title": _text(p.get("Video Adı", {})),
        "status": sel("Durum"),
        "trigger": sel("Tetikleyici"),
        "model": sel("Model"),
        "date": date,
        "topic": _text(p.get("Konu", {})),
        "prompt": _text(p.get("Prompt", {})),
        "combo_key": _text(p.get("Combo Key", {})),
        "motion": _text(p.get("Hareket", {})),
        "error": _text(p.get("Hata", {})),
        "youtube_url": (p.get("YouTube URL") or {}).get("url") or "",
        "video_url": (p.get("Video URL") or {}).get("url") or "",
        "seconds": (p.get("Süre (sn)") or {}).get("number"),
    }


def fetch_all(token: str, db_id: str) -> list[dict]:
    headers = {"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
    rows, cursor = [], None
    while True:
        body = {"page_size": 100, "sorts": [{"property": "Tarih", "direction": "descending"}]}
        if cursor:
            body["start_cursor"] = cursor
        r = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query", headers=headers, json=body, timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"Notion {r.status_code}: {r.text[:200]}")
        j = r.json()
        rows += [simplify(pg) for pg in j.get("results", [])]
        if not j.get("has_more"):
            return rows
        cursor = j.get("next_cursor")


def write(payload: dict) -> None:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    os.replace(tmp, OUT)


def sync_once() -> bool:
    env = {}
    for path in ENV_FILES:
        env.update(read_env(path))
    token = env.get("NOTION_SOCIAL_TOKEN") or env.get("NOTION_API_TOKEN")
    db_id = env.get("NOTION_DB_YOUTUBE_OTOMASYON")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if not (token and db_id):
        print("❌ .env içinde NOTION_SOCIAL_TOKEN / NOTION_DB_YOUTUBE_OTOMASYON yok.")
        return False
    try:
        rows = fetch_all(token, db_id)
    except Exception as e:
        # Eski veriyi silme: son başarılı listeyi koru, sadece hatayı işaretle
        old = {}
        if os.path.exists(OUT):
            try:
                old = json.load(open(OUT, encoding="utf-8"))
            except Exception:
                pass
        write({**old, "sync_error": str(e)[:300], "sync_error_at": now})
        print(f"❌ Notion okunamadı: {e}")
        return False
    write({"synced_at": now, "sync_error": "", "runs": rows})
    print(f"✅ {len(rows)} Notion kaydı -> dashboard_data/notion_runs.json")
    return True


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if "--loop" in sys.argv:
        while True:
            sync_once()
            time.sleep(LOOP_SECONDS)
    sys.exit(0 if sync_once() else 1)
