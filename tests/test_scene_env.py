#!/usr/bin/env python3
"""Ortam ekseni (9 olay) + ışık kapsamı + kelime tavanı (21 Eki 2026, Gece 1 / Aşama 5).

- Ortam: A = bugünkü görünüm birebir; B-E Bahadır'ın metinleri (ülke adı yok); Setting satırı + GPT PLACE; son 2 hariç;
  Notion "ortam".
- Uyum: çelişen spot × ortam seçilmez, kadraj çelişen noktayı ödünç almaz; her ortamda en az 2 kadraj tipi.
- Işık: her olayda sabah, öğle, gün batımı, kapalı/fırtına; yangında gün batımı ağırlığı 2; volkanda "rain" yok; son 2.
- Tavan: sel ve kıyı dalga 175 kelime (GPT bütçesi stil ekine göre + kod yedeği).
- Stil ekinde en fazla 8 kısıt. GPT/Kie/Notion yok.
"""
import collections
import json
import logging
import os
import random
import re
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import core.event_structure as es   # noqa: E402  (önce: döngüsel import sırası)
import core.axes_history as ah   # noqa: E402
import core.frame_axis as fx   # noqa: E402
import core.scene_env as sv   # noqa: E402
import core.skeleton_pipeline as sk   # noqa: E402
import prompt_rules as pr   # noqa: E402
import prompt_snapshot as ps   # noqa: E402
from core.trace_format import count_constraints   # noqa: E402

NINE = (es.MUDSLIDE, es.SLOPE, es.VILLAGE, es.LANDFALL, es.MARINA_TORNADO, es.AVENUE, es.WILDFIRE, es.FACADE_FIRE,
        es.HELICOPTER)
COUNTRIES = ("turkey", "türkiye", "greece", "italy", "spain", "france", "japan", "china", "india", "usa", "america",
             "mexico", "brazil", "morocco", "portugal", "california", "florida", "bali", "thailand", "vietnam",
             "indonesia", "philippines", "switzerland", "austria", "peru", "chile")


class _Quiet(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.WARNING)
        ps.reset_memory()

    def tearDown(self):
        logging.disable(logging.NOTSET)
        ps.reset_memory()


class TestEnvData(unittest.TestCase):
    def test_nine_events_four_new_envs(self):
        self.assertEqual(set(sv.SCENE_ENVS), set(NINE))
        for e in NINE:
            self.assertEqual(sv.env_options(e), ["A", "B", "C", "D", "E"])

    def test_texts_verbatim_spot_checks(self):
        # 21 Eki (genel kalite): 175 için kısa (önceki: "a steep hillside town of pastel concrete houses with tin
        # roofs, banana trees and tangled power lines")
        self.assertEqual(sv.SCENE_ENVS[es.MUDSLIDE]["B"], "a steep town of pastel concrete houses with tin roofs and "
                                                          "banana trees")
        self.assertEqual(sv.SCENE_ENVS[es.FACADE_FIRE]["E"], "a 1970s concrete housing estate with long balcony "
                                                              "corridors and a playground")
        self.assertEqual(sv.SCENE_ENVS[es.HELICOPTER]["C"], "a lakeside town of houses below wooded hills")

    def test_no_country_names(self):
        for e, envs in sv.SCENE_ENVS.items():
            for t in envs.values():
                for c in COUNTRIES:
                    self.assertIsNone(re.search(rf"\b{c}\b", t.lower()), (e, t, c))

    def test_env_a_is_todays_suffix(self):
        for e in NINE:
            for spot in sk.view_spots(e, None):
                for f in fx.all_frames(e, spot, sk.view_spots(e, None))[:4]:
                    self.assertEqual(sk.style_suffix(e, None, spot, frame=f, scene_env="A"),
                                     sk.style_suffix(e, None, spot, frame=f))

    def test_setting_line_and_constraints(self):
        for e in NINE:
            for spot in sk.view_spots(e, None):
                for env in sv.compatible_envs(e, spot):
                    for f in fx.all_frames(e, spot, sk.view_spots(e, None), blocked=sv.excluded_positions(e, env)):
                        suffix = sk.style_suffix(e, None, spot, frame=f, scene_env=env)
                        total, _ = count_constraints(suffix)
                        self.assertLessEqual(total, 8, (e, env, suffix))
                        if env != "A":
                            self.assertIn(f"Setting: {sv.env_text(e, env)}", suffix)
                            self.assertEqual(suffix.count("no readable signs") + suffix.count("No readable signs"),
                                             1 if sk.EVENT_SKELETONS[e]["domain"] in sk.NO_SIGNS_DOMAINS else 0)


