#!/usr/bin/env python3
"""Açılış ekseni (21 Eki 2026, Gece 1 / Aşama 6): 18 olayda kilit cümle varyantları.

- A = bugünkü kilit cümle kelimesi kelimesine (spec, stil eki, prompt birebir); ateş hortumunda eksen yok.
- B/C/D olaya özel dil kurallarını geçer: ilk cümlede tetik (a), olay adından en az 2 kök (e), yasak kelime (çığ/deprem
  araç vb.), volkanda "rain" yok, kamera kelimesi yok.
- Son 2 hariç LRU; ortamla çelişen açılış (KEY_VISUAL_CONFLICTS dahil) seçilmez; beat çakışması aynı üretimde seçilmez.
- Seçilen açılış GPT mesajında kilit cümle, kod yedeğinde 0-4 sn cümlesi. Bütçe: tüm kombinasyonlar sığar.
GPT/Kie/Notion yok.
"""
import collections
import json
import logging
import os
import random
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import core.event_structure as es   # noqa: E402  (önce: döngüsel import sırası)
import core.axes_history as ah   # noqa: E402
import core.creative_pipeline as cp   # noqa: E402
import core.opening_axis as ox   # noqa: E402
import core.scene_env as sv   # noqa: E402
import core.skeleton_pipeline as sk   # noqa: E402
import prompt_snapshot as ps   # noqa: E402
from core.prompt_generator import _event_stems, text_event_stems   # noqa: E402

# 29 Eki: meteorda açılış ekseni yok (kilit cümle Bahadır'ın metni birebir, her üretimde aynı)
EVENTS = [e for e in ps.active_events() if e not in (es.FIRE_TORNADO, es.METEOR)]


class TestData(unittest.TestCase):
    def test_eighteen_events_fire_tornado_excluded(self):
        self.assertEqual(set(ox.OPENINGS), set(EVENTS))
        self.assertEqual(len(EVENTS), 18)
        self.assertNotIn(es.FIRE_TORNADO, ox.OPENINGS)
        for e in EVENTS:
            self.assertEqual(ox.options(e), ["A", "B", "C", "D"])
            self.assertIsNone(ox.text(e, "A"))

    def test_openings_pass_language_rules(self):
        for e, ops in ox.OPENINGS.items():
            key = _event_stems(e)
            for letter, t in ops.items():
                with self.subTest(event=e, opening=letter):
                    self.assertTrue(t.endswith(".") and "\n" not in t)
                    groups = cp.EVENT_REQUIRED[e]
                    self.assertTrue(cp.trigger_stems(e) & text_event_stems(t)
                                    or (groups and es.find_terms(groups[0], t)), "a: ilk cümlede tetik")
                    self.assertGreaterEqual(len(key & text_event_stems(t)), min(2, len(key)), "e: olay adı kökü")
                    for code, terms, *_ in es.EVENT_BANNED_WORDS.get(e, ()):
                        self.assertEqual(es.find_terms(terms, t), [], code)
                    if e in es.NO_RAIN_EVENTS:
                        self.assertEqual(es.rain_words(t), [])
                    self.assertEqual(es.find_terms(cp.CAMERA_WORDS, t), [])
                    self.assertEqual(es.find_terms(es.HARD_CAMERA_EXTRA, t), [])
                    self.assertEqual(es.find_terms(cp.SCALE_REDUCERS, t), [])

    def test_changed_openings_recorded(self):
        for (e, letter), orig in ox.ORIGINAL.items():
            self.assertNotEqual(ox.OPENINGS[e][letter], orig)
        self.assertIn("car park", ox.ORIGINAL[(es.AVALANCHE_SKI, "D")])


class TestAVerbatim(unittest.TestCase):
    def test_a_spec_identical(self):
        for e in EVENTS:
            view = es.structure_views(e)[0]
            spot = sk.view_spots(e, view)[0]
            b2, b3 = sorted(es.allowed_pairs(e, view, spot))[0]
            veh = es.event_vehicles(e, view)[0][0] if es.uses_vehicle(e) else None
            ppl = sk.count_range(e, None)[0] if es.has_people_rule(e) else None
            with_a = es.build_spec(e, None, spot, view, b2, b3, veh, ppl, opening="A")
            plain = es.build_spec(e, None, spot, view, b2, b3, veh, ppl)
            self.assertEqual(with_a["key_visual"], es.EVENT_KEY_VISUAL[e])
            self.assertEqual({k: v for k, v in with_a.items() if k != "opening"}, plain)

    def test_opening_flows_to_key_visual(self):
        e = es.TIDAL
        spot = sk.view_spots(e, "riviera")[0]
        spec = es.build_spec(e, None, spot, "riviera", "T2", "W3", "large SUV", 4, opening="C")
        self.assertEqual(spec["key_visual"], ox.OPENINGS[e]["C"])
        msg = cp._slices_message(spec, "P", "W", 3, 6, [], None)
        self.assertIn(f"OPENING SENTENCE (fixed, already written): {ox.OPENINGS[e]['C']}", msg)
        sl = es.build_fallback(spec, random.Random(1))
        self.assertTrue(es.assemble_story(spec, sl).startswith(f"0-4s: {ox.OPENINGS[e]['C']}"))
        self.assertEqual(es.final_prompt_issues(spec, sl, es.assemble_prompt(spec, sl), es.assemble_story(spec, sl)), [])
        wrong = dict(spec, opening="B")
        self.assertIn("key_visual", [i["rule"] for i in es.final_prompt_issues(
            wrong, sl, es.assemble_prompt(spec, sl), es.assemble_story(spec, sl))])


