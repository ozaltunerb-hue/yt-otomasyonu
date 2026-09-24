#!/usr/bin/env python3
"""
main.run_pipeline akış testleri (2026-09-24, TUR 20 / T1). TUR 13'teki retry testlerini tamamlar:
hareket profili, hata yollarında Notion kaydının kapanması (takılı kayıt yok), upload modları,
retry'da reddedilen combo'nun yeni senaryo üretimine gitmesi. Ayrıca yazıcı kural 5/7 domain'e göre.
GPT/Kie/Notion/YouTube mock'lanır.
"""
import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import core.prompt_generator as pg
import main
from config import settings
from core.creative_engine import DOMAIN_CAST_RANGES, ENV_CENTRIC_DOMAINS
from core.prompt_generator import NoValidScenarioError
from infrastructure.kie_client import ContentFilterError

MOTION = {"per_second": [2.0, 3.0, 3.0, 6.0], "opening_avg": 2.7, "rest_avg": 6.0, "opening_ratio": 0.45, "peak_second": 4}


def _prompt_data(i):
    return {"scenes": [{"prompt": f"story {i}. lock", "story": f"story {i}", "style_suffix": "lock", "duration": 15}],
            "combo_key": f"ferry_operations|passenger car ferry|e{i}|env|fixed_cctv",
            "scenario_summary": f"s{i}", "youtube_title": f"t{i}", "total_duration": 15, "beat1_action_verb": "snaps"}


def run(kie=("https://cdn/v.mp4",), gen=None, skip_upload=True, youtube_enabled=False,
        download=None, motion=None, upload=None):
    trackers = []

    def new_tracker():
        t = MagicMock()
        t.page_id = None
        t.get_recent_history.return_value = []
        t.get_recent_beat1_verbs.return_value = ["lurches"]
        t.create_entry.side_effect = lambda *a, **k: setattr(t, "page_id", "p")
        trackers.append(t)
        return t

    gen = gen or AsyncMock(side_effect=[_prompt_data(i) for i in range(1, 10)])
    kie_client = MagicMock()
    kie_client.create_video = AsyncMock(side_effect=list(kie))
    upload = upload or AsyncMock(return_value="https://youtu.be/x")
    with patch.object(settings, "IS_DRY_RUN", False), patch.object(settings, "YOUTUBE_ENABLED", youtube_enabled), \
         patch.object(main, "load_used_combos", return_value=[]), \
         patch.object(main, "NotionTracker", side_effect=new_tracker), \
         patch.object(main, "generate_prompts", gen), \
         patch.object(main, "KieClient", return_value=kie_client), \
         patch.object(main, "download_video", download or MagicMock(return_value="v.mp4")), \
         patch.object(main, "motion_profile", motion or MagicMock(return_value=MOTION)), \
         patch.object(main, "upload_to_youtube", upload), \
         patch.object(main, "cleanup_video"):
        result = asyncio.run(main.run_pipeline(skip_upload=skip_upload))
    return SimpleRun(result, trackers[0], trackers[1:], gen, upload)


class SimpleRun:
    def __init__(self, result, reader, attempts, gen, upload):
        self.result, self.reader, self.attempts, self.gen, self.upload = result, reader, attempts, gen, upload

    def statuses(self, i=0):
        return [c.args[0] for c in self.attempts[i].update_status.call_args_list]

    def errors(self):
        return [t.update_with_error.call_args.args[0] for t in self.attempts if t.update_with_error.called]


class TestMotion(unittest.TestCase):
    def test_motion_written(self):
        r = run()
        self.assertTrue(r.result["success"])
        text = r.attempts[0].update_with_motion.call_args.args[0]
        self.assertIn("ilk3/sonrası=0.45", text)
        self.assertIn("kamera=fixed_cctv", text)   # combo_key'in son parçası

    def test_motion_failure_not_fatal(self):
        r = run(motion=MagicMock(side_effect=RuntimeError("ffmpeg yok")))
        self.assertTrue(r.result["success"])
        self.assertEqual(r.attempts[0].update_with_motion.call_args.args[0], "ölçülemedi: ffmpeg yok")
        self.assertFalse(r.attempts[0].update_with_error.called)


