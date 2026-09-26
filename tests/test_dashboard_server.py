#!/usr/bin/env python3
"""
scripts/dashboard_server.py izin listesi testleri (2026-09-26).
Panel sunucusu sadece dashboard.html, status.json, dashboard_data/ ve .mp4 sunar; .env, nokta ile
başlayanlar, .py ve proje dışı her şey 403. Hem geçici bir klasörde hem gerçek proje kökünde denenir.
"""
import http.client
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_spec = importlib.util.spec_from_file_location("dashboard_server", os.path.join(PROJECT_ROOT, "scripts", "dashboard_server.py"))
ds = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ds)


class _ServerCase(unittest.TestCase):
    root = None

    @classmethod
    def start(cls, root):
        cls.srv = ds.make_server(root=root, port=0, quiet=True)   # port 0: boş port
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def get(self, path, headers=None, method="GET"):
        # http.client yolu olduğu gibi gönderir ("../" ve %2e normalize edilmez)
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        c.request(method, path, headers=headers or {})
        r = c.getresponse()
        body = r.read()
        c.close()
        return r.status, body, r


class TestRealProjectRoot(_ServerCase):
    """İstenen asıl kural: gerçek projede /.env ve /main.py 403."""

    @classmethod
    def setUpClass(cls):
        cls.start(PROJECT_ROOT)

    def test_env_forbidden(self):
        self.assertEqual(self.get("/.env")[0], 403)

    def test_main_py_forbidden(self):
        self.assertEqual(self.get("/main.py")[0], 403)

    def test_dashboard_served(self):
        status, body, _ = self.get("/dashboard.html")
        self.assertEqual(status, 200)
        self.assertIn(b"DeepMyster", body)


