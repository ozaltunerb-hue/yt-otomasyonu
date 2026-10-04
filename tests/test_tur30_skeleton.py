#!/usr/bin/env python3
"""
TUR 30: iskelet hattı (varsayılan) + eski hat anahtarı. Ağ çağrısı yok: gpt-4o-mini boşluk doldurma, metadata,
Kie, Notion sahte. Gerçek OpenAI istemcisi kurulursa test patlar.
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
import core.prompt_generator as pg
import core.prompt_sanitizer as ps
import core.skeleton_pipeline as sk
import main
from config import settings
from core.creative_engine import DOMAIN_ATTRIBUTES, is_current_universe_combo
from core.trace_format import count_constraints, format_generation
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


def _valid_slots(event, ship=None, i=0):
    s = sk.EVENT_SKELETONS[event]
    lo, hi = sk.count_range(event, ship)
    spots, weather, people = list(s["spots"]), s["weather"], s["people"]
    return {"spot": spots[i % len(spots)], "weather": weather[i % len(weather)], "people": people[i % len(people)],
            "count": lo if i % 2 == 0 else hi}


def _combos():
    for e, s in sk.EVENT_SKELETONS.items():
        for ship in (s["ships"] or [None]):
            for i in range(max(len(s["spots"]), len(s["weather"]), len(s["people"]), 2)):
                yield e, ship, _valid_slots(e, ship, i)


class TestEventPool(unittest.TestCase):
    def test_22_events_by_category(self):
        counts = {d: len(sk.skeleton_events(d)) for d in DOMAIN_ATTRIBUTES}
        self.assertEqual(counts, {"ferry_operations": 3, "shipyard_and_drydock_engineering": 5,
                                  "marina_and_yacht_operations": 2, "cruise_ship_operations": 3,
                                  "coastal_tornado_landfall": 3, "urban_city_disasters": 2,
                                  "open_beach_coastal_events": 3, "landslide_disasters": 3})   # 2 Eki: heyelan
        self.assertEqual(sum(counts.values()), 24)

    def test_removed_events(self):
        # 30 Eyl: + tabela/iskele (aksiyonsuz video); 1 Eki: + halat, kontrolsüz yat; 4 Eki (TASLAK): + hortum kıyıya
        # yaklaşma, yağmur bantları
        self.assertEqual(len(sk.REMOVED_EVENTS), 22)
        self.assertIn("Tornado approaching coastline", sk.REMOVED_EVENTS)
        self.assertIn("Tornado rain bands and flying debris lash the waterfront", sk.REMOVED_EVENTS)
        self.assertIn("Storm gust tears signs and scaffolding loose downtown", sk.REMOVED_EVENTS)
        self.assertIn("Mooring line snaps in a storm gust", sk.REMOVED_EVENTS)
        self.assertIn("Yacht loses control and rams moored boats in the marina", sk.REMOVED_EVENTS)
        self.assertNotIn("Tidal wave surges over a coastal city street", sk.REMOVED_EVENTS)
        for e in ("Coastal evacuation", "Jammed throttle sends the boat careening",
                  "Heavy roll tilts the deck and sends loungers sliding", sk.ALL_EVENTS[3]):
            self.assertIn(e, sk.REMOVED_EVENTS)   # ALL_EVENTS[3] = yandan indirme
        self.assertTrue(sk.ALL_EVENTS[3].startswith("Side launch"))

    def test_phenomena(self):
        self.assertEqual({k: len(v) for k, v in sk.PHENOMENA.items()},
                         {"Hortum": 4, "Tsunami": 0, "Sel": 1, "Heyelan": 3, "Dev Dalga": 5})
        for events in sk.PHENOMENA.values():
            self.assertTrue(set(events) <= set(sk.EVENT_SKELETONS))


class TestSkeletonOutput(unittest.TestCase):
    def test_every_filled_skeleton(self):
        n = 0
        for e, ship, slots in _combos():
            n += 1
            with self.subTest(event=e, ship=ship, slots=slots):
                self.assertEqual(sk.validate_slots(e, ship, slots), [])
                story = sk.fill_skeleton(e, ship, slots)
                self.assertNotIn("{", story)
                self.assertTrue(35 <= len(story.split()) <= 70, len(story.split()))
                self.assertEqual(pg.event_fidelity_issues(e, story), [])
                self.assertTrue(pg.validate_beat3_ongoing_danger({"visible_consequence": story.split(". ")[-1]})[0])
                if ship:
                    self.assertIn(sk.SHIP_PHRASES[ship], story)
                suffix = sk.style_suffix(e, ship, slots["spot"])
                total, negative = count_constraints(suffix)
                self.assertLessEqual(total, 8, suffix)
                self.assertIn("Handheld footage shot by a person standing", suffix)
                self.assertIn("the camera pans to follow the", suffix)
                self.assertNotIn("phone", suffix.lower())   # final turu: telefon/REC ekranı çiziliyordu
                self.assertIn("no zoom, no cuts", suffix)
                self.assertIn("Raw natural light matching the weather, never glossy or CGI", suffix)
                self.assertTrue("wear" in suffix)   # kıyafet satırı korunur
                for removed in ("fully in frame", "fisheye", "hands or fingers", "bow-first", "fixed position",
                                "Already moving in the first frame", "Nobody pushes", "second ship"):
                    self.assertNotIn(removed, suffix)
        self.assertGreater(n, 60)

    def test_final_test_events_ship_rules(self):
        self.assertEqual(sk.EVENT_SKELETONS["Restraining cable snaps during slipway launch"]["ships"], ["Luxury Motor Yacht"])
        self.assertIsNone(sk.EVENT_SKELETONS["Flash flooding in city streets"]["ships"])


class TestSlots(unittest.TestCase):
    E = "Rogue wave breaks over the rail onto the pool deck"

    def test_validation_errors(self):
        good = _valid_slots(self.E, "Ocean Cruise Liner")
        self.assertEqual(sk.validate_slots(self.E, "Ocean Cruise Liner", good), [])
        for key, bad in (("spot", "Sun deck"), ("weather", "sunny"), ("people", "pirates"), ("count", 99),
                         ("count", "many")):
            with self.subTest(key=key):
                errs = sk.validate_slots(self.E, "Ocean Cruise Liner", dict(good, **{key: bad}))
                self.assertTrue(any(e.startswith(key) for e in errs), errs)

    def test_retry_with_feedback_then_ok(self):
        good = _valid_slots(self.E, "Ocean Cruise Liner")
        gpt = AsyncMock(side_effect=[dict(good, spot="Sun deck"), good])
        slots, attempts = asyncio.run(sk.fill_slots(self.E, "Ocean Cruise Liner", [], gpt))
        self.assertEqual(slots["spot"], good["spot"])
        self.assertEqual(len(attempts), 2)
        self.assertIn("INVALID", gpt.await_args_list[1].args[1])
        self.assertEqual(gpt.await_args.kwargs["model"], "gpt-4o-mini")

    def test_two_invalid_raises(self):
        gpt = AsyncMock(return_value={"spot": "x", "weather": "y", "people": "z", "count": 0})
        with self.assertRaises(sk.SlotFillError):
            asyncio.run(sk.fill_slots(self.E, "Ocean Cruise Liner", [], gpt))


class TestChoose(unittest.TestCase):
    def test_forced_event(self):
        d, e, ship = sk.choose_event_and_ship(None, "Restraining cable snaps during slipway launch", [])
        self.assertEqual((d, ship), ("shipyard_and_drydock_engineering", "Luxury Motor Yacht"))

    def test_removed_or_mismatched_event_rejected(self):
        with self.assertRaises(ValueError):
            sk.choose_event_and_ship(None, "Coastal evacuation", [])
        with self.assertRaises(ValueError):
            sk.choose_event_and_ship("ferry_operations", "Flash flooding in city streets", [])

    def test_random_event_is_lru(self):
        d = "urban_city_disasters"
        hist = [f"{d}|none|flash flooding in city streets|downtown city center|bystander_handheld"]
        for _ in range(10):
            _, e, ship = sk.choose_event_and_ship(d, None, hist)
            self.assertEqual(e, "Tidal wave surges over a coastal city street")
            self.assertIsNone(ship)


def _fake_gpt():
    async def call(system, user, temperature=0.85, model="gpt-4o"):
        if "fill the blanks" in system:
            event = user.split("EVENT: ", 1)[1].split("\n", 1)[0]
            ship = user.split("VESSEL: ", 1)[1].split("\n", 1)[0]
            return _valid_slots(event, None if ship == "none" else ship)
        return {"youtube_title": "⚠️ Test #Shorts", "youtube_description": "d", "tags": ["x"]}
    return AsyncMock(side_effect=call)


class TestGeneratePrompts(unittest.TestCase):
    def run_gen(self, config, pipeline="skeleton"):
        gpt = _fake_gpt()
        legacy = AsyncMock(return_value={"legacy": True})
        writer = AsyncMock(side_effect=AssertionError("iskelet hattında yazıcı çağrılmamalı"))
        with patch.object(settings, "IS_DRY_RUN", False), patch.object(settings, "PROMPT_PIPELINE", pipeline), \
             patch.object(pg, "_call_gpt", gpt), patch.object(pg, "generate_legacy_prompts", legacy), \
             patch.object(pg, "_generate_scenario", writer):
            return asyncio.run(pg.generate_prompts(config)), gpt, legacy

    def test_skeleton_selectable_by_switch(self):
        # TUR 31: varsayılan "creative"; iskelet hattı anahtarla seçilir (test_tur31_creative varsayılanı sınar)
        from config import Config
        with patch.dict(os.environ, {"PROMPT_PIPELINE": "skeleton"}, clear=False):
            self.assertEqual(Config().PROMPT_PIPELINE, "skeleton")

    def test_skeleton_output_shape(self):
        event = "Flash flooding in city streets"
        r, gpt, legacy = self.run_gen({"used_combos": [], "recent_topics": [], "domain": "urban_city_disasters",
                                       "event": event})
        legacy.assert_not_awaited()
        scene = r["scenes"][0]
        self.assertEqual(scene["prompt"], f"{scene['story'].rstrip('.')}. {scene['style_suffix']}")
        self.assertIsNone(r["gate_context"])
        self.assertEqual(r["scenario_text"], scene["story"])
        self.assertEqual(r["selection"]["camera"], "bystander_handheld")
        self.assertTrue(is_current_universe_combo(r["combo_key"]))
        self.assertEqual(r["trace"]["pipeline"], "skeleton")
        self.assertEqual([c.kwargs.get("model", "gpt-4o") for c in gpt.await_args_list], ["gpt-4o-mini", "gpt-4o"])

    def test_legacy_switch(self):
        r, _, legacy = self.run_gen({"used_combos": []}, pipeline="legacy")
        self.assertEqual(r, {"legacy": True})
        r, _, legacy = self.run_gen({"used_combos": [], "prompt_pipeline": "legacy"}, pipeline="skeleton")
        self.assertEqual(r, {"legacy": True})

    def test_unknown_pipeline(self):
        with self.assertRaises(ValueError):
            self.run_gen({"used_combos": []}, pipeline="bilinmiyor")

    def test_trace_sections(self):
        r, _, _ = self.run_gen({"used_combos": [], "event": "Rogue wave breaks over the rail onto the pool deck"})
        text = "\n".join(t + "\n" + b for t, b in format_generation(r["trace"]))
        for part in ("iskelet", "gpt-4o-mini", r["scenes"][0]["story"], "✅ geçerli"):
            self.assertIn(part, text)


class TestPipelineWithSkeleton(unittest.TestCase):
    def test_event_check_uses_skeleton_story(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        event = "Restraining cable snaps during slipway launch"
        gpt = _fake_gpt()
        tracker = MagicMock()
        tracker.page_id = None
        tracker.get_recent_history.return_value = []
        tracker.get_recent_beat1_verbs.return_value = []
        create = AsyncMock(return_value="t1")

        def download(url):
            fd, p = tempfile.mkstemp(suffix=".mp4")
            os.write(fd, b"\0" * 2048)
            os.close(fd)
            return p
        with patch.object(settings, "IS_DRY_RUN", False), patch.object(settings, "PROMPT_PIPELINE", "skeleton"), \
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
            r = asyncio.run(main.run_pipeline(skip_upload=True, mode="TEST", domain="shipyard_and_drydock_engineering",
                                              event=event, trigger="manual"))
        self.assertTrue(r["success"], r)
        sent = create.await_args.args[1]
        self.assertIn("restraining cable snaps", sent)
        self.assertIn("luxury motor yacht", sent)
        self.assertIn("Handheld footage shot by a person standing on the quay beside the slipway", sent)
        upload.assert_not_awaited()


class TestRecoveryQuery(unittest.TestCase):
    def test_unknown_select_option_does_not_break_recovery(self):
        # 29 Eyl ilk açılış: "✋ Onay Bekliyor" seçeneği veritabanında yokken filtre 400 verdi, kurtarma çalışmadı
        from infrastructure import notion_logger as nl
        page = {"id": "p1", "properties": {"Durum": {"select": {"name": "Video Üretiliyor"}},
                                           "Kie Task ID": {"rich_text": [{"plain_text": "t1"}]}}}
        req = MagicMock(side_effect=[{"results": [page]},
                                     RuntimeError('Notion API hatası: 400 — select option "✋ Onay Bekliyor" not found')])
        with patch.object(settings, "NOTION_ENABLED", True), patch.object(settings, "IS_DRY_RUN", False), \
             patch.object(nl, "_notion_request", req):
            out = nl.NotionTracker.find_by_status(["Video Üretiliyor", "✋ Onay Bekliyor"])
        self.assertEqual([(r["page_id"], r["task_id"]) for r in out], [("p1", "t1")])

    def test_other_notion_errors_still_raise(self):
        from infrastructure import notion_logger as nl
        req = MagicMock(side_effect=RuntimeError("Notion API hatası: 401 — unauthorized"))
        with patch.object(settings, "NOTION_ENABLED", True), patch.object(settings, "IS_DRY_RUN", False), \
             patch.object(nl, "_notion_request", req):
            with self.assertRaises(RuntimeError):
                nl.NotionTracker.find_by_status(["Video Üretiliyor"])


class TestMenu(unittest.TestCase):
    def test_menu_follows_pipeline(self):
        with patch.object(settings, "PROMPT_PIPELINE", "skeleton"):
            self.assertEqual(sum(len(bot.domain_events(d)) for d in DOMAIN_ATTRIBUTES), 24)   # 2 Eki: + 3 heyelan
        with patch.object(settings, "PROMPT_PIPELINE", "legacy"):
            # 30 Eyl: dev dalga baskını havuza eklendi (tabela/iskele havuzda kaldı, sadece iskeletten çıktı)
            # 1 Eki: kontrolsüz yat havuza eklendi (halat havuzda kaldı, sadece iskeletten çıktı)
            # 2 Eki: + 3 heyelan; 4 Eki (TASLAK): + hortum marina, sahil caddesi
            self.assertEqual(sum(len(bot.domain_events(d)) for d in DOMAIN_ATTRIBUTES), 46)


if __name__ == "__main__":
    unittest.main()