class TestCompat(unittest.TestCase):
    def test_every_env_keeps_two_frames(self):
        for e in NINE:
            for env in sv.env_options(e):
                bl = sv.excluded_positions(e, env)
                spots = [s for s in sk.view_spots(e, None) if s not in bl]
                self.assertTrue(spots, (e, env))
                for s in spots:
                    types = {f["type"] for f in fx.all_frames(e, s, sk.view_spots(e, None), blocked=bl)}
                    self.assertGreaterEqual(len(types), 2, (e, env, s))

    def test_incompatible_never_selected(self):
        for e, table in sv.ENV_EXCLUDE.items():
            for env, positions in table.items():
                for spot in positions:
                    if spot.startswith("lib:"):
                        continue
                    for i in range(30):
                        letter, _ = sv.choose_env(e, spot, [], random.Random(i))
                        self.assertNotEqual(letter, env, (e, spot))
                bl = sv.excluded_positions(e, env)
                for spot in sv.view_spots_ok(e, env) if hasattr(sv, "view_spots_ok") else \
                        [s for s in sk.view_spots(e, None) if s not in bl]:
                    for i in range(20):
                        f, _ = fx.choose_frame(e, spot, sk.view_spots(e, None), set(), [], random.Random(i), bl)
                        self.assertNotIn(f["pos_spot"], bl)
                        if f["pos_spot"] is None:
                            self.assertNotIn(f"lib:{f['type']}", bl)

    def test_key_visual_conflicts_listed(self):
        self.assertEqual(sv.KEY_VISUAL_CONFLICTS, {es.AVENUE: {"B", "C", "E"}, es.MARINA_TORNADO: {"E"},
                                                   es.FACADE_FIRE: {"C"}})


class TestEnvSelection(_Quiet):
    def test_env_lru_last_two(self):
        e, spot = es.MUDSLIDE, "Balcony across a steep hillside street"
        for i in range(40):
            letter, _ = sv.choose_env(e, spot, ["B", "C"], random.Random(i))
            self.assertNotIn(letter, ("B", "C"))

    def test_scene_axes_and_place(self):
        seen = collections.Counter()
        for seed in range(40):
            random.seed(seed)
            scene = ps.build(es.WILDFIRE)
            ax = scene["structure"]["axes"]
            self.assertIn(ax["ortam"], sv.env_options(es.WILDFIRE))
            seen[ax["ortam"]] += 1
            if ax["ortam"] != "A":
                self.assertEqual(scene["structure"]["place"], sv.env_text(es.WILDFIRE, ax["ortam"]))
                self.assertIn(sv.env_text(es.WILDFIRE, ax["ortam"]), scene["prompt"])
            data = json.loads(scene["axes_json"])
            self.assertEqual(data["axes"]["ortam"], ax["ortam"])
            self.assertEqual(es.final_prompt_issues(scene["structure"]["spec"], scene["structure"]["slices"],
                                                    scene["prompt"], scene["story"]), [])
        self.assertEqual(len(seen), 5)
        self.assertIn("ortam", ah.AXIS_KEYS)

    def test_notion_history_drives_env(self):
        e = es.HELICOPTER
        spot = "Balcony of a hillside house"
        rec = lambda letter: {"combo_key": f"fire_disasters|none|{e.lower()}|{spot.lower()}##F1+G1|c",
                              "eksenler": ah.axes_json(e, {"spot": spot, "ortam": letter}), "status": "❌ İptal"}
        for seed in range(15):
            random.seed(seed)
            scene = ps.build(e, axes_loader=lambda d: [rec("D"), rec("A")])
            self.assertNotIn(scene["structure"]["axes"]["ortam"], ("D", "A"))


