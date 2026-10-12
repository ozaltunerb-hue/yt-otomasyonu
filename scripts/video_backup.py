# Panel videolarının kalıcı yerel yedeği (12 Eki 2026). Notion'a YAZMAZ, hiçbir videoyu silmez.
#
# Neden: panel videoyu Kie'nin geçici linkinden oynatıyordu, link ~15 günde ölüyor (12 Eki ölçümü). Railway'de
# kalıcı disk yok. Kalıcı kopya Telegram'da (Notion "Telegram File ID", 29 Eyl'den beri).
# Bu betik her kaydın videosunu OneDrive DIŞINDAKİ klasöre indirir: C:\DeepMyster_videolar\<kayıt id>.mp4
# Kaynak sırası: Telegram File ID -> Kie linki. Her indirme ffprobe ile doğrulanır (video akışı, süre >= 4 sn,
# indirilen boyut = beklenen boyut); bozuk dosya kopya sayılmaz, tekrar denenir.
# Sonuç dashboard_data/video_backup.json'a yazılır, panel kaynak rozetini oradan çizer.
# Ayrıca elle kurtarılan videolar (C:\DeepMyster_videolar_kurtarilan, dizin.json'da notion_id eşleşmesi) yerel kopya
# sayılır; o klasöre sadece okunur, yazılmaz.
#
#   python scripts/video_backup.py            -> eksik videoları indir, özet yaz
#   (dashboard_sync.py her Notion çekiminden sonra bunu otomatik çağırır)
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.abspath(os.path.join(ROOT, "..", ".."))
ENV_FILES = [os.path.join(REPO_ROOT, "_knowledge", "credentials", "master.env"), os.path.join(ROOT, ".env")]
RUNS_FILE = os.path.join(ROOT, "dashboard_data", "notion_runs.json")
STATE_FILE = os.path.join(ROOT, "dashboard_data", "video_backup.json")
VIDEO_DIR = os.environ.get("DEEPMYSTER_VIDEO_DIR", r"C:\DeepMyster_videolar")
RECOVERED_DIR = os.environ.get("DEEPMYSTER_RECOVERED_DIR", r"C:\DeepMyster_videolar_kurtarilan")

TG_LIMIT = 20 * 1024 * 1024        # Telegram Bot API getFile indirme sınırı
TG_LIMIT_MSG = "indirilemedi (20 MB sınırı)"
MIN_SECONDS = 4.0
MIN_BYTES = 100 * 1024
ATTEMPTS = 3
ID_RE = re.compile(r"^[0-9a-f]{32}$")


def read_env(path: str) -> dict:
    out = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8", errors="ignore"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip("\"'")
    return out


def bot_token() -> str:
    env = {}
    for path in ENV_FILES:
        env.update(read_env(path))
    return env.get("TELEGRAM_BOT_TOKEN", "")


def record_key(record_id: str) -> str:
    """Notion sayfa id'si -> dosya adı (tiresiz 32 hex). Geçersizse ''."""
    key = (record_id or "").replace("-", "").lower()
    return key if ID_RE.match(key) else ""


def video_path(key: str, video_dir: str = VIDEO_DIR) -> str:
    return os.path.join(video_dir, f"{key}.mp4")


def recovered_index(recovered_dir: str = RECOVERED_DIR) -> dict:
    """Kurtarılanlar klasörünün dizin.json'u -> {kayıt anahtarı: dosya yolu} (sadece var olan dosyalar)."""
    try:
        with open(os.path.join(recovered_dir, "dizin.json"), encoding="utf-8") as f:
            rows = json.load(f)
    except (OSError, ValueError):
        return {}
    out = {}
    for row in rows if isinstance(rows, list) else []:
        key = record_key(str(row.get("notion_id", "")))
        name = os.path.basename(str(row.get("file", "")))
        path = os.path.join(recovered_dir, name)
        if key and name.lower().endswith(".mp4") and os.path.isfile(path):
            out.setdefault(key, path)
    return out


