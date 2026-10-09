#!/usr/bin/env python3
"""
TUR 31: creative hattı (varsayılan). GPT-4o hikâyeyi kısa sistem prompt'uyla yazar; sert kontroller sadece olay
uyuşması ve 40-60 kelime; stil eki iskeletle birebir aynı. Ağ çağrısı yok: GPT, Kie, Notion sahte.
"""
import asyncio
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import bot
import core.creative_pipeline as cp
import core.prompt_generator as pg
import core.prompt_sanitizer as ps
import core.skeleton_pipeline as sk
import main
from config import settings
from core.creative_engine import DOMAIN_ATTRIBUTES, is_current_universe_combo
from core.trace_format import format_generation
from infrastructure.kie_client import KieClient

_GUARDS = []


def setUpModule():
    import openai
    for name in ("OpenAI", "AsyncOpenAI"):
        p = patch.object(openai, name, side_effect=AssertionError(f"Testte gerçek openai.{name} kuruldu"))
        p.start()
        _GUARDS.append(p)
    p = patch.object(pg, "_get_openai_client", side_effect=AssertionError("Testte gerçek GPT istemcisi istendi"))
    p.start()
    _GUARDS.append(p)


def tearDownModule():
    for p in _GUARDS:
        p.stop()


WAVE = "Rogue wave breaks over the rail onto the pool deck"
STORY = ("A towering rogue wave breaks over the rail of the ocean cruise liner and crashes onto the open-air pool "
         "deck. Sun loungers skid across the soaked tiles as twelve passengers stagger toward the stairs. Seawater "
         "keeps pouring over the rail, still sweeping chairs and towels across the pool deck toward the far railing.")
SHORT = "A rogue wave breaks over the rail onto the pool deck."
OFF_TOPIC = ("A violent storm gust rips a sign off a downtown building and hurls it across four lanes of traffic "
             "while several pedestrians duck behind parked cars. Metal panels keep tumbling down the avenue, still "
             "bouncing off car roofs as the wind howls between the towers and more debris lifts off.")