class TestLight(_Quiet):
    def full_lights(self, e):
        if e in es.AVALANCHE_EVENTS:
            return list(es.ENV_AXES["light"]) + list(sv.ENV_LIGHT_ADD["avalanche"])
        if e in es.EARTHQUAKE_EVENTS:
            return list(es.EQ_ENV_AXES["light"]) + list(sv.ENV_LIGHT_ADD["earthquake"])
        base = list(es.VOLCANO_WEATHER_WEIGHTS[e]) if e in es.VOLC_ENV_EVENTS else list(sk.EVENT_SKELETONS[e]["weather"])
        return base + [x for x in sv.LIGHT_ADD[e] if x not in base]

    def test_every_event_covers_four_conditions(self):
        for e in ps.active_events():
            cats = set().union(*(sv.light_category(t) for t in self.full_lights(e)))
            self.assertEqual(cats, set(sv.LIGHT_CATEGORIES), e)

    def test_existing_lights_kept(self):
        for e in ps.active_events():
            if e in sv.LIGHT_ADD:
                old = list(es.VOLCANO_WEATHER_WEIGHTS[e]) if e in es.VOLC_ENV_EVENTS else sk.EVENT_SKELETONS[e]["weather"]
                self.assertTrue(set(old) <= set(self.full_lights(e)))

    def test_fire_sunset_weight_two(self):
        for e in sv.FIRE_EVENTS:
            for t in self.full_lights(e):
                self.assertEqual(sv.light_weight(e, t), 2 if "gün batımı" in sv.light_category(t) else 1)
        self.assertEqual(sv.light_weight(es.FLOOD, "orange sunset light under breaking storm clouds"), 1)

    def test_volcano_no_rain(self):
        for e in es.VOLC_ENV_EVENTS:
            for t in self.full_lights(e):
                self.assertIsNone(pr.RAIN_RE.search(t), t)

    def test_light_lru_last_two(self):
        e = es.FLOOD
        opts = self.full_lights(e)
        for i in range(40):
            got, _ = sv.choose_light(e, opts, opts[:2], random.Random(i))
            self.assertNotIn(got, opts[:2])

    def test_selected_light_from_full_list(self):
        for e in (es.FLOOD, es.WILDFIRE, es.AVALANCHE_SKI, es.EARTHQUAKE_APARTMENT, es.VOLCANIC_BOMBS):
            for seed in range(10):
                random.seed(seed)
                scene = ps.build(e)
                self.assertIn(scene["structure"]["axes"]["light"], self.full_lights(e), e)


class TestWordCap(unittest.TestCase):
    def test_flood_tidal_capped(self):
        for e in (es.FLOOD, es.TIDAL):
            self.assertIn(e, es.WORD_CAP_EVENTS)
            self.assertIn(e, es.CAP_BUDGET_EVENTS)
            self.assertIn(e, es.BUDGET_EVENTS)

    def test_gpt_budget_feasible_for_every_suffix(self):
        lo = sum(es.SLICE_WORDS[f][0] for f in es.SLICE_FIELDS)
        for e in (es.FLOOD, es.TIDAL):
            key = len(es.EVENT_KEY_VISUAL[e].split())
            for item in pr.camera_items()[e].values():
                budget = es.VOLC_MAX_PROMPT_WORDS - 3 - len(item["style_suffix"].split())
                self.assertGreaterEqual(budget, key + lo, (e, item["style_suffix"]))

    def test_all_fallback_combos_fit(self):
        import frame_budget as fb
        logging.disable(logging.WARNING)
        try:
            for e in (es.FLOOD, es.TIDAL):
                self.assertEqual(fb.measure(e)["after_fail"], 0, e)
        finally:
            logging.disable(logging.NOTSET)

    def test_budget_line_uses_suffix(self):
        random.seed(2)
        logging.disable(logging.WARNING)
        try:
            scene = ps.build(es.FLOOD)
        finally:
            logging.disable(logging.NOTSET)
        spec = scene["structure"]["spec"]
        line = es.word_budget_line(spec)
        cap = min(es.TOTAL_WORDS_BY_EVENT.get(es.FLOOD, es.TOTAL_WORDS)[1],
                  es.VOLC_MAX_PROMPT_WORDS - 3 - len(spec["suffix"].split()))
        self.assertIn(f"must total at most {cap} words", line)


if __name__ == "__main__":
    unittest.main()
