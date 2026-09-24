#!/usr/bin/env python3
"""TUR 23: scripts/refresh_youtube_token.py. Gerçek Google/Railway çağrısı yok; ağ ve onay akışı mock'lanır.
Kritik: yanlış kanal/başarısız doğrulamada Railway'e yazılmaz; başarıda Railway + .env güncellenir."""
import importlib.util
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import MagicMock, patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
spec = importlib.util.spec_from_file_location("refresh_tok", os.path.join(ROOT, "scripts", "refresh_youtube_token.py"))
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)


class TestEnvFile(unittest.TestCase):
    def test_replace_and_append(self):
        p = os.path.join(tempfile.mkdtemp(), ".env")
        open(p, "w", encoding="utf-8").write('A=1\nYOUTUBE_REFRESH_TOKEN="old"\n# yorum\nB=2\n')
        rt.set_env_value(p, "YOUTUBE_REFRESH_TOKEN", "new")
        self.assertEqual(open(p, encoding="utf-8").read(), 'A=1\nYOUTUBE_REFRESH_TOKEN="new"\n# yorum\nB=2\n')
        rt.set_env_value(p, "C", "3")
        self.assertEqual(rt.read_env(p), {"A": "1", "YOUTUBE_REFRESH_TOKEN": "new", "B": "2", "C": "3"})


class TestMainFlow(unittest.TestCase):
    ENV = {"YOUTUBE_CLIENT_ID": "cid", "YOUTUBE_CLIENT_SECRET": "sec", "RAILWAY_TOKEN": "rw"}

    def run_main(self, title="DeepMyster", stored_matches=True, new_token="NEWTOKEN"):
        writes, state = [], {"railway": "OLD"}

        def railway(query, variables, token):
            if "variableUpsert" in query:
                writes.append(variables["i"]["value"])
                state["railway"] = variables["i"]["value"] if stored_matches else "SOMETHING_ELSE"
                return {"variableUpsert": True}
            return {"variables": {"YOUTUBE_REFRESH_TOKEN": state["railway"]}}

        fake_setup = types.ModuleType("setup_youtube")
        fake_setup.get_credentials_via_local_server = MagicMock(return_value=MagicMock(refresh_token=new_token))
        tmp = tempfile.mkdtemp()
        local = os.path.join(tmp, ".env")
        open(local, "w", encoding="utf-8").write('YOUTUBE_REFRESH_TOKEN="OLD"\n')
        with patch.object(rt, "read_env", return_value=self.ENV), patch.object(rt, "railway", side_effect=railway), \
             patch.object(rt, "access_token", return_value=("at", "")), patch.object(rt, "channel_title", return_value=title), \
             patch.object(rt, "LOCAL_ENV", local), patch.object(rt, "MASTER_ENV", os.path.join(tmp, "none.env")), \
             patch.dict(sys.modules, {"setup_youtube": fake_setup}):
            code = rt.main()
        return code, writes, open(local, encoding="utf-8").read()

    def test_success_writes_railway_and_env(self):
        code, writes, local = self.run_main()
        self.assertEqual(code, 0)
        self.assertEqual(writes, ["NEWTOKEN"])
        self.assertIn('YOUTUBE_REFRESH_TOKEN="NEWTOKEN"', local)

    def test_wrong_channel_writes_nothing(self):
        code, writes, local = self.run_main(title="Başka Kanal")
        self.assertEqual(code, 1)
        self.assertEqual(writes, [])
        self.assertIn('"OLD"', local)

    def test_no_refresh_token_from_google(self):
        code, writes, _ = self.run_main(new_token=None)
        self.assertEqual((code, writes), (1, []))

    def test_railway_readback_mismatch_fails_and_keeps_local(self):
        code, writes, local = self.run_main(stored_matches=False)
        self.assertEqual(code, 1)
        self.assertIn('"OLD"', local)       # Railway doğrulanmadan lokal yazılmaz

    def test_missing_credentials(self):
        with patch.object(rt, "read_env", return_value={}):
            self.assertEqual(rt.main(), 1)


class TestBatFile(unittest.TestCase):
    def test_bat_calls_script_and_waits_on_error(self):
        raw = open(os.path.join(ROOT, "refresh_youtube_token.bat"), "rb").read()
        self.assertNotIn(b"\r\r", raw)
        text = raw.decode("ascii")
        self.assertIn("python scripts\\refresh_youtube_token.py", text)
        self.assertIn("pause", text)          # hatada pencere açık kalır
        self.assertIn("timeout /t 5", text)   # başarıda 5 sn sonra kapanır


if __name__ == "__main__":
    unittest.main()