class TestConfigAndPrompt(unittest.TestCase):
    def test_default_is_creative(self):
        from config import Config
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PROMPT_PIPELINE", None)
            self.assertEqual(Config().PROMPT_PIPELINE, "creative")

    def test_system_prompt_short_and_only_the_rules(self):
        self.assertLessEqual(len(cp.CREATIVE_SYSTEM.split()), 160)
        for rule in ("40 to 60 words", "trigger happens", "reaching the given outcome", "clearly visible on camera",
                     "still visibly moving at the very end", "Catastrophic in scale", "ankle-deep, floats, honking futilely",
                     "Name any given vessel by its type", "different from the recent stories"):
            self.assertIn(rule, cp.CREATIVE_SYSTEM)
        self.assertEqual(cp.CREATIVE_SYSTEM.count("\n1. ") + cp.CREATIVE_SYSTEM.count("\n5. "), 2)   # 5 kural
        self.assertNotIn("\n6. ", cp.CREATIVE_SYSTEM)   # ilk cümle netleştirmesi 2. kuralın içinde, yeni kural değil

    def test_first_sentence_is_the_trigger_and_no_phone(self):
        rule2 = [l for l in cp.CREATIVE_SYSTEM.splitlines() if l.startswith("2. ")][0]
        for part in ("The first sentence shows the moment the trigger happens", "the wave clears the rail",
                     "the cable snaps", "the wall of water enters the street", "never open with waiting, tension or buildup",
                     "never the camera or the video"):
            self.assertIn(part, rule2)
        self.assertTrue(cp.CREATIVE_SYSTEM.startswith("You write one short scene for a 15-second realistic video"))
        self.assertNotIn("phone", cp.CREATIVE_SYSTEM.lower())

    def test_outcomes_one_sentence_per_event(self):
        self.assertEqual(set(cp.EVENT_OUTCOMES), set(sk.EVENT_SKELETONS))
        for e, o in cp.EVENT_OUTCOMES.items():
            with self.subTest(event=e):
                self.assertNotIn(".", o.rstrip("."))
                self.assertLessEqual(len(o.split()), 30)

    def test_outcomes_fast_visible_motion(self):
        # Final turu denetimi: 15 sn'de görünmeyen yavaş süreç ifadesi yok
        import re
        for e, o in cp.EVENT_OUTCOMES.items():
            with self.subTest(event=e):
                self.assertIsNone(re.search(r"\b(?:rises?|rising|fills?|filling|gradually|begins? to|slowly|floods)\b", o), o)

    def test_slipway_launches_tip_sideways(self):
        for e in ("Restraining cable snaps during slipway launch", "Keel blocks collapse under the launching hull"):
            with self.subTest(event=e):
                o = cp.EVENT_OUTCOMES[e]
                # Yat ileri gitmez: olduğu yerde yana yatar, SONRA yan tarafıyla suya devrilir
                self.assertEqual(o, "the yacht heels over onto its side in place, then topples sideways into the water "
                                    "beside it with a huge splash and keeps rolling hard from side to side")
                self.assertLess(o.index("heels over onto its side in place"), o.index("then topples sideways"))
                import re
                self.assertIsNone(re.search(r"\b(?:slides? down|sliding|hurtl\w*|lurch\w*|forward|plung\w*|"
                                            r"div(?:e|es|ing)|nose\w*|bow-first)\b", o), o)
        self.assertEqual(sk.EVENT_SKELETONS["Restraining cable snaps during slipway launch"]["object"], "tilting yacht")
        self.assertEqual(sk.EVENT_SKELETONS["Keel blocks collapse under the launching hull"]["object"], "tilting hull")
        self.assertIn("the camera pans to follow the tilting yacht",
                      sk.style_suffix("Restraining cable snaps during slipway launch", "Luxury Motor Yacht",
                                      "Construction slipway"))
        self.assertEqual(sk.CAMERA_SPOTS["Construction slipway"],
                         "on the quay beside the slipway, level with the yacht's bow, seeing its whole side")

    def test_flash_flood_is_a_moving_wall(self):
        o = cp.EVENT_OUTCOMES["Flash flooding in city streets"]
        self.assertTrue(o.startswith("a wall of brown floodwater surges down the street"))
        self.assertNotIn("rises", o)

    def test_outcome_reaches_gpt(self):
        gpt = AsyncMock(return_value={"story": STORY})
        asyncio.run(cp.write_story(WAVE, None, "x", "y", [], gpt))
        self.assertIn("OUTCOME TO REACH IN THE LAST BEAT: waves keep sweeping loungers and people across the pool deck",
                      gpt.await_args.args[1])
        low = cp.CREATIVE_SYSTEM.lower()
        for old in ("friction", "rotate", "library", "beat plan", "additional vessel", "slipway", "brand",
                    "never write", "cast size", "silent screen"):
            self.assertNotIn(old, low)

    def test_story_word_count_is_in_range(self):
        self.assertTrue(40 <= len(STORY.split()) <= 60)


