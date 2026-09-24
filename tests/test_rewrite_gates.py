#!/usr/bin/env python3
"""
TUR 21: preflight ve Kie retry rewrite'ından dönen hikaye aynı simplifier kapılarından geçer (C hariç).
Kalırsa geri bildirimle 1 kez daha yazılır; yine kalırsa preflight'ta PreflightError(content),
Kie retry'ında ContentFilterError. Işık metni senaryonun havasına uyar (R3). Gerçek API yok.
"""
import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import main
from config import settings
from core.creative_engine import CAMERA_ARCHETYPES, MARITIME_INSPIRATION_DOMAINS, apply_style_lock, join_story_and_style
from core.prompt_generator import SIMPLIFIER_GATES, make_story_validator
from core.prompt_sanitizer import PreflightError
from infrastructure.kie_client import ContentFilterError, KieClient

SCEN = {"visible_start": "The passenger car ferry rolls hard as four deckhands grab the rail.",
        "physical_movement": "Cars slide across the deck.", "visible_consequence": "Cars keep sliding toward the ramp.",
        "beat1_action_verb": "rolls"}
CTX = {"scenario": SCEN, "domain_id": "ferry_operations", "ship": "Passenger Car Ferry"}
STORY = "The passenger car ferry rolls hard as four deckhands grab the rail. Cars keep sliding toward the ramp."
GOOD = "The passenger car ferry lists hard as four deckhands grab the rail. Cars keep sliding toward the ramp."
BAD_F = "The vessel lists hard as four deckhands grab the rail. Cars keep sliding toward the ramp."          # F
BAD_A = "The passenger car ferry lists hard as four deckhands grab the rail. The cars finally halt."        # A
SUFFIX = "Static fixed-mount security CCTV camera."
J = lambda story: join_story_and_style(story, SUFFIX)


def run(preflight, rewrites, rejections=0, validator=True):
    client = KieClient()
    create_task = AsyncMock(side_effect=[ContentFilterError("nsfw")] * rejections + ["task-1"])
    rewrite = AsyncMock(side_effect=rewrites)
    with patch.object(settings, "IS_DRY_RUN", False), patch.object(settings, "POLL_INITIAL_WAIT", 0), \
         patch("core.prompt_sanitizer.gpt_preflight_check", AsyncMock(return_value=preflight)), \
         patch("core.prompt_sanitizer.gpt_rewrite_rejected_prompt", rewrite), \
         patch.object(KieClient, "_create_task", create_task), \
         patch.object(KieClient, "_poll_for_result", AsyncMock(return_value="https://cdn/v.mp4")):
        try:
            out = asyncio.run(client.create_video(model=settings.DEFAULT_MODEL, prompt=STORY, style_suffix=SUFFIX,
                                                  story_validator=make_story_validator(CTX) if validator else None))
        except (PreflightError, ContentFilterError) as e:
            out = e
    return out, [c.args[1] for c in create_task.await_args_list], rewrite


class TestValidator(unittest.TestCase):
    def test_none_context(self):
        self.assertIsNone(make_story_validator(None))

    def test_c_skipped_others_run(self):
        v = make_story_validator(CTX)
        self.assertEqual(v(GOOD), [])                     # Beat 1 fiili "rolls" -> "lists": C atlandı
        self.assertTrue(any(m.startswith(SIMPLIFIER_GATES["F"]) for m, _ in v(BAD_F)))
        self.assertTrue(any(m.startswith(SIMPLIFIER_GATES["A"]) for m, _ in v(BAD_A)))