def local_copy(key: str, video_dir: str = VIDEO_DIR, recovered_dir: str = RECOVERED_DIR) -> str:
    """Kaydın yerel kopyası: önce yedek klasörü, sonra kurtarılanlar. Yoksa ''."""
    if not record_key(key):
        return ""
    path = video_path(key, video_dir)
    if os.path.isfile(path):
        return path
    return recovered_index(recovered_dir).get(key, "")


class BackupError(Exception):
    pass


class TooBigError(BackupError):
    pass


class GoneError(BackupError):
    """Link kalıcı olarak ölü (404/410): tekrar denemenin anlamı yok."""


def probe(path: str, expected_size: int | None = None) -> dict:
    """ffprobe ile doğrular; geçerliyse {"seconds", "size"}, değilse BackupError."""
    size = os.path.getsize(path) if os.path.exists(path) else 0
    if size < MIN_BYTES:
        raise BackupError(f"dosya çok küçük ({size} bayt)")
    if expected_size and size != expected_size:
        raise BackupError(f"eksik indirme ({size}/{expected_size} bayt)")
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
                              "-of", "json", path], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as e:
        raise BackupError(f"ffprobe çalışmadı: {e}")
    if out.returncode != 0:
        raise BackupError(f"ffprobe okuyamadı: {(out.stderr or '').strip()[:150]}")
    try:
        info = json.loads(out.stdout or "{}")
        seconds = float((info.get("format") or {}).get("duration") or 0)
    except (ValueError, TypeError):
        raise BackupError("ffprobe çıktısı anlaşılamadı")
    if not any(s.get("codec_type") == "video" for s in info.get("streams", [])):
        raise BackupError("video akışı yok")
    if seconds < MIN_SECONDS:
        raise BackupError(f"süre çok kısa ({seconds:.1f} sn)")
    return {"seconds": round(seconds, 2), "size": size}


def _download(url: str, dst: str, expected_size: int | None = None, session=requests) -> int | None:
    """URL'yi dst'ye akıtır; beklenen boyutu döndürür (Content-Length ya da verilen)."""
    with session.get(url, stream=True, timeout=60) as r:
        if r.status_code in (404, 410):
            raise GoneError(f"HTTP {r.status_code} (link ölü)")
        if r.status_code != 200:
            raise BackupError(f"HTTP {r.status_code}")
        length = r.headers.get("Content-Length")
        with open(dst, "wb") as f:
            for chunk in r.iter_content(256 * 1024):
                if chunk:
                    f.write(chunk)
    return expected_size or (int(length) if length and length.isdigit() else None)


def telegram_url(file_id: str, token: str, session=requests) -> tuple[str, int | None]:
    """getFile -> (indirme URL'si, boyut). 20 MB üstü TooBigError."""
    if not token:
        raise BackupError("TELEGRAM_BOT_TOKEN yok")
    r = session.get(f"https://api.telegram.org/bot{token}/getFile", params={"file_id": file_id}, timeout=30)
    try:
        j = r.json()
    except ValueError:
        raise BackupError(f"Telegram HTTP {r.status_code}")
    if not j.get("ok"):
        desc = str(j.get("description", ""))
        if "too big" in desc.lower():
            raise TooBigError(TG_LIMIT_MSG)
        raise BackupError(f"Telegram: {desc[:120]}")
    res = j.get("result") or {}
    size = res.get("file_size")
    if size and size > TG_LIMIT:
        raise TooBigError(TG_LIMIT_MSG)
    if not res.get("file_path"):
        raise BackupError("Telegram file_path vermedi")
    return f"https://api.telegram.org/file/bot{token}/{res['file_path']}", size


def fetch_valid(get_url, dst: str, attempts: int = ATTEMPTS, session=requests, pause: float = 2.0) -> dict:
    """get_url() -> (url, beklenen boyut). İndir + doğrula; bozuksa tekrar dene. Geçici .part dosyası
    sadece bu betiğin yarım indirmesidir; başarıda hedefe taşınır, sonunda kalırsa kaldırılır."""
    part = dst + ".part"
    last = "bilinmeyen hata"
    try:
        for i in range(attempts):
            try:
                url, size = get_url()
                expected = _download(url, part, size, session=session)
                info = probe(part, expected)
                os.replace(part, dst)
                return info
            except (TooBigError, GoneError):
                raise
            except (BackupError, requests.RequestException, OSError) as e:
                last = str(e)[:200]
                if i + 1 < attempts:
                    time.sleep(pause)
        raise BackupError(f"{attempts} denemede geçerli dosya inmedi: {last}")
    finally:
        if os.path.exists(part):
            os.remove(part)