class TestChecks(unittest.TestCase):
    def test_word_count_and_event_checks(self):
        self.assertEqual(cp.story_issues(WAVE, STORY), [])
        self.assertTrue(any("words" in i for i in cp.story_issues(WAVE, SHORT)))
        self.assertTrue(any("event" in i for i in cp.story_issues(WAVE, OFF_TOPIC)))

    def test_event_feedback_names_missing_words(self):
        rain = ("Thunder rumbles as sheets of rain batter the city, water cascading over the sidewalks. Shoppers dash "
                "from storefronts, umbrellas flipping inside out in the wind. The rain keeps hammering down, still "
                "blowing across the awnings and bouncing off parked cars and the glass bus shelters nearby.")
        issue = [i for i in cp.story_issues("Flash flooding in city streets", rain) if "event" in i][0]
        self.assertIn("Flash", issue)
        self.assertIn("flooding", issue)

    def test_event_meaning_synonyms(self):
        E = "Flash flooding in city streets"
        deluge = "A sudden deluge turns the street into a brown river that sweeps cars away."
        torrent = "A torrent roars down the avenue, lifting parked cars off the road."
        rain = "Sheets of rain batter the city and bounce off the sidewalks."
        self.assertEqual(pg.event_fidelity_issues(E, deluge), [])
        self.assertEqual(pg.event_fidelity_issues(E, torrent), [])
        self.assertTrue(pg.event_fidelity_issues(E, rain))   # eşik aynı: sel olmayan yağmur geçmez
        self.assertEqual(pg.event_fidelity_issues("Tornado making landfall",
                                                  "A black twister crosses the shoreline and makes landfall."), [])

    def test_retry_once_with_feedback(self):
        gpt = AsyncMock(side_effect=[{"story": SHORT}, {"story": STORY}])
        story, attempts = asyncio.run(cp.write_story(WAVE, "Ocean Cruise Liner", "the open-air pool deck", "heavy rain",
                                                     [], gpt))
        self.assertEqual(story, STORY)
        self.assertEqual([len(a["issues"]) > 0 for a in attempts], [True, False])
        self.assertIn("REJECTED", gpt.await_args_list[1].args[1])
        self.assertEqual(gpt.await_args.kwargs["model"], "gpt-4o")

    def test_three_failures_raise(self):
        # 30 Eyl kural kapısı: deneme 2'den 3'e çıktı
        gpt = AsyncMock(return_value={"story": OFF_TOPIC})
        with self.assertRaises(cp.CreativeStoryError):
            asyncio.run(cp.write_story(WAVE, None, "x", "y", [], gpt))
        self.assertEqual(gpt.await_count, 3)

    def test_recent_stories_filter_and_limit(self):
        texts = [f"Başlık {i}" for i in range(10)] + [f"story {i} " + "word " * 25 for i in range(20)]
        rec = cp.recent_stories(texts)
        self.assertEqual(len(rec), 15)
        self.assertTrue(all(len(t.split()) >= 20 for t in rec))
        self.assertTrue(rec[-1].startswith("story 19"))

    def test_recent_stories_reach_gpt(self):
        gpt = AsyncMock(return_value={"story": STORY})
        asyncio.run(cp.write_story(WAVE, None, "x", "y", ["ONCEKI HIKAYE"], gpt))
        self.assertIn("- ONCEKI HIKAYE", gpt.await_args.args[1])

    def test_setting_from_skeleton_lists(self):
        for e, s in sk.EVENT_SKELETONS.items():
            for _ in range(5):
                spot, weather = cp.pick_setting(e)
                self.assertIn(spot, s["spots"])
                self.assertIn(weather, s["weather"])


def _fake_gpt(story=STORY):
    async def call(system, user, temperature=0.85, model="gpt-4o"):
        if system == cp.CREATIVE_SYSTEM:
            return {"story": story}
        return {"youtube_title": "⚠️ Test #Shorts", "youtube_description": "d", "tags": ["x"]}
    return AsyncMock(side_effect=call)


class TestGeneratePrompts(unittest.TestCase):
    def run_gen(self, config, pipeline="creative", story=STORY):
        gpt = _fake_gpt(story)
        forbid = AsyncMock(side_effect=AssertionError("creative hattında çağrılmamalı"))
        with patch.object(settings, "IS_DRY_RUN", False), patch.object(settings, "PROMPT_PIPELINE", pipeline), \
             patch.object(pg, "_call_gpt", gpt), patch.object(pg, "_generate_scenario", forbid), \
             patch.object(pg, "simplify_with_gate", forbid), patch.object(sk, "fill_slots", forbid):
            return asyncio.run(pg.generate_prompts(config)), gpt

    def test_creative_output(self):
        r, gpt = self.run_gen({"used_combos": [], "recent_topics": [], "domain": "cruise_ship_operations",
                               "event": WAVE})
        scene = r["scenes"][0]
        self.assertEqual(scene["story"], STORY)
        spot = r["selection"]["environment"]
        self.assertEqual(scene["style_suffix"], sk.style_suffix(WAVE, r["selection"]["ship"], spot))   # birebir aynı
        self.assertEqual(scene["prompt"], f"{STORY.rstrip('.')}. {scene['style_suffix']}")
        self.assertEqual((r["scenario_summary"], r["scenario_text"]), (STORY, STORY))
        self.assertIsNone(r["gate_context"])
        self.assertTrue(is_current_universe_combo(r["combo_key"]))
        self.assertEqual(r["trace"]["pipeline"], "creative")
        self.assertEqual([c.kwargs.get("model", "gpt-4o") for c in gpt.await_args_list], ["gpt-4o", "gpt-4o"])

    def test_all_three_switches(self):
        with patch.object(pg, "generate_skeleton_prompts", AsyncMock(return_value="S")), \
             patch.object(pg, "generate_legacy_prompts", AsyncMock(return_value="L")), \
             patch.object(pg, "generate_creative_prompts", AsyncMock(return_value="C")), \
             patch.object(settings, "IS_DRY_RUN", False):
            for value, want in (("creative", "C"), ("skeleton", "S"), ("legacy", "L")):
                with patch.object(settings, "PROMPT_PIPELINE", value):
                    self.assertEqual(asyncio.run(pg.generate_prompts({})), want)
            with patch.object(settings, "PROMPT_PIPELINE", "yok"):
                with self.assertRaises(ValueError):
                    asyncio.run(pg.generate_prompts({}))

    def test_detail_says_creative(self):
        r, _ = self.run_gen({"used_combos": [], "event": WAVE})
        text = "\n".join(t + "\n" + b for t, b in format_generation(r["trace"]))
        for part in ("Hat: creative", STORY, "Deneme 1 · ✅ geçti", "kural kapısı"):
            self.assertIn(part, text)