class TestPreflightRewriteGated(unittest.TestCase):
    def test_bad_preflight_rewrite_fixed_with_feedback(self):
        out, sent, rewrite = run((BAD_F, True, {"risk_score": 7, "risk_reasons": ["x"]}), [GOOD])
        self.assertEqual(out, "https://cdn/v.mp4")
        self.assertEqual(sent, [J(GOOD)])
        fb = rewrite.await_args.kwargs["feedback"]
        self.assertTrue(any("passenger car ferry" in f for f in fb))
        self.assertEqual(rewrite.await_args.kwargs["original_prompt"], STORY)   # asıl hikayeden yeniden yazılır

    def test_preflight_rewrite_never_passes(self):
        out, sent, _ = run((BAD_F, True, {"risk_score": 7}), [BAD_A])
        self.assertIsInstance(out, PreflightError)
        self.assertEqual(out.kind, "content")
        self.assertEqual(sent, [])                       # Kie'ye hiç gitmedi

    def test_good_preflight_rewrite_no_extra_call(self):
        out, sent, rewrite = run((GOOD, True, {"risk_score": 7}), [])
        self.assertEqual(sent, [J(GOOD)])
        rewrite.assert_not_awaited()


class TestKieRewriteGated(unittest.TestCase):
    SAFE = (STORY, False, {"risk_score": 1})

    def test_first_rewrite_bad_second_good(self):
        out, sent, rewrite = run(self.SAFE, [BAD_A, GOOD], rejections=1)
        self.assertEqual(out, "https://cdn/v.mp4")
        self.assertEqual(sent, [J(STORY), J(GOOD)])
        self.assertEqual(rewrite.await_count, 2)
        self.assertIsNone(rewrite.await_args_list[0].kwargs["feedback"])
        self.assertTrue(rewrite.await_args_list[1].kwargs["feedback"])

    def test_both_rewrites_bad(self):
        out, sent, _ = run(self.SAFE, [BAD_A, BAD_F], rejections=1)
        self.assertIsInstance(out, ContentFilterError)
        self.assertEqual(len(sent), 1)                  # kalitesiz rewrite Kie'ye gönderilmedi

    def test_no_validator_legacy(self):
        out, sent, rewrite = run(self.SAFE, [BAD_F], rejections=1, validator=False)
        self.assertEqual(sent[1], J(BAD_F))
        self.assertEqual(rewrite.await_count, 1)


class TestMainPassesValidator(unittest.TestCase):
    def test_validator_built_from_gate_context(self):
        pd = {"scenes": [{"prompt": "s. l", "story": "s", "style_suffix": "l", "duration": 15}],
              "combo_key": "ferry_operations|passenger car ferry|e|x|fixed_cctv", "scenario_summary": "s",
              "gate_context": CTX}
        kie = MagicMock()
        kie.create_video = AsyncMock(return_value="https://cdn/v.mp4")
        tracker = MagicMock()
        tracker.get_recent_history.return_value = []
        tracker.get_recent_beat1_verbs.return_value = []
        with patch.object(settings, "IS_DRY_RUN", False), patch.object(main, "load_used_combos", return_value=[]), \
             patch.object(main, "NotionTracker", return_value=tracker), \
             patch.object(main, "generate_prompts", AsyncMock(return_value=pd)), \
             patch.object(main, "KieClient", return_value=kie), \
             patch.object(main, "download_video", return_value="v.mp4"), \
             patch.object(main, "motion_profile", side_effect=RuntimeError("x")):
            asyncio.run(main.run_pipeline(skip_upload=True))
        v = kie.create_video.await_args.kwargs["story_validator"]
        self.assertTrue(callable(v))
        self.assertTrue(v(BAD_F))


class TestLighting(unittest.TestCase):
    def test_weather_matched_lighting(self):
        for d in MARITIME_INSPIRATION_DOMAINS:
            for cam in CAMERA_ARCHETYPES:
                with self.subTest(domain=d, cam=cam):
                    out = apply_style_lock("x", cam, {"domain_id": d, "forced_ship": "None"})
                    self.assertNotIn("overcast/fog/rain lighting", out)
                    self.assertIn("matches the scenario's weather", out)
                    self.assertIn("never glossy, CGI-clean, or cinematic", out)


if __name__ == "__main__":
    unittest.main()
