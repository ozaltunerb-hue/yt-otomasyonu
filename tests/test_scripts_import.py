#!/usr/bin/env python3
"""TUR 19: scripts/ altındaki betikler import edilebilir (sözdizimi/bağımlılık hatası yok) ve import
sırasında iş yapmaz (__main__ korumalı; run_kie_batch Kie harcaması yapar). Gerçek API yok."""
import importlib.util
import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
SCRIPTS = ["dry_run_full", "finalize_prompts", "run_kie_batch", "notion_test_page", "motion_profile", "dry_run_beat1",
           "real_generation_check", "live_prompt_check", "batch_diversity_check"]   # son 3: TUR 21 tests/ dışına


class TestScriptsImport(unittest.TestCase):
    def test_import_without_side_effects(self):
        for name in SCRIPTS:
            with self.subTest(script=name):
                spec = importlib.util.spec_from_file_location(f"script_{name}", os.path.join(ROOT, "scripts", f"{name}.py"))
                mod = importlib.util.module_from_spec(spec)
                with patch("asyncio.run") as run, patch("requests.get") as get, patch.object(sys, "argv", ["x"]):
                    spec.loader.exec_module(mod)
                run.assert_not_called()
                get.assert_not_called()

    def test_notion_payload(self):
        spec = importlib.util.spec_from_file_location("ntp", os.path.join(ROOT, "scripts", "notion_test_page.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        res = {"credit_before": 1000.0, "credit_after": 825.0, "model": "m",
               "videos": [{"domain": "d", "camera": "c", "ship": "s", "file": "/x/a.mp4", "url": "u", "ffprobe": {},
                           "motion": "ilk3/sonrası=0.8", "final_prompt": "p"}, {"domain": "d2", "error": "boom"}]}
        payload = mod.build_payload(res, "TEST — x", "intro")
        self.assertNotIn("Combo Key", payload["properties"])
        text = str(payload["children"])
        self.assertIn("harcanan 175.0", text)
        self.assertIn("HATA: boom", text)
        self.assertIn("ilk3/sonrası=0.8", text)


if __name__ == "__main__":
    unittest.main()
