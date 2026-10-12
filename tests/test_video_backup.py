#!/usr/bin/env python3
"""
scripts/video_backup.py + panel kalıcı kopya testleri (12 Eki 2026).
Kie linki ~15 günde ölür; videolar OneDrive dışına indirilir. Kurallar: ffprobe doğrulaması, bozuk dosya kopya
sayılmaz ve tekrar denenir, 20 MB üstü Telegram dosyası raporlanır, var olan dosya ezilmez/silinmez,
Notion'a yazılmaz. Ağ yok: indirmeler sahte oturumla, klasörler geçici.
"""
import http.client
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import threading
import unittest
from unittest import mock

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(PROJECT_ROOT, "scripts", f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


vb = _load("video_backup")
ds = _load("dashboard_server")
sync = _load("dashboard_sync")

KEY = "3f5d048d625e81aaaaaaaaaaaaaaaaaa"
RUN_ID = f"{KEY[:8]}-{KEY[8:12]}-{KEY[12:16]}-{KEY[16:20]}-{KEY[20:]}"
HAS_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def write(path, data):
    with open(path, "wb") as f:
        f.write(data)


def read(path):
    with open(path, "rb") as f:
        return f.read()


def make_video(path, seconds=5):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc=size=320x240:rate=25:duration={seconds}",
                    "-pix_fmt", "yuv420p", path], check=True, timeout=120)


class FakeResp:
    def __init__(self, status=200, body=b"", payload=None):
        self.status_code, self.body, self.payload = status, body, payload
        self.headers = {"Content-Length": str(len(body))} if body else {}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def iter_content(self, n):
        yield self.body

    def json(self):
        if self.payload is None:
            raise ValueError
        return self.payload


class FakeSession:
    """URL -> sıradaki yanıtlar listesi. Yapılan istekler calls'ta."""
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def get(self, url, **kw):
        self.calls.append(url)
        for prefix, queue in self.routes.items():
            if url.startswith(prefix):
                return queue.pop(0) if len(queue) > 1 else queue[0]
        raise AssertionError(f"beklenmeyen istek: {url}")


class TestHelpers(unittest.TestCase):
    def test_record_key(self):
        self.assertEqual(vb.record_key(RUN_ID), KEY)
        self.assertEqual(vb.record_key("../../x"), "")
        self.assertEqual(vb.record_key(""), "")

    def test_default_dir_outside_onedrive(self):
        self.assertNotIn("onedrive", vb.VIDEO_DIR.lower())

    def test_sync_reads_telegram_file_id(self):
        page = {"id": RUN_ID, "properties": {"Telegram File ID": {"rich_text": [{"plain_text": "BAAC123"}]}}}
        self.assertEqual(sync.simplify(page)["telegram_file_id"], "BAAC123")

    def test_permanent_failure_not_retried(self):
        self.assertFalse(vb.retry_due({"status": "failed", "permanent": True, "attempted_at": "2000-01-01T00:00:00+00:00"}))
        self.assertTrue(vb.retry_due({"status": "failed", "attempted_at": "2000-01-01T00:00:00+00:00"}))


