#!/usr/bin/env python3
"""
main.run_pipeline hata akışları (2026-09-24, TUR 13).

Kie reddi ve içerik kaynaklı preflight hatası aynı 3 senaryoluk bütçeyle yeni senaryo dener;
API kaynaklı preflight hatası hemen durur. Her reddedilen denemenin Notion kaydı hata olarak
kapanır (eskiden "Video Üretiliyor"da takılı kalıyordu). GPT/Kie/Notion mock'lanır.
"""
import asyncio
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import main
from config import settings
from core.prompt_sanitizer import PreflightError, gpt_preflight_check
from infrastructure.kie_client import ContentFilterError


def _prompt_data(i):
    return {"scenes": [{"prompt": f"story {i}. lock", "story": f"story {i}", "style_suffix": "lock", "duration": 15}],
            "combo_key": f"ferry_operations|passenger car ferry|e{i}|env|fixed_cctv",
            "scenario_summary": f"s{i}", "youtube_title": f"t{i}", "total_duration": 15}


def run(kie_outcomes):
    """kie_outcomes: her deneme için create_video sonucu (URL veya Exception)."""
    trackers = []

    def new_tracker():
        t = MagicMock()
        t.page_id = "p"
        t.get_recent_history.return_value = []
        trackers.append(t)
        return t

    gen = AsyncMock(side_effect=[_prompt_data(i) for i in range(1, 10)])
    kie = MagicMock()
    kie.create_video = AsyncMock(side_effect=kie_outcomes)
    used = []
    with patch.object(settings, "IS_DRY_RUN", False), \
         patch.object(main, "load_used_combos", return_value=used), \
         patch.object(main, "NotionTracker", side_effect=new_tracker), \
         patch.object(main, "generate_prompts", gen), \
         patch.object(main, "KieClient", return_value=kie), \
         patch.object(main, "download_video", return_value="v.mp4"), \
         patch.object(main, "motion_profile", return_value={"per_second": [1.0], "opening_avg": 1.0,
                                                           "rest_avg": None, "opening_ratio": None,
                                                           "peak_second": 1}):
        result = asyncio.run(main.run_pipeline(skip_upload=True))
    attempt_trackers = trackers[1:]   # ilk tracker run_pipeline'ın tarihçe okuyucusu
    errors = [t.update_with_error.call_args.args[0] for t in attempt_trackers if t.update_with_error.called]
    return result, gen, kie, used, errors


class TestPipelineRetry(unittest.TestCase):
    def test_preflight_content_then_success(self):
        result, gen, kie, used, errors = run([PreflightError("riskli", "content"), "https://cdn/v.mp4"])
        self.assertTrue(result["success"])
        self.assertEqual(gen.await_count, 2)
        self.assertIn(_prompt_data(1)["combo_key"], used)
        self.assertEqual(len(errors), 1)
        self.assertIn("Preflight (content)", errors[0])

    def test_preflight_content_three_times(self):
        result, gen, kie, used, errors = run([PreflightError("x", "content")] * 3)
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "preflight_content")
        self.assertEqual(gen.await_count, 3)
        self.assertEqual(len(errors), 3)

    def test_preflight_api_stops(self):
        result, gen, kie, used, errors = run([PreflightError("timeout", "api"), "https://cdn/v.mp4"])
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "preflight_api")
        self.assertEqual(gen.await_count, 1)
        self.assertEqual(len(errors), 1)
        self.assertIn("Preflight (api)", errors[0])

    def test_mixed_shares_budget(self):
        result, gen, kie, used, errors = run([ContentFilterError("nsfw"), PreflightError("x", "content"),
                                              "https://cdn/v.mp4"])
        self.assertTrue(result["success"])
        self.assertEqual(gen.await_count, 3)
        self.assertEqual(len(errors), 2)
        self.assertEqual(len(used), 2)

    def test_content_filter_closes_notion_record(self):
        result, gen, kie, used, errors = run([ContentFilterError("nsfw")] * 3)
        self.assertEqual(result["reason"], "content_filter")
        self.assertEqual(len(errors), 3)
        self.assertTrue(all("Kie içerik filtresi" in e for e in errors))

    def test_story_and_suffix_passed_to_kie(self):
        _, _, kie, _, _ = run(["https://cdn/v.mp4"])
        kw = kie.create_video.await_args.kwargs
        self.assertEqual((kw["prompt"], kw["style_suffix"]), ("story 1", "lock"))


class TestPreflightKind(unittest.TestCase):
    def kind(self, *outputs):
        resp = lambda c: SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=c))])
        client = MagicMock()
        client.chat.completions.create = AsyncMock(
            side_effect=[o if isinstance(o, Exception) else resp(o) for o in outputs])
        with patch("openai.AsyncOpenAI", return_value=client):
            with self.assertRaises(PreflightError) as cm:
                asyncio.run(gpt_preflight_check("story"))
        return cm.exception.kind

    def test_all_api(self):
        self.assertEqual(self.kind(*[RuntimeError("timeout")] * 3), "api")

    def test_all_broken_json(self):
        self.assertEqual(self.kind(*['{"safe": tr'] * 3), "content")

    def test_mixed(self):
        self.assertEqual(self.kind(RuntimeError("timeout"), '{"safe": tr', RuntimeError("timeout")), "content")


if __name__ == "__main__":
    unittest.main()