class TestNoStuckRecords(unittest.TestCase):
    def test_download_failure_closes_record(self):
        r = run(download=MagicMock(side_effect=RuntimeError("404")))
        self.assertFalse(r.result["success"])
        self.assertEqual(r.errors(), ["404"])
        self.assertEqual(r.gen.await_count, 1)      # senaryoya bağlı değil, yeni senaryo denenmez

    def test_kie_generic_error_closes_record(self):
        r = run(kie=[TimeoutError("poll timeout")])
        self.assertFalse(r.result["success"])
        self.assertEqual(r.errors(), ["poll timeout"])
        self.assertIn("Video Üretiliyor", r.statuses())   # hata öncesi son durum buydu, artık kapanıyor

    def test_no_valid_scenario_opens_and_closes_record(self):
        r = run(gen=AsyncMock(side_effect=NoValidScenarioError("5 senaryo kaldı")))
        self.assertEqual(r.result["reason"], "no_valid_scenario")
        t = r.attempts[0]
        self.assertIn("Boş Cron", t.create_entry.call_args.args[0]["topic"])
        self.assertIn("5 senaryo kaldı", t.update_with_error.call_args.args[0])


class TestUploadModes(unittest.TestCase):
    def test_skip_upload(self):
        r = run(skip_upload=True, youtube_enabled=True)
        r.upload.assert_not_awaited()
        self.assertEqual(r.statuses()[-1], "✅ Tamamlandı (Test Modu / YouTube Atlandı)")

    def test_youtube_disabled(self):
        r = run(skip_upload=False, youtube_enabled=False)
        r.upload.assert_not_awaited()

    def test_upload_success(self):
        r = run(skip_upload=False, youtube_enabled=True)
        r.upload.assert_awaited_once()
        r.attempts[0].update_with_youtube.assert_called_once_with("https://youtu.be/x")
        self.assertEqual(r.result["privacy"], settings.YOUTUBE_PRIVACY)
        self.assertEqual(r.statuses()[-1], "✅ Tamamlandı")

    def test_upload_failure_keeps_video(self):
        r = run(skip_upload=False, youtube_enabled=True, upload=AsyncMock(side_effect=RuntimeError("invalid_grant")))
        self.assertTrue(r.result["success"])
        self.assertEqual(r.statuses()[-1], "✅ Tamamlandı (Upload Başarısız)")
        self.assertFalse(r.attempts[0].update_with_error.called)

    def test_default_privacy_private(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("YOUTUBE_PRIVACY", None)
            from config import Config
            self.assertEqual(Config().YOUTUBE_PRIVACY, "private")


class TestRetryPlumbing(unittest.TestCase):
    def test_rejected_combo_reaches_next_generation(self):
        r = run(kie=[ContentFilterError("nsfw"), "https://cdn/v.mp4"])
        self.assertTrue(r.result["success"])
        second_cfg = r.gen.await_args_list[1].args[0]
        self.assertIn(_prompt_data(1)["combo_key"], second_cfg["used_combos"])

    def test_recent_verbs_passed(self):
        r = run()
        self.assertEqual(r.gen.await_args.args[0]["recent_verbs"], ["lurches"])


class TestWriterRules5And7(unittest.TestCase):
    def user_msg(self, domain, ship):
        cat = {"domain_id": domain, "domain_title": "t", "guidance": "g", "example_elements": [], "camera_styles": [],
               "forced_ship": ship, "forced_event": "e", "forced_environment": "x"}
        mock = AsyncMock(return_value={})
        with patch.object(pg, "_call_gpt", mock):
            asyncio.run(pg._generate_scenario(cat, "fixed_cctv"))
        return mock.call_args.args[1]

    def test_env_centric_no_vessel_clothing(self):
        for d in ENV_CENTRIC_DOMAINS:
            with self.subTest(domain=d):
                m = self.user_msg(d, "None")
                for bad in ["car-deck", "pool/deck", "boat owners", "yacht-casual", "pure raw industrial physics"]:
                    self.assertNotIn(bad, m)
                self.assertIn("never hi-vis PPE on civilians", m)
                self.assertIn("emergency responders", m)
                self.assertNotIn("Marina and dock workers", m)

    def test_tornado_marina_dock_workers(self):
        self.assertIn("Marina and dock workers", self.user_msg("coastal_tornado_landfall", "Sailing Yacht"))

    def test_vessel_domains_unchanged(self):
        for d in DOMAIN_CAST_RANGES:
            with self.subTest(domain=d):
                m = self.user_msg(d, "Passenger Car Ferry")
                self.assertIn("casual clothing for car-deck scenes", m)
                self.assertIn("Dress crew/staff in authentic high-visibility", m)
                self.assertNotIn("pure raw industrial physics", m)


if __name__ == "__main__":
    unittest.main()
