# Panel için yerel sunucu (python -m http.server yerine). start_dashboard.bat çalıştırır.
#
# İzin listesi mantığı: sadece şunlar sunulur, geri kalan HER ŞEY 403:
#   /dashboard.html, /status.json, /dashboard_data/<dosya>, proje içindeki *.mp4
#   /api/local.json -> panel için üretilen özet (mp4 listesi, scratch senaryoları);
#                      o dosyaların kendisi sunulmaz, sadece gerekli alanlar
#   /videos/<32 hex>.mp4  -> OneDrive dışındaki yedek klasöründen (video_backup.VIDEO_DIR) tek video; orada yoksa
#                            elle kurtarılanlar klasöründen (video_backup.RECOVERED_DIR, dizin.json notion_id eşleşmesi)
#   /api/tg/<32 hex>.mp4  -> yerel kopya yoksa Telegram File ID ile indirir (ffprobe doğrulamalı), sonra sunar
# Her zaman 403: nokta ile başlayan her yol parçası (.env, .git, .venv...), .py dosyaları,
# proje dışına çıkan yollar (../, mutlak yol, symlink), klasör listeleri.
#
#   python scripts/dashboard_server.py            -> http://127.0.0.1:8771/dashboard.html
#   python scripts/dashboard_server.py --port 9000
import argparse
import email.utils
import importlib.util
import json
import mimetypes
import os
import posixpath
import re
import sys
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST, PORT = "127.0.0.1", 8771
ALLOWED_FILES = {"dashboard.html", "status.json"}
ALLOWED_DIRS = ("dashboard_data",)
MP4_SKIP_DIRS = {"__pycache__", "node_modules"}
CHUNK = 256 * 1024
VIDEO_ROUTE = re.compile(r"^/(videos|api/tg)/([0-9a-f]{32})\.mp4$")

_spec = importlib.util.spec_from_file_location("video_backup", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                            "video_backup.py"))
video_backup = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(video_backup)
_tg_lock = threading.Lock()


def resolve(root: str, url_path: str) -> str | None:
    """URL yolunu proje içindeki gerçek dosya yoluna çevirir; izin yoksa None (-> 403)."""
    path = unquote(url_path)
    if "\\" in path or "\x00" in path or ":" in path:   # Windows ayırıcısı, sürücü harfi, NTFS akışı
        return None
    parts = [p for p in path.split("/") if p]
    if not parts:
        return None
    for p in parts:
        # "..", nokta ile başlayanlar; Windows "main.py." / "main.py " -> main.py açar, onlar da kapalı
        if p.startswith(".") or p.endswith(".") or p.endswith(" "):
            return None
    rel = "/".join(parts)
    low = rel.lower()                       # Windows büyük/küçük harf ayırmaz: .PY, .ENV
    if low.endswith((".py", ".pyc", ".pyw")):
        return None
    ok = (low in ALLOWED_FILES
          or (len(parts) > 1 and parts[0].lower() in ALLOWED_DIRS)
          or low.endswith(".mp4"))
    if not ok:
        return None
    full = os.path.realpath(os.path.join(root, *parts))
    real_root = os.path.realpath(root)
    if os.path.commonpath([full, real_root]) != real_root:   # symlink ile dışarı kaçış
        return None
    return full


def local_summary(root: str) -> dict:
    """Panelin 'Lokal video dosyaları' kartı için özet. Dosya içerikleri sunulmaz."""
    videos = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in MP4_SKIP_DIRS]
        for f in filenames:
            if f.lower().endswith(".mp4") and not f.startswith("."):
                full = os.path.join(dirpath, f)
                st = os.stat(full)
                rel = os.path.relpath(full, root).replace(os.sep, "/")
                videos.append({"path": rel, "size": st.st_size, "modified": st.st_mtime})
    # scratch/kie_*_result.json: dosya adı -> senaryo (sadece gösterilen alanlar)
    scenarios = {}
    scratch = os.path.join(root, "scratch")
    if os.path.isdir(scratch):
        for f in os.listdir(scratch):
            if f.startswith("kie_") and f.endswith("result.json"):
                try:
                    data = json.load(open(os.path.join(scratch, f), encoding="utf-8"))
                except Exception:
                    continue
                for v in data.get("videos", []):
                    name = str(v.get("file", "")).replace("\\", "/").split("/")[-1]
                    if name:
                        scenarios[name] = {k: v.get(k) for k in ("domain", "camera", "seconds", "story", "final_prompt")}
    for v in videos:
        v["info"] = scenarios.get(v["path"].split("/")[-1])
    videos.sort(key=lambda v: v["modified"], reverse=True)
    return {"videos": videos}