class TestAllowlist(_ServerCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.outside = tempfile.mkdtemp()
        root = os.path.join(cls.tmp, "proj")
        os.makedirs(os.path.join(root, "dashboard_data"))
        os.makedirs(os.path.join(root, "scratch"))
        os.makedirs(os.path.join(root, ".git"))
        os.makedirs(os.path.join(root, "infrastructure"))
        files = {
            ".env": "OPENAI_API_KEY=secret",
            "main.py": "print('x')",
            "youtube_token.json": '{"refresh_token": "secret"}',
            "railway.json": '{"deploy": {"cronSchedule": "30 13 * * 1,5"}}',
            "dashboard.html": "<html>panel</html>",
            "status.json": '{"state": "running"}',
            "dashboard_data/notion_runs.json": '{"runs": []}',
            "dashboard_data/x.py": "print(1)",
            ".git/config": "[core]",
            "infrastructure/kie_client.py": "KEY='x'",
            "scratch/final_prompts.json": "[]",
            "scratch/kie_t_result.json": json.dumps({"videos": [{"file": "C:\\x\\clip.mp4", "domain": "d", "camera": "c", "story": "s"}]}),
            "clip.mp4": "0123456789",
            "scratch/test.mp4": "abc",
        }
        for rel, content in files.items():
            with open(os.path.join(root, *rel.split("/")), "w", encoding="utf-8") as f:
                f.write(content)
        with open(os.path.join(cls.tmp, "secret.txt"), "w") as f:
            f.write("outside")
        cls.start(root)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(cls.tmp, ignore_errors=True)
        shutil.rmtree(cls.outside, ignore_errors=True)

    def assertForbidden(self, path):
        status, body, _ = self.get(path)
        self.assertEqual(status, 403, f"{path} -> {status}")
        self.assertNotIn(b"secret", body)

    def test_allowed(self):
        for path in ["/dashboard.html", "/status.json", "/dashboard_data/notion_runs.json", "/clip.mp4", "/scratch/test.mp4"]:
            self.assertEqual(self.get(path)[0], 200, path)

    def test_root_redirects_to_dashboard(self):
        status, _, r = self.get("/")
        self.assertEqual(status, 302)
        self.assertEqual(r.getheader("Location"), "/dashboard.html")

    def test_secrets_and_code_forbidden(self):
        for path in ["/.env", "/main.py", "/youtube_token.json", "/railway.json", "/.git/config",
                     "/infrastructure/kie_client.py", "/dashboard_data/x.py", "/scratch/final_prompts.json"]:
            self.assertForbidden(path)

    def test_encoding_and_case_tricks_forbidden(self):
        for path in ["/%2eenv", "/%2Eenv", "/.ENV", "/MAIN.PY", "/main.py.", "/main.py%20",
                     "/main.py::$DATA", "/main%2epy", "/dashboard_data/../.env", "/./.env",
                     "/dashboard_data%5c..%5c.env", "/.env?x=dashboard.html", "/.env%00.mp4"]:
            self.assertForbidden(path)

    def test_outside_project_forbidden(self):
        for path in ["/../secret.txt", "/%2e%2e/secret.txt", "/..%2fsecret.txt", "/dashboard_data/../../secret.txt",
                     "//etc/passwd", "/C:/Windows/win.ini", "/../secret.mp4"]:
            self.assertForbidden(path)

    def test_directory_listing_forbidden(self):
        for path in ["/scratch/", "/dashboard_data/", "/.git/"]:
            self.assertIn(self.get(path)[0], (403, 404), path)
            self.assertNotIn(b"href", self.get(path)[1])

    def test_missing_allowed_file_is_404(self):
        self.assertEqual(self.get("/dashboard_data/token_refresh.json")[0], 404)

    def test_range_for_video_seek(self):
        status, body, r = self.get("/clip.mp4", headers={"Range": "bytes=2-5"})
        self.assertEqual(status, 206)
        self.assertEqual(body, b"2345")
        self.assertEqual(r.getheader("Content-Range"), "bytes 2-5/10")

    def test_api_local_summary(self):
        status, body, _ = self.get("/api/local.json")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertNotIn("cron", data)   # cron 2026-09-26'da kaldırıldı
        paths = {v["path"]: v for v in data["videos"]}
        self.assertEqual(set(paths), {"clip.mp4", "scratch/test.mp4"})
        self.assertEqual(paths["clip.mp4"]["info"]["domain"], "d")
        self.assertNotIn(b"secret", body)


class TestDashboardHtml(unittest.TestCase):
    """Panel Telegram tetikleyiciye göre (2026-09-26): cron kalıntısı yok, şema ve kayıtlar güncel."""

    @classmethod
    def setUpClass(cls):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.html = open(os.path.join(root, "dashboard.html"), encoding="utf-8").read()
        cls.js = re.search(r"<script>\s*\n(.*?)</script>", cls.html, re.S).group(1)

    def test_no_cron_left(self):
        for word in ("parseCron", "renderCron", "nextCronRuns", "isCronRun", "STATE.cron", 'id="cron"', "cronSchedule", "Railway'deki cron"):
            with self.subTest(word=word):
                self.assertNotIn(word, self.html)

    def test_domain_labels_match_bot(self):
        import bot
        block = re.search(r"const DOMAIN_LABELS = \{(.*?)\};", self.js, re.S).group(1)
        labels = dict(re.findall(r'^\s*(\w+): "([^"]+)",', block, re.M))
        self.assertEqual(labels, bot.DOMAIN_LABELS)

    def test_pipeline_has_telegram_boxes(self):
        nodes = re.search(r"const NODES = \[(.*?)\];", self.js, re.S).group(1)
        ids = re.findall(r'\["(\w+)",', nodes)
        self.assertEqual(ids[0], "telegram")
        self.assertEqual(ids[-1], "tgvideo")
        self.assertIn("0 · Telegram /uret", nodes)
        self.assertIn("telegram --> senaryo", self.js)
        self.assertIn("youtube --> tgvideo", self.js)

    def test_records_show_trigger_and_domain(self):
        self.assertIn("tetik: ${esc(r.trigger", self.js)
        self.assertIn("esc(domainOf(r))", self.js)
        self.assertIn('id="trigger"', self.html)

    def _node(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node yok")
        return node

    def test_js_syntax(self):
        node = self._node()
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(self.js)
        self.addCleanup(os.remove, f.name)
        r = subprocess.run([node, "--check", f.name], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_domain_of(self):
        node = self._node()
        start = self.js.index("const DOMAIN_LABELS")
        end = self.js.index("}", self.js.index("function domainOf")) + 1
        snippet = self.js[start:end] + """
console.log(JSON.stringify([
  domainOf({combo_key: "ferry_operations|passenger car ferry|e|env|fixed_cctv"}),
  domainOf({combo_key: ""}), domainOf({}), domainOf({combo_key: "old_domain|x|y|z|c"})]));"""
        r = subprocess.run([node, "-e", snippet], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout), ["⛴️ Feribot", "", "", "old_domain"])


if __name__ == "__main__":
    unittest.main()
