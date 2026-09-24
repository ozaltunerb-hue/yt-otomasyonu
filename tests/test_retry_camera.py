#!/usr/bin/env python3
"""
Kie içerik filtresi retry'ı kamera tipini korur (2026-09-24, TUR 12).

Eskiden rewrite tam prompt'u (stil kilidi dahil, ~300 kelime) max_tokens=250 ile yeniden
yazıyordu (kesilme), "CCTV realism" isteyip sona "Raw surveillance footage" ekliyordu; hata
olunca sessizce regex yumuşatmaya düşüyordu. Şimdi GPT sadece hikayeyi yazar, stil eki
değişmeden eklenir; rewrite başarısızsa ContentFilterError fırlar. Gerçek API çağrısı yok.
"""
import asyncio
import json
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import settings
from core.creative_engine import apply_style_lock, join_story_and_style, style_lock_suffix
from core.prompt_sanitizer import PromptRewriteError, gpt_rewrite_rejected_prompt
from infrastructure.kie_client import ContentFilterError, KieClient

STORY = "The passenger car ferry rolls hard as four deckhands in orange coveralls grab the rail. Cars keep sliding."
SAFE_STORY = "The passenger car ferry rolls hard as four deckhands in orange coveralls hold the rail. Cars keep sliding."
CAT = {"domain_id": "ferry_operations", "forced_ship": "Passenger Car Ferry"}
CAMS = ["fixed_cctv", "bystander_handheld", "chase_pov"]
SAFE_PREFLIGHT = (STORY, False, {"risk_score": 1})


def _resp(text):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


def run_video(style_suffix, rewrite, preflight=SAFE_PREFLIGHT, rejections=1):
    """Kie ilk `rejections` denemede reddeder. Dönüş: (url|hata, _create_task mock, rewrite mock)."""
    client = KieClient()
    create_task = AsyncMock(side_effect=[ContentFilterError("nsfw")] * rejections + ["task-1"])
    with patch.object(settings, "IS_DRY_RUN", False), patch.object(settings, "POLL_INITIAL_WAIT", 0), \
         patch("core.prompt_sanitizer.gpt_preflight_check", AsyncMock(return_value=preflight)), \
         patch("core.prompt_sanitizer.gpt_rewrite_rejected_prompt", rewrite), \
         patch.object(KieClient, "_create_task", create_task), \
         patch.object(KieClient, "_poll_for_result", AsyncMock(return_value="https://cdn/v.mp4")):
        try:
            result = asyncio.run(client.create_video(model=settings.DEFAULT_MODEL, prompt=STORY,
                                                     style_suffix=style_suffix))
        except ContentFilterError as e:
            result = e
    return result, create_task, rewrite


def sent_prompts(create_task):
    return [c.args[1] for c in create_task.await_args_list]


class TestStyleSuffix(unittest.TestCase):
    def test_suffix_rebuilds_apply_style_lock(self):
        for cam in CAMS:
            for cat in (CAT, {"domain_id": "urban_city_disasters", "forced_ship": "None"}, None):
                with self.subTest(cam=cam, cat=cat):
                    self.assertEqual(join_story_and_style(STORY, style_lock_suffix(cam, cat)),
                                     apply_style_lock(STORY, cam, cat))


class TestRetryKeepsCamera(unittest.TestCase):
    def test_each_camera_survives_retry(self):
        for cam in CAMS:
            with self.subTest(cam=cam):
                suffix = style_lock_suffix(cam, CAT)
                url, create_task, rewrite = run_video(suffix, AsyncMock(return_value=SAFE_STORY))
                self.assertEqual(url, "https://cdn/v.mp4")
                first, second = sent_prompts(create_task)
                self.assertEqual(first, join_story_and_style(STORY, suffix))
                self.assertEqual(second, join_story_and_style(SAFE_STORY, suffix))
                self.assertEqual(second.count(suffix), 1)
                if cam != "fixed_cctv":
                    self.assertNotIn("CCTV", second)
                    self.assertNotIn("surveillance", second.lower())

    def test_rewrite_sees_only_story(self):
        suffix = style_lock_suffix("chase_pov", CAT)
        _, _, rewrite = run_video(suffix, AsyncMock(return_value=SAFE_STORY))
        self.assertEqual(rewrite.await_args.kwargs["original_prompt"], STORY)

    def test_preflight_rewrite_keeps_suffix(self):
        suffix = style_lock_suffix("bystander_handheld", CAT)
        _, create_task, _ = run_video(suffix, AsyncMock(), preflight=(SAFE_STORY, True, {"risk_score": 7}),
                                      rejections=0)
        self.assertEqual(sent_prompts(create_task), [join_story_and_style(SAFE_STORY, suffix)])

    def test_rewrite_failure_raises_no_softening(self):
        suffix = style_lock_suffix("bystander_handheld", CAT)
        err, create_task, _ = run_video(suffix, AsyncMock(side_effect=PromptRewriteError("boş")))
        self.assertIsInstance(err, ContentFilterError)
        self.assertEqual(len(sent_prompts(create_task)), 1)   # yumuşatılmış metinle tekrar gönderilmedi

    def test_legacy_no_suffix(self):
        _, create_task, rewrite = run_video("", AsyncMock(return_value=SAFE_STORY))
        self.assertEqual(sent_prompts(create_task), [STORY, SAFE_STORY])


class TestRewriteFunction(unittest.TestCase):
    def call(self, *outputs):
        create = AsyncMock(side_effect=[o if isinstance(o, Exception) else _resp(o) for o in outputs])
        client = MagicMock()
        client.chat.completions.create = create
        with patch("openai.AsyncOpenAI", return_value=client):
            try:
                return asyncio.run(gpt_rewrite_rejected_prompt(STORY, "nsfw")), create
            except PromptRewriteError as e:
                return e, create

    def test_no_camera_tag_appended(self):
        out, create = self.call(SAFE_STORY)
        self.assertEqual(out, SAFE_STORY)
        msgs = create.await_args.kwargs["messages"]
        self.assertNotIn("Maintain 100% CCTV", msgs[0]["content"])
        self.assertIn("Do NOT add any camera", msgs[0]["content"])
        self.assertNotIn("CCTV prompt", msgs[1]["content"])

    def test_json_wrapped(self):
        out, _ = self.call(json.dumps({"prompt": SAFE_STORY}))
        self.assertEqual(out, SAFE_STORY)

    def test_failures_raise(self):
        for bad in ["", "too short", RuntimeError("timeout"), json.dumps({"x": 1})]:
            with self.subTest(bad=str(bad)[:20]):
                out, _ = self.call(bad)
                self.assertIsInstance(out, PromptRewriteError)

    def test_softened_prompt_removed(self):
        import core.prompt_sanitizer as ps
        self.assertFalse(hasattr(ps, "create_softened_prompt"))


if __name__ == "__main__":
    unittest.main()