class TestPipelineCreative(unittest.TestCase):
    def test_end_to_end_mocked(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        tracker = MagicMock()
        tracker.page_id = None
        tracker.get_recent_history.return_value = ["eski hikaye " + "kelime " * 30]
        tracker.get_recent_beat1_verbs.return_value = []
        create = AsyncMock(return_value="t1")
        gpt = _fake_gpt()

        def download(url):
            fd, p = tempfile.mkstemp(suffix=".mp4")
            os.write(fd, b"\0" * 2048)
            os.close(fd)
            return p
        with patch.object(settings, "IS_DRY_RUN", False), patch.object(settings, "PROMPT_PIPELINE", "creative"), \
             patch.object(settings, "ARCHIVE_DIR", d), patch.object(settings, "POLL_INITIAL_WAIT", 0), \
             patch.object(pg, "_call_gpt", gpt), \
             patch.object(main, "load_used_combos", return_value=[]), patch.object(main, "NotionTracker", return_value=tracker), \
             patch.object(ps, "gpt_preflight_check", AsyncMock(side_effect=lambda s: (s, False, {"risk_score": 1}))), \
             patch.object(KieClient, "_create_task", create), \
             patch.object(KieClient, "_poll_for_result", AsyncMock(return_value="https://cdn/v.mp4")), \
             patch.object(KieClient, "get_credit", AsyncMock(return_value=None)), \
             patch.object(main, "download_video", side_effect=download), \
             patch.object(main, "motion_profile", MagicMock(side_effect=RuntimeError("yok"))), \
             patch.object(main, "upload_to_youtube", AsyncMock()) as upload:
            r = asyncio.run(main.run_pipeline(skip_upload=True, mode="TEST", domain="cruise_ship_operations",
                                              event=WAVE, trigger="manual"))
        self.assertTrue(r["success"], r)
        sent = create.await_args.args[1]
        self.assertTrue(sent.startswith(STORY.rstrip(".")))
        self.assertIn("Handheld footage shot by a person standing on the pool deck", sent)
        self.assertNotIn("phone", sent[len(STORY):].lower())   # stil ekinde "phone" yok
        tracker.get_recent_history.assert_called_with(days=30, limit=40)
        self.assertIn("eski hikaye", gpt.await_args_list[0].args[1])   # tekrar önleme listesi GPT'ye gitti
        upload.assert_not_awaited()


class TestMenuAndHistory(unittest.TestCase):
    def test_menu_22_in_creative(self):
        with patch.object(settings, "PROMPT_PIPELINE", "creative"):
            self.assertEqual(sum(len(bot.domain_events(d)) for d in DOMAIN_ATTRIBUTES), 28)   # 1 Eki: 2 marina çıktı, 1 girdi; 2 Eki: + 3 heyelan; 8 Eki: + 3 yangın; 10 Eki: + helikopter

    def test_recent_history_limit(self):
        from infrastructure import notion_logger as nl

        def page(i):
            return {"properties": {"Combo Key": {"rich_text": [{"text": {"content": "ferry_operations|none|a|b|c"}}]},
                                   "Konu": {"rich_text": [{"text": {"content": f"konu {i}"}}]},
                                   "Video Adı": {"title": [{"text": {"content": f"başlık {i}"}}]}}}
        req = MagicMock(return_value={"results": [page(i) for i in range(30)]})
        with patch.object(settings, "NOTION_ENABLED", True), patch.object(settings, "IS_DRY_RUN", False), \
             patch.object(nl, "_notion_request", req):
            t = nl.NotionTracker()
            self.assertEqual(len(t.get_recent_history(days=30)), 20)
            self.assertEqual(len(t.get_recent_history(days=30, limit=40)), 40)


if __name__ == "__main__":
    unittest.main()