class TestSelection(unittest.TestCase):
    def test_lru_last_two(self):
        e = es.MUDSLIDE
        for i in range(40):
            got, _ = ox.choose(e, "A", "H1", "M1", ["B", "C"], random.Random(i))
            self.assertIn(got, ("A", "D"))

    def test_key_visual_conflicts_never_selectable(self):
        for e, envs in sv.KEY_VISUAL_CONFLICTS.items():
            self.assertTrue(envs <= ox.A_ENV_CONFLICTS[e], e)
        for e, envs in ox.A_ENV_CONFLICTS.items():
            for env in envs:
                self.assertFalse(ox.env_compatible(e, "A", env))
                for b2, b3 in es.allowed_pairs(e, None, sk.view_spots(e, None)[0]):
                    self.assertNotIn("A", ox.allowed(e, env, b2, b3))
        for e, table in ox.OPENING_ENV_EXCLUDE.items():
            for letter, envs in table.items():
                for env in envs:
                    self.assertFalse(ox.env_compatible(e, letter, env))

    def test_beat_conflicts_blocked(self):
        self.assertIn("V5", ox.beat_conflicts(es.FLOOD, "B"))   # açılış arabaları yan yatırır, V5 de aynısı
        for e in EVENTS:
            b = es.EVENT_BEATS[e]
            for letter in ("B", "C", "D"):
                for bid in ox.beat_conflicts(e, letter):
                    self.assertTrue(bid in b["slice_2"] or bid in b["slice_3"])
                    for b2 in b["slice_2"]:
                        for b3 in b["slice_3"]:
                            if bid in (b2, b3):
                                self.assertNotIn(letter, ox.allowed(e, "A", b2, b3))

    def test_env_a_always_has_an_opening(self):
        for e in EVENTS:
            for view in es.structure_views(e):
                for spot in sk.view_spots(e, view):
                    for b2, b3 in es.allowed_pairs(e, view, spot):
                        self.assertIn("A", ox.allowed(e, "A", b2, b3), (e, b2, b3))


class TestPipeline(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.WARNING)
        ps.reset_memory()

    def tearDown(self):
        logging.disable(logging.NOTSET)
        ps.reset_memory()

    def test_scenes_carry_opening(self):
        for e in (es.FLOOD, es.LANDFALL, es.AVENUE, es.AVALANCHE_SKI, es.EARTHQUAKE_OLD_STREET, es.VOLCANIC_BOMBS):
            seen = collections.Counter()
            for seed in range(30):
                random.seed(seed)
                scene = ps.build(e)
                st, ax = scene["structure"], scene["structure"]["axes"]
                op = ax["acilis"]
                seen[op] += 1
                expected = ox.text(e, op) or es.EVENT_KEY_VISUAL[e]
                self.assertEqual(st["spec"]["key_visual"], expected)
                self.assertTrue(scene["prompt"].startswith(f"0-4s: {expected}"))
                self.assertTrue(ox.env_compatible(e, op, ax.get("ortam")))
                self.assertFalse({st["spec"]["beat_2"], st["spec"]["beat_3"]} & ox.beat_conflicts(e, op))
                self.assertIn("açılış=", st["axes_line"])
                self.assertEqual(json.loads(scene["axes_json"])["axes"]["acilis"], op)
                self.assertEqual(es.final_prompt_issues(st["spec"], st["slices"], scene["prompt"], scene["story"]), [])
            # 31 Eki (3): rotasyonda A + koruma harfi (core.proven_axes); diğerleri DENEME
            import core.proven_axes as pa
            self.assertEqual(set(seen), {"A", pa.GUARD["acilis"][e][0]}, e)
        self.assertIn("acilis", ah.AXIS_KEYS)

    def test_notion_history_drives_opening(self):
        e = es.EARTHQUAKE_APARTMENT
        spot = sk.view_spots(e, None)[0]
        rec = lambda letter: {"combo_key": f"earthquake_disasters|none|{e.lower()}|{spot.lower()}##P1+Q1|c",
                              "eksenler": ah.axes_json(e, {"spot": spot, "acilis": letter}), "status": "❌ İptal"}
        # 31 Eki (3): rotasyonda A + koruma B (en fazla %20); son açılış koruma ise sıradaki A, koruma art arda gelmez
        for seed in range(15):
            random.seed(seed)
            scene = ps.build(e, axes_loader=lambda d: [rec("A"), rec("B")])
            self.assertEqual(scene["structure"]["axes"]["acilis"], "A")

    def test_fire_tornado_unchanged(self):
        random.seed(3)
        scene = ps.build(es.FIRE_TORNADO)
        self.assertIsNone(scene["structure"]["axes"]["acilis"])
        self.assertNotIn("opening", scene["structure"]["spec"])


class TestBudget(unittest.TestCase):
    def test_every_combination_fits_and_passes(self):
        import frame_budget as fb
        logging.disable(logging.WARNING)
        try:
            for e in (es.FLOOD, es.AVALANCHE_VILLAGE, es.EARTHQUAKE_APARTMENT, es.SLOPE):
                with self.subTest(event=e):
                    m = fb.measure(e)
                    self.assertEqual(m["after_fail"], 0)
                    self.assertEqual(m["gate_fail"], 0)
        finally:
            logging.disable(logging.NOTSET)


if __name__ == "__main__":
    unittest.main()