def backup_one(run: dict, state: dict, token: str, video_dir: str = VIDEO_DIR, session=requests,
               pause: float = 2.0, recovered: dict | None = None) -> dict:
    """Tek kayıt. Geçerli yerel kopya varsa dokunmaz (üzerine yazmaz). Sonuç state'e yazılır ve döner."""
    key = record_key(run.get("id", ""))
    if not key:
        return {}
    dst = video_path(key, video_dir)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    prev = state.get(key) or {}
    if os.path.exists(dst):
        if prev.get("status") == "ok" and prev.get("size") == os.path.getsize(dst):
            return prev
        try:   # klasörde var ama durumda yok / değişmiş: yeniden doğrula, dosyayı asla silme/ezme
            info = probe(dst)
            entry = {**prev, "status": "ok", "source": prev.get("source") or "yerel", "path": dst, **info,
                     "error": "", "checked_at": now}
        except BackupError as e:
            entry = {**prev, "status": "bozuk_yerel", "path": dst, "error": f"yerel dosya bozuk: {e}",
                     "checked_at": now}
        state[key] = entry
        return entry

    rec_path = (recovered or {}).get(key, "")
    if rec_path and os.path.isfile(rec_path):   # elle kurtarılan kopya: indirme yok, sadece doğrula
        if prev.get("status") == "ok" and prev.get("path") == rec_path and prev.get("size") == os.path.getsize(rec_path):
            return prev
        try:
            entry = {"status": "ok", "source": "kurtarilan", "path": rec_path, **probe(rec_path), "error": "",
                     "checked_at": now}
        except BackupError as e:
            entry = {**prev, "status": "bozuk_yerel", "path": rec_path, "error": f"kurtarılan dosya bozuk: {e}",
                     "checked_at": now}
        state[key] = entry
        return entry

    tg_id, kie = run.get("telegram_file_id") or "", run.get("video_url") or ""
    if not (tg_id or kie):
        return {}
    os.makedirs(video_dir, exist_ok=True)
    errors = []
    sources = []
    if tg_id:
        sources.append(("telegram", lambda: telegram_url(tg_id, token, session=session)))
    if kie:
        sources.append(("kie", lambda: (kie, None)))
    tg_too_big = False
    gone = []
    for name, get_url in sources:
        try:
            info = fetch_valid(get_url, dst, session=session, pause=pause)
            entry = {"status": "ok", "source": name, "path": dst, **info,
                     "error": TG_LIMIT_MSG if tg_too_big else "", "downloaded_at": now, "checked_at": now}
            state[key] = entry
            return entry
        except TooBigError as e:
            tg_too_big = True
            errors.append(f"telegram: {e}")
        except GoneError as e:
            gone.append(name)
            errors.append(f"{name}: {e}")
        except BackupError as e:
            errors.append(f"{name}: {e}")
    entry = {"status": "failed", "source": "", "error": "; ".join(errors), "too_big": tg_too_big,
             "permanent": len(gone) == len(sources), "checked_at": now, "attempted_at": now}
    state[key] = entry
    return entry


def load_state(path: str = STATE_FILE) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f).get("videos", {})
    except (OSError, ValueError):
        return {}


def _replace(tmp: str, path: str, tries: int = 5) -> None:
    """os.replace; dosya OneDrive içinde, eşitleme anında kısa süre kilitlenebilir -> birkaç kez dene."""
    for i in range(tries):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if i + 1 == tries:
                raise
            time.sleep(0.5 * (i + 1))


def save_state(state: dict, path: str = STATE_FILE, video_dir: str = VIDEO_DIR,
               recovered_dir: str = RECOVERED_DIR) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "video_dir": video_dir,
                   "recovered_dir": recovered_dir, "videos": state}, f, ensure_ascii=False, indent=1)
    _replace(tmp, path)