@unittest.skipUnless(HAS_FFMPEG, "ffmpeg yok")
class TestProbeAndDownload(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.good_path = os.path.join(cls.tmp, "good.mp4")
        make_video(cls.good_path)
        cls.good = read(cls.good_path)
        if len(cls.good) < vb.MIN_BYTES:   # testsrc çok küçük çıkarsa alt sınırı testte gevşet
            cls._min = mock.patch.object(vb, "MIN_BYTES", 1000)
            cls._min.start()
        short = os.path.join(cls.tmp, "short.mp4")
        make_video(short, seconds=2)
        cls.short = read(short)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "_min"):
            cls._min.stop()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        self.dir = tempfile.mkdtemp(dir=self.tmp)
        self.state = {}

    def run_backup(self, run, session):
        return vb.backup_one(run, self.state, "TOKEN", self.dir, session=session, pause=0)

    def tg_ok(self, size=None):
        return FakeResp(payload={"ok": True, "result": {"file_path": "videos/f.mp4",
                                                        "file_size": size or len(self.good)}})

    def test_probe_accepts_valid_video(self):
        info = vb.probe(self.good_path, len(self.good))
        self.assertGreaterEqual(info["seconds"], 4.5)

    def test_probe_rejects_truncated_and_short(self):
        bad = os.path.join(self.dir, "bad.mp4")
        write(bad, self.good[: len(self.good) // 2])
        with self.assertRaises(vb.BackupError):
            vb.probe(bad, len(self.good))       # eksik indirme
        with self.assertRaises(vb.BackupError):
            vb.probe(bad)                       # moov yok, ffprobe okuyamaz
        write(bad, self.short)
        with self.assertRaises(vb.BackupError):
            vb.probe(bad)                       # 2 sn < 4 sn

    def test_telegram_first_and_corrupt_retried(self):
        s = FakeSession({"https://api.telegram.org/botTOKEN/getFile": [self.tg_ok()],
                         "https://api.telegram.org/file/": [FakeResp(body=b"x" * 5000), FakeResp(body=self.good)]})
        e = self.run_backup({"id": RUN_ID, "telegram_file_id": "F", "video_url": "https://kie/x.mp4"}, s)
        self.assertEqual((e["status"], e["source"]), ("ok", "telegram"))
        self.assertFalse(any("kie" in c for c in s.calls))
        self.assertEqual(read(vb.video_path(KEY, self.dir)), self.good)
        self.assertFalse(os.path.exists(vb.video_path(KEY, self.dir) + ".part"))

    def test_telegram_too_big_reported_then_kie(self):
        s = FakeSession({"https://api.telegram.org/botTOKEN/getFile": [self.tg_ok(size=25 * 1024 * 1024)],
                         "https://kie/": [FakeResp(body=self.good)]})
        e = self.run_backup({"id": RUN_ID, "telegram_file_id": "F", "video_url": "https://kie/x.mp4"}, s)
        self.assertEqual((e["status"], e["source"]), ("ok", "kie"))
        self.assertEqual(e["error"], "indirilemedi (20 MB sınırı)")

    def test_telegram_too_big_api_message(self):
        s = FakeSession({"https://api.telegram.org/botTOKEN/getFile": [
            FakeResp(400, payload={"ok": False, "description": "Bad Request: file is too big"})]})
        e = self.run_backup({"id": RUN_ID, "telegram_file_id": "F"}, s)
        self.assertEqual(e["status"], "failed")
        self.assertTrue(e["too_big"])
        self.assertIn("indirilemedi (20 MB sınırı)", e["error"])

    def test_dead_kie_is_permanent_and_not_retried(self):
        s = FakeSession({"https://kie/": [FakeResp(404)]})
        e = self.run_backup({"id": RUN_ID, "video_url": "https://kie/x.mp4"}, s)
        self.assertEqual(e["status"], "failed")
        self.assertTrue(e["permanent"])
        self.assertEqual(len(s.calls), 1)

    def test_always_corrupt_fails_without_copy(self):
        s = FakeSession({"https://kie/": [FakeResp(body=b"y" * 5000)]})
        e = self.run_backup({"id": RUN_ID, "video_url": "https://kie/x.mp4"}, s)
        self.assertEqual(e["status"], "failed")
        self.assertEqual(len(s.calls), vb.ATTEMPTS)
        self.assertFalse(os.path.exists(vb.video_path(KEY, self.dir)))

    def test_existing_file_never_overwritten(self):
        dst = vb.video_path(KEY, self.dir)
        write(dst, b"bozuk ama benim dosyam" * 10)
        s = FakeSession({})
        e = self.run_backup({"id": RUN_ID, "telegram_file_id": "F", "video_url": "https://kie/x.mp4"}, s)
        self.assertEqual(e["status"], "bozuk_yerel")
        self.assertEqual(s.calls, [])
        self.assertTrue(read(dst).startswith(b"bozuk ama benim"))


class TestServerBackupRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.root = os.path.join(cls.tmp, "proj")
        cls.vdir = os.path.join(cls.tmp, "videolar")
        os.makedirs(os.path.join(cls.root, "dashboard_data"))
        os.makedirs(cls.vdir)
        with open(os.path.join(cls.root, "dashboard_data", "notion_runs.json"), "w", encoding="utf-8") as f:
            json.dump({"runs": [{"id": RUN_ID, "telegram_file_id": ""}]}, f)
        with open(os.path.join(cls.vdir, f"{KEY}.mp4"), "wb") as f:
            f.write(b"VIDEO")
        cls.srv = ds.make_server(root=cls.root, port=0, quiet=True, video_dir=cls.vdir)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def get(self, path):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        c.request("GET", path)
        r = c.getresponse()
        body = r.read()
        c.close()
        return r.status, body

    def test_local_copy_served(self):
        self.assertEqual(self.get(f"/videos/{KEY}.mp4"), (200, b"VIDEO"))
        self.assertEqual(self.get(f"/api/tg/{KEY}.mp4"), (200, b"VIDEO"))   # yerel varsa Telegram'a gitmez

    def test_bad_keys_forbidden(self):
        for p in ["/videos/../x.mp4", "/videos/ABC.mp4", f"/videos/{KEY}.py", "/videos/%2e%2e/secret.mp4"]:
            self.assertIn(self.get(p)[0], (403, 404), p)

    def test_tg_without_file_id(self):
        other = "0" * 32
        self.assertEqual(self.get(f"/api/tg/{other}.mp4")[0], 404)


class TestPanelHtml(unittest.TestCase):
    def test_badges_and_order(self):
        html = open(os.path.join(PROJECT_ROOT, "dashboard.html"), encoding="utf-8").read()
        for label in ["Yerel kopya", "Telegram", "YouTube", "Kopya yok", "indirilemedi (20 MB sınırı)",
                      "dashboard_data/video_backup.json"]:
            self.assertIn(label, html)
        fn = html[html.index("function videoSources"):html.index("const TG_LIMIT")]
        self.assertLess(fn.index("out.push(`videos/"), fn.index("out.push(`api/tg/"))
        self.assertLess(fn.index("out.push(`api/tg/"), fn.index("out.push(r.video_url)"))


if __name__ == "__main__":
    unittest.main()