class Handler(BaseHTTPRequestHandler):
    root = ROOT
    video_dir = video_backup.VIDEO_DIR
    recovered_dir = video_backup.RECOVERED_DIR
    quiet = False
    server_version = "DeepMysterPanel"

    def log_message(self, fmt, *args):   # sadece reddedilen istekleri yaz, gerisi gürültü
        if not self.quiet and len(args) > 1 and str(args[1]) == "403":
            sys.stderr.write(f"403 {self.path}\n")

    def do_HEAD(self):
        self._serve(head=True)

    def do_GET(self):
        self._serve(head=False)

    def _plain(self, code: int, text: str, head: bool):
        body = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head:
            self.wfile.write(body)

    def _serve(self, head: bool):
        path = urlsplit(self.path).path
        if path == "/":
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", "/dashboard.html")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if path == "/api/local.json":
            body = json.dumps(local_summary(self.root), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if not head:
                self.wfile.write(body)
            return
        m = VIDEO_ROUTE.match(path)
        if m:
            return self._serve_backup(m.group(1), m.group(2), head)
        full = resolve(self.root, path)
        if full is None:
            return self._plain(403, "403 Yasak", head)
        if not os.path.isfile(full):
            return self._plain(404, "404 Bulunamadı", head)
        self._send_file(full, head)

    def _serve_backup(self, route: str, key: str, head: bool):
        """Yedek klasöründen video. /api/tg: yerel kopya yoksa önce Telegram'dan indirir (Notion'a yazmaz)."""
        full = video_backup.local_copy(key, self.video_dir, self.recovered_dir)
        if not full and route == "api/tg":
            run = self._find_run(key)
            if not run or not run.get("telegram_file_id"):
                return self._plain(404, "404 Telegram File ID yok", head)
            state_file = os.path.join(self.root, "dashboard_data", "video_backup.json")
            full = video_backup.video_path(key, self.video_dir)
            with _tg_lock:   # aynı anda iki kart aynı videoyu istemesin
                if not os.path.isfile(full):
                    state = video_backup.load_state(state_file)
                    entry = video_backup.backup_one({**run, "video_url": ""}, state, video_backup.bot_token(),
                                                    self.video_dir)
                    video_backup.save_state(state, state_file, self.video_dir)
                    if entry.get("status") != "ok":
                        return self._plain(502, "Telegram'dan indirilemedi: " + entry.get("error", ""), head)
        if not full or not os.path.isfile(full):
            return self._plain(404, "404 Yerel kopya yok", head)
        self._send_file(full, head)

    def _find_run(self, key: str) -> dict | None:
        try:
            with open(os.path.join(self.root, "dashboard_data", "notion_runs.json"), encoding="utf-8") as f:
                runs = json.load(f).get("runs", [])
        except (OSError, ValueError):
            return None
        return next((r for r in runs if video_backup.record_key(r.get("id", "")) == key), None)

    def _send_file(self, full: str, head: bool):
        size = os.path.getsize(full)
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype == "application/json":
            ctype += "; charset=utf-8"
        start, end, code = 0, size - 1, 200
        rng = self.headers.get("Range", "")
        if rng.startswith("bytes=") and "," not in rng and size:   # video ileri sarma için tek aralık
            a, _, b = rng[6:].partition("-")
            try:
                if a:
                    start, end = int(a), min(int(b), size - 1) if b else size - 1
                else:
                    start, end = max(0, size - int(b)), size - 1
            except ValueError:
                start, end = 0, size - 1
            if start > end or start >= size:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            code = 206
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Last-Modified", email.utils.formatdate(os.path.getmtime(full), usegmt=True))
        self.send_header("Cache-Control", "no-store")
        if code == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if head:
            return
        try:
            with open(full, "rb") as f:
                f.seek(start)
                left = end - start + 1
                while left > 0:
                    chunk = f.read(min(CHUNK, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass   # tarayıcı videoyu ileri sarınca bağlantıyı keser, normal


def make_server(root: str = ROOT, host: str = HOST, port: int = PORT, quiet: bool = False,
                video_dir: str | None = None, recovered_dir: str | None = None) -> ThreadingHTTPServer:
    handler = type("BoundHandler", (Handler,), {"root": root, "quiet": quiet,
                                                "video_dir": video_dir or video_backup.VIDEO_DIR,
                                                "recovered_dir": recovered_dir or video_backup.RECOVERED_DIR})
    return ThreadingHTTPServer((host, port), handler)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=PORT)
    args = ap.parse_args()
    try:
        srv = make_server(port=args.port)
    except OSError as e:   # 12 Eki: port doluyken pencere sessizce kapanıyordu
        print(f"❌ Panel sunucusu açılamadı (port {args.port}): {e}\n"
              f"   Başka bir panel penceresi zaten açık olabilir. Onu kapatıp start_dashboard.bat'ı yeniden çalıştır.")
        sys.exit(1)
    print(f"Panel: http://{HOST}:{args.port}/dashboard.html  (sadece bu bilgisayar, Ctrl+C ile kapanır)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