def write_index(runs: list[dict], state: dict, video_dir: str = VIDEO_DIR) -> None:
    """Klasöre okunur dizin: hangi dosya hangi video (tarih, başlık). Sadece bilgi amaçlı."""
    rows = []
    for r in runs:
        key = record_key(r.get("id", ""))
        st = state.get(key) or {}
        if st.get("status") == "ok" and os.path.dirname(st.get("path", "")) == os.path.normpath(video_dir):
            rows.append({"file": f"{key}.mp4", "date": r.get("date", ""), "title": r.get("title", ""),
                         "source": st.get("source", ""), "notion_url": r.get("notion_url", "")})
    if not rows:
        return
    tmp = os.path.join(video_dir, "dizin.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    _replace(tmp, os.path.join(video_dir, "dizin.json"))


def retry_due(entry: dict) -> bool:
    """Başarısız kayıt her senkronda değil, 6 saatte bir yeniden denenir. Bütün kaynakları kalıcı ölü (404) olan
    kayıt hiç yeniden denenmez (--force hariç)."""
    if (entry or {}).get("status") != "failed":
        return True
    if entry.get("permanent"):
        return False
    try:
        last = datetime.fromisoformat(entry.get("attempted_at", ""))
    except ValueError:
        return True
    return (datetime.now(timezone.utc) - last).total_seconds() > 6 * 3600


def backup_all(runs: list[dict], video_dir: str = VIDEO_DIR, state_file: str = STATE_FILE,
               token: str | None = None, force: bool = False, log=print,
               recovered_dir: str = RECOVERED_DIR) -> dict:
    token = bot_token() if token is None else token
    state = load_state(state_file)
    before = json.dumps(state, sort_keys=True)
    recovered = recovered_index(recovered_dir)
    summary = {"ok": 0, "new": [], "failed": [], "too_big": []}
    for r in sorted(runs, key=lambda x: x.get("date") or ""):   # en eski önce: ölmesi en yakın link
        key = record_key(r.get("id", ""))
        if not key or not (r.get("telegram_file_id") or r.get("video_url") or key in state or key in recovered):
            continue
        prev_status = (state.get(key) or {}).get("status")
        if (not force and key not in recovered and not retry_due(state.get(key))
                and not os.path.exists(video_path(key, video_dir))):
            summary["failed"].append((r, state[key]))
            continue
        entry_before = json.dumps(state.get(key), sort_keys=True)
        entry = backup_one(r, state, token, video_dir, recovered=recovered)
        if not entry:
            continue
        if entry.get("status") == "ok":
            summary["ok"] += 1
            if prev_status != "ok":
                summary["new"].append((r, entry))
                log(f"💾 {r.get('date', '')[:16]} {entry['source']}: {r.get('title', '')[:50]}")
        else:
            summary["failed"].append((r, entry))
            log(f"❌ {r.get('date', '')[:16]} {r.get('title', '')[:50]}: {entry.get('error', '')[:150]}")
        if entry.get("too_big") or entry.get("error") == TG_LIMIT_MSG:
            summary["too_big"].append((r, entry))
        if json.dumps(state.get(key), sort_keys=True) != entry_before:
            save_state(state, state_file, video_dir, recovered_dir)   # yarıda kesilirse ilerleme kalsın
    if json.dumps(state, sort_keys=True) != before or not os.path.exists(state_file):
        save_state(state, state_file, video_dir, recovered_dir)   # değişiklik yoksa yazma (OneDrive kilidi)
    try:
        write_index(runs, state, video_dir)
    except OSError:
        pass
    return summary


def main() -> int:
    try:
        runs = json.load(open(RUNS_FILE, encoding="utf-8")).get("runs", [])
    except (OSError, ValueError) as e:
        print(f"❌ {RUNS_FILE} okunamadı: {e}. Önce python scripts/dashboard_sync.py")
        return 1
    s = backup_all(runs, force="--force" in sys.argv)
    print(f"✅ Yerel kopya: {s['ok']} (bu tur yeni: {len(s['new'])}) · başarısız: {len(s['failed'])} · "
          f"20 MB sınırı: {len(s['too_big'])} · klasör: {VIDEO_DIR}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
