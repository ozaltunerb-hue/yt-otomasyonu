#!/usr/bin/env python3
"""4 Kasım 2026, Bahadır: sel düzeltmeleri + sel insan hikâyesi + yeni olay "🗽 Özgürlük Anıtı hortumu". Ağ yok,
Kie/GPT çağrısı yok (sahte GPT).

A1 {vehicle} boşluğu (Seçim satırı, GPT mesajı, kod yedeği, VERBATIM) · A2 (V1, D13) dışlı · A3 dev dalga insan
cümlesi VERBATIM · A4 sel hikâye ekseni H1-H5 (kısa hâl, 4 Kas (2) Bahadır kararı) · A5 kameraya yakınlık · A6 sel
tavanı 215 / 1400 karakter, 11 bütçe çifti dışlı · A7 iyi video kaydı.
B1-B12 Özgürlük Anıtı: yapı, OZGURLUK_DOGRULAMA, kilit cümle, havuzlar (B4, B6, C5 kabul listesinden geçmedi), kadraj,
ışık, araç, insan, ortam (kısa hâl, tavan 205: Bahadır kararı), kapı, kabul listesi.
"""
import asyncio
import collections
import json
import logging
import os
import random
import re
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (ROOT, os.path.join(ROOT, "scripts"), os.path.join(ROOT, "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import prompt_snapshot as ps   # noqa: E402
import core.creative_pipeline as cp   # noqa: E402
import core.event_structure as es   # noqa: E402
import core.frame_axis as fx   # noqa: E402
import core.opening_axis as ox   # noqa: E402
import core.skeleton_pipeline as sk   # noqa: E402
from core.creative_engine import DOMAIN_ATTRIBUTES   # noqa: E402
from test_toplu_3kas import _sequence   # noqa: E402

F, T, L = es.FLOOD, es.TIDAL, es.LIBERTY
L2 = "Water rises past the car windows and races toward the camera."
L3 = "A second surge, first-floor high, slams in."
FINALS = {
    "D10": "the current shoves parked cars into a shopfront in the street right below the camera and its wall caves in",
    "D12": "the current piles a row of parked cars against the front of a shop in the street right below the camera",
    "D13": "the street right below the camera becomes a fast brown river and the {vehicle} is carried away toward the "
           "intersection",
    "D14": "the current shoves a city bus into a shopfront right below the camera",   # 4 Kas (2)
    "D15": "the flood bursts open a row of shop shutters and pours into the stores",
    "D16": "the surge tears the ground-floor fronts off the shops across the street",
    "D17": "the surge tips a city bus onto its side in the street right below the camera and pushes it along",
    "D18": "the surge slams the {vehicle} into the shopfront right below the camera",   # 4 Kas (2)
}
# 4 Kas (2/3): yeniden ölçümden sonra dışlı kalan bütçe çiftleri; sığan 8'i ve V11'in tüm dışlamaları kalktı
BUDGET_PAIRS = {("V9", "D13"), ("V9", "D12")}
FREED_PAIRS = {("V9", "D18"), ("V1", "D18"), ("V1", "D14"), ("V12", "D18"), ("V10", "D14"), ("V12", "D14"),
               ("V2", "D18"), ("V2", "D14")} | {("V11", d) for d in ("D10", "D12", "D13", "D14", "D15", "D16", "D17")}
# 4 Kas (3): (V11, D18) yeniden dışlandı (aynı araç iki dilimde de çarpıyor); test_sel_ozgurluk_4kas_3.py
K = ("Rooftop terrace of a Lower Manhattan high-rise facing the harbor",
     "High apartment balcony in Battery Park City looking across the harbor",
     "Top-floor terrace of a waterfront hotel next to Battery Park")
STATUE = "the Statue of Liberty standing intact in the distance across the harbor"
KEY = ("A colossal wedge tornado, far wider than Liberty Island, tears across New York Harbor past the Statue of "
       "Liberty, ripping spray off the water, and slams into the Battery Park waterfront promenade.")
B_POOL = {"B1": "tears the roof off the ferry terminal and hurls the metal sheets across the road",
          "B2": "rips the tall park trees out by the roots and throws them across the lawn",
          "B3": "smashes the waterfront café pavilion apart and flings its walls into the street",
          "B4": "shoves the {vehicle} across the road and slams it into the seawall",   # 4 Kas (2)
          "B5": "strips the scaffolding off a building front and throws it into the street",
          "B6": "shoves a city bus across the road and slams it into the side of the ferry terminal"}
C_POOL = {"C1": "crosses onto the avenue directly below the camera, tearing out the street trees and blasting debris "
                "against the building fronts",
          "C2": "tears the entire roof off the low brick building below and hurls it across the avenue",
          "C3": "tips a delivery truck onto its side in the middle of the avenue and drags it along",
          "C4": "collapses the front wall of the old waterfront warehouse into the street",
          "C6": "drives the {vehicle} along the avenue and slams it into the building corner below"}
P_LINES = ("{N} people sprint off the waterfront promenade into the building entrances below.",
           "{N} people sprint across the park lawn toward the subway entrance.",
           "{N} people run into the lobby of the building below.")
LIGHTS = ["dark overcast storm afternoon", "green-tinted storm sky", "low late-afternoon sun under black storm clouds"]


class _Quiet(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.WARNING)

    def tearDown(self):
        logging.disable(logging.NOTSET)


def _unlocked():
    return [e for e in ps.active_events() if e not in es.LOCKED_EVENTS]


def _all_specs(event, light=None):
    """Olayın her görünüm × nokta × izinli çift × araç kombinasyonu için bir spec (kişi sayısı aralığın en büyüğü)."""
    lo, hi = sk.count_range(event, None)
    people = hi if es.has_people_rule(event) else None
    for view in es.structure_views(event):
        for spot in sk.view_spots(event, view):
            vehicles = [v for v, _ in es.event_vehicles(event, view)] if es.uses_vehicle(event) else [None]
            for b2, b3 in es.allowed_pairs(event, view, spot):
                for veh in vehicles:
                    yield es.build_spec(event, None, spot, view, b2, b3, veh, people, light=light)


def _lib_spec(b2="B1", b3="C6", spot=K[0], veh="yellow taxi", n=4, light=LIGHTS[0]):
    frame = fx.all_frames(L, spot, [spot])[0]
    return es.build_spec(L, None, spot, None, b2, b3, veh, n, None, None, frame, None, None, light)


async def _gpt(system, msg, **kw):
    return {"slice_1_rest": "Five people run away in the street right below.", "slice_2": "x", "slice_3": "x"}


def _scene(event, seed=1):
    ps.reset_memory()
    random.seed(seed)
    real = cp.record_story_source
    cp.record_story_source = lambda entry: None
    try:
        return asyncio.run(cp.build_creative_scene(None, event, [], [], _gpt))
    finally:
        cp.record_story_source = real


# ══════ BÖLÜM A ══════════════════════════════════════════════════════════════════════════════════════════════════════
class TestA1VehiclePlaceholder(_Quiet):
    def test_every_path_fills_vehicle(self):
        """Kilitsiz her olayda {vehicle} taşıyan her öğe: Seçim satırı, GPT mesajı, kod yedeği, VERBATIM dolu."""
        n = 0
        for e in _unlocked():
            b = es.EVENT_BEATS[e]
            for spec in _all_specs(e):
                for slot, bid in (("slice_2", spec["beat_2"]), ("slice_3", spec["beat_3"])):
                    if "{vehicle}" not in b[slot][bid]["text"]:
                        continue
                    n += 1
                    texts = [es.beat_text(e, slot, bid, spec["vehicle"]), es.fallback_beat_slice(spec, slot),
                             es.apply_verbatim(spec, {"slice_1_rest": "x", "slice_2": "x", "slice_3": "x"})[slot],
                             cp._slices_message(spec, "p", "w", 3, 6, [], None)]
                    for t in texts:
                        self.assertNotIn("{vehicle}", t)
                        self.assertNotRegex(t, r"the  |the \.|  ")
                        self.assertIn(spec["vehicle"], t, (e, bid))
        self.assertGreater(n, 100)

    def test_selection_line_and_message(self):
        spec = es.build_spec(F, None, "Downtown city center", "riviera", "V10", "D13", "red SUV", None)
        msg = cp._slices_message(spec, "p", "w", 3, 6, [], None)
        self.assertIn("9-15s EVENT: the street right below the camera becomes a fast brown river and the red SUV is "
                      "carried away", msg)
        for seed in range(1, 41):
            r = _scene(F, seed) if seed <= 3 else None
            if r is None:
                break
            t = r["trace"]
            self.assertNotIn("the  is", t["beat_3_text"])
            self.assertNotIn("{vehicle}", t["beat_3_text"])

    def test_locked_have_no_vehicle_in_slice_3(self):
        """Kilitli olaylarda aynı hata var mı (rapor): 9-15s'te {vehicle} taşıyan öğe yok (hata kilitlilerde yoktu)."""
        for e in es.LOCKED_EVENTS:
            self.assertFalse([b for b, x in es.EVENT_BEATS[e]["slice_3"].items() if "{vehicle}" in x["text"]], e)


class TestA2Pairs(_Quiet):
    def test_excluded(self):
        ex = es.EVENT_BEATS[F]["excluded_pairs"]
        self.assertIn(("V1", "D13"), ex)
        self.assertIn(("V12", "D13"), ex)
        self.assertIn(("V2", "D13"), ex)   # 4 Kas (2): aynı araç iki kez sürükleniyor
        for view in es.structure_views(F):
            for spot in sk.view_spots(F, view):
                pairs = es.allowed_pairs(F, view, spot)
                self.assertNotIn(("V1", "D13"), pairs)
                self.assertNotIn(("V12", "D13"), pairs)


class TestA3VerbatimPeople(_Quiet):
    def test_tidal_people_line_verbatim(self):
        spec = es.build_spec(T, None, "Coastal street of low shopfronts", "riviera", "T2", "W1", "red SUV", 5)
        for i, t in enumerate(es.FALLBACK_PEOPLE[T]):
            sp = {**spec, "people_line": f"I{i + 1}"}
            out = es.apply_verbatim(sp, {"slice_1_rest": "Five people flee to safety in panic.", "slice_2": "x",
                                         "slice_3": "x"})
            self.assertEqual(out["slice_1_rest"], es.clean_slice(t.format(N="Five")))
            self.assertNotIn("{N}", out["slice_1_rest"])
            bad = {**out, "slice_1_rest": "Five people run away from the wave."}
            self.assertIn("verbatim_people", {i["rule"] for i in es.verbatim_issues(sp, bad)})

    def test_scene_uses_axis_line(self):
        for seed in (1, 2, 3):
            sc = _scene(T, seed)
            spec, sl = sc["structure"]["spec"], sc["structure"]["slices"]
            self.assertEqual(sl["slice_1_rest"], es.people_line_text(spec, sc["structure"]["axes"]["insan"]))

    def test_locked_unchanged(self):
        for e in es.LOCKED_EVENTS:
            self.assertNotIn(e, es.VERBATIM_PEOPLE_EVENTS)
            self.assertNotIn(e, es.PEOPLE_AXIS_EVENTS)
        self.assertEqual(set(es.VERBATIM_PEOPLE_EVENTS), {F, T, L})


class TestA4FloodStories(_Quiet):
    def test_texts(self):
        self.assertEqual(list(es.FLOOD_STORIES), ["H1", "H2", "H3", "H4", "H5"])
        self.assertEqual(es.FLOOD_STORIES["H1"], ("Two people run for the doorway right below the camera.",
                                                  "Waist-deep, they cling to a railing as a shop window bursts.",
                                                  "They climb the steps as the surge bursts the windows behind them."))
        self.assertEqual(es.FLOOD_STORIES["H4"], ("A man pulls a woman toward the shop entrance right below.",
                                                  "Chest-deep, they watch the shop's glass door burst in front of them.",
                                                  "They climb the stone steps as the surge bursts the first-floor windows."))
        self.assertIn("H5", es.FLOOD_STORIES_LONG)   # ilk hâller silinmedi

    def test_slices_carry_story(self):
        spec = es.build_spec(F, None, "Downtown city center", "riviera", "V2", "D17", "red SUV", None)
        for hid, (a, b, c) in es.FLOOD_STORIES.items():
            sp = {**spec, "people_line": hid}
            s2, s3 = es.fallback_beat_slice(sp, "slice_2"), es.fallback_beat_slice(sp, "slice_3")
            self.assertTrue(s2.startswith(L2 + " ") and s2.endswith(" " + b))
            self.assertTrue(s3.startswith(L3 + " ") and s3.endswith(" " + c))
            out = es.apply_verbatim(sp, {"slice_1_rest": "People are swept away.", "slice_2": "x", "slice_3": "x"})
            self.assertEqual(out, {"slice_1_rest": a, "slice_2": s2, "slice_3": s3})
            self.assertEqual(es.final_prompt_issues(sp, out, es.assemble_prompt(sp, out), es.assemble_story(sp, out)),
                             [], hid)

    def test_old_people_axis_passive(self):
        self.assertEqual(len(es.FALLBACK_PEOPLE[F]), 6)   # I1-I6 silinmedi
        spec = es.build_spec(F, None, "Downtown city center", "riviera", "V2", "D17", "red SUV", None)
        self.assertEqual(es.fallback_people_pool(spec), tuple(s[0] for s in es.FLOOD_STORIES.values()))
        self.assertFalse(es.has_people_rule(F))
        self.assertIn(F, es.SLICE_RULES_RETIRED)

    def test_lru_equal_all_trial(self):
        self.assertTrue(es.SEL_DOGRULAMA)
        c = collections.Counter()
        for seed in (1, 2):
            rows = _sequence(F, 60, seed)
            ids = [r["structure"]["axes"]["insan"] for r in rows]
            self.assertFalse([1 for a, b in zip(ids, ids[1:]) if a == b])
            c.update(ids)
        self.assertEqual(set(c), set(es.FLOOD_STORIES))
        for h, k in c.items():
            self.assertTrue(0.10 <= k / sum(c.values()) <= 0.30, (h, k))
        for h in es.FLOOD_STORIES:
            self.assertNotIn(h, es.PEOPLE_AXIS_PROVEN)

    def test_story_lint_exception(self):
        for a, b, c in es.FLOOD_STORIES.values():
            for t in (a, b, c):
                hits = [w for name, ws in es.pool_lint_hits(t) for w in ws
                        if not (name == "ince/uzak hedef" and w in es.STORY_LINT_THIN_OK)]
                self.assertEqual(hits, [], t)
                self.assertEqual(es.people_scatter(t), [])
                self.assertEqual(es.flood_root_words(t), [], t)

    def test_people_loss_gate(self):
        spec = es.build_spec(F, None, "Downtown city center", "riviera", "V10", "D13", "red SUV", None,
                             light="heavy rain")
        sp = {**spec, "people_line": "H3"}
        sl = es.apply_verbatim(sp, {"slice_1_rest": "x", "slice_2": "x", "slice_3": "x"})
        self.assertIn("carried away", sl["slice_3"])   # D13: araç (koddan), insan değil
        self.assertEqual(es.flood_people_loss_issues(sp, sl), [])
        for bad in ("Two people are swept away by the water.", "They are carried away down the street.",
                    "A man drowns in the current.", "The group vanishes under the water.",
                    "Three pedestrians disappear into the flood."):
            with self.subTest(bad=bad):
                self.assertTrue(es.flood_people_loss_issues(sp, {**sl, "slice_1_rest": bad}))
        self.assertEqual(es.flood_people_loss_issues(sp, {**sl, "slice_1_rest": "The red SUV is swept down the street."}),
                         [])


class TestA5Proximity(_Quiet):
    def test_water_lines(self):
        self.assertEqual(es.WATER_LEVEL_LINES[F], {"slice_2": L2, "slice_3": L3})
        self.assertEqual(ox.OPENINGS[F]["A"] if "A" in ox.OPENINGS[F] else es.EVENT_KEY_VISUAL[F],
                         es.EVENT_KEY_VISUAL[F])
        self.assertEqual(es.EVENT_KEY_VISUAL[F], "A waist-high wall of brown muddy floodwater surges into the street.")

    def test_finals(self):
        for bid, text in FINALS.items():
            self.assertEqual(es.EVENT_BEATS[F]["slice_3"][bid]["text"], text)
        self.assertEqual(es.EVENT_BEATS[F]["slice_3"]["D5"]["text"], "a city bus is shoved sideways by the current")

    def test_camera_word_only_from_code(self):
        spec = {**es.build_spec(F, None, "Downtown city center", "riviera", "V2", "D17", "red SUV", None),
                "people_line": "H1"}
        sl = es.apply_verbatim(spec, {"slice_1_rest": "x", "slice_2": "x", "slice_3": "x"})
        story = es.plain_story(spec, sl)
        self.assertIn("camera", story)
        rules = {i["rule"] for i in es.verbatim_story_exempt(spec, sl, cp.story_rule_issues(F, None, story))}
        self.assertNotIn("b_no_camera_words", rules)
        bad = {**sl, "slice_1_rest": "Two people run as the camera shakes."}
        rules = {i["rule"] for i in es.verbatim_story_exempt(spec, bad, cp.story_rule_issues(
            F, None, es.plain_story(spec, bad)))}
        self.assertIn("b_no_camera_words", rules)


class TestA6Budget(_Quiet):
    def test_limits(self):
        self.assertEqual(es.max_prompt_words(F), 215)
        self.assertEqual(es.max_prompt_chars(F), 1400)
        self.assertEqual(es.slice_words(F, "slice_2"), (10, 43))
        self.assertEqual(es.slice_words(F, "slice_3"), (10, 45))
        self.assertEqual(es.TOTAL_WORDS_BY_EVENT[F], (40, 116))
        for e in es.EVENT_KEY_VISUAL:
            if e not in (F, L):
                self.assertEqual(es.slice_words(e, "slice_2"), es.SLICE_WORDS["slice_2"])
        self.assertEqual(es.max_prompt_words(T), 175)

    def test_budget_pairs_excluded(self):
        self.assertTrue(BUDGET_PAIRS <= es.EVENT_BEATS[F]["excluded_pairs"])
        self.assertFalse(FREED_PAIRS & es.EVENT_BEATS[F]["excluded_pairs"])
        pairs = es.allowed_pairs(F, "riviera", "Downtown city center")
        for bid in ("V11", "D14", "D18"):   # 4 Kas (2/3): her birinin en az 2 seçilebilir çifti
            self.assertGreaterEqual(len([p for p in pairs if bid in p]), 2, bid)
        self.assertEqual(es.EVENT_BEATS[F]["slice_2"]["V11"]["text"],
                         "the {vehicle} is swept up onto the sidewalk and slammed against a stone wall")
        self.assertFalse(es.pool_lint_hits("the vehicle is swept up onto the sidewalk and slammed against a stone wall"))

    def test_snapshot_fits(self):
        for seed, r in ps.snapshot_all([F], seeds=range(1, 41))[F].items():
            self.assertNotIn("error", r, seed)
            self.assertLessEqual(len(r["prompt"].split()), 215)
            self.assertLessEqual(len(r["prompt"]), 1400)
            self.assertIn(f"4-9s: {L2} ", r["prompt"])
            self.assertIn(f"9-15s: {L3} ", r["prompt"])
            self.assertTrue(any(a in r["prompt"] for a, _, _ in es.FLOOD_STORIES.values()), seed)


class TestA7Record(_Quiet):
    def test_fixture(self):
        with open(os.path.join(ROOT, "tests", "fixtures", "sel_good_videos.json"), encoding="utf-8") as f:
            v = json.load(f)["videos"][0]
        self.assertEqual((v["beats"], v["opening"], v["view"], v["score"]),
                         ("V12+D17", "A", "north_european_seaside", "8/10"))
        self.assertTrue(es.SEL_DOGRULAMA)
        self.assertIn("V12", es.TRIAL_BEATS[F])
        self.assertIn("D17", es.TRIAL_BEATS[F])


# ══════ BÖLÜM B ══════════════════════════════════════════════════════════════════════════════════════════════════════
class TestB1Structure(_Quiet):
    def test_registered(self):
        import bot
        self.assertTrue(es.is_structured(L))
        self.assertEqual(sk.EVENT_SKELETONS[L]["domain"], "coastal_tornado_landfall")
        self.assertTrue(es.verbatim_on(L))
        self.assertIn(L, es.VERBATIM_PEOPLE_EVENTS)
        self.assertIn(L, es.PEOPLE_AXIS_EVENTS)
        self.assertNotIn(L, es.LOCKED_EVENTS)
        self.assertEqual(bot.EVENT_LABELS[L], "🗽 Özgürlük Anıtı hortumu")
        self.assertEqual(sk.skeleton_events("coastal_tornado_landfall"),
                         ["Tornado making landfall", "Tornado crosses a marina quay",
                          "Tornado sweeps down a coastal avenue", L])
        self.assertEqual(DOMAIN_ATTRIBUTES["coastal_tornado_landfall"]["events"][-1], L)

    def test_menu_button(self):
        import bot
        di = bot.DOMAIN_KEYS.index("coastal_tornado_landfall")
        rows = bot.event_keyboard(di).inline_keyboard
        self.assertEqual([r[0].text for r in rows[:-2]], ["🌪️ Hortum karaya vurur", "🌪️ Hortum marina rıhtımını geçer",
                                                          "🌪️ Hortum sahil caddesini süpürür",
                                                          "🗽 Özgürlük Anıtı hortumu"])
        self.assertEqual(bot.parse_selection(*rows[3][0].callback_data.split(":")[2:]),
                         ("coastal_tornado_landfall", L))

    def test_landfall_data_untouched(self):
        self.assertEqual(es.EVENT_KEY_VISUAL[es.LANDFALL],
                         "A violent tornado makes landfall on the waterfront, tearing roofs and signs into the air.")
        self.assertEqual(set(es.EVENT_BEATS[es.LANDFALL]["slice_2"]), {"C1", "C2", "C4", "C5"})
        self.assertNotIn(es.LANDFALL, es.PEOPLE_AXIS_EVENTS)
        self.assertIsNot(es.EVENT_BEATS[L], es.EVENT_BEATS[es.LANDFALL])

    def test_builds(self):
        for seed in range(1, 41):
            r = ps.snapshot_event(L, seed)
            self.assertNotIn("error", r, seed)


class TestB2Flag(_Quiet):
    def tearDown(self):
        es.OZGURLUK_DOGRULAMA = True
        super().tearDown()

    def test_flag_on_equal_lru(self):
        self.assertTrue(es.OZGURLUK_DOGRULAMA)
        self.assertTrue(es.dogrulama_on(L))
        self.assertEqual(es.TRIAL_BEATS[L], set(es.EVENT_BEATS[L]["slice_2"]) | set(es.EVENT_BEATS[L]["slice_3"]))
        c2, c3, cp_ = collections.Counter(), collections.Counter(), collections.Counter()
        for seed in (1, 2):
            rows = _sequence(L, 60, seed)
            tags = [r["trace"]["beats"] for r in rows]
            self.assertFalse([1 for a, b in zip(tags, tags[1:]) if a == b])
            for t in tags:
                a, b = t.split("+")
                c2[a] += 1
                c3[b] += 1
            cp_.update(r["structure"]["axes"]["insan"] for r in rows)
        self.assertEqual(set(c2), set(B_POOL))
        self.assertEqual(set(c3), set(C_POOL))
        self.assertEqual(set(cp_), {"P1", "P2", "P3"})
        # 4 Kas (3): C6 sadece B5 ile eşleşir (tek çift), eşit pay bandının dışında; ayrı kontrol
        self.assertGreater(c3.pop("C6"), 0)
        for c in (c2, c3):
            n = sum(c.values())
            for k, v in c.items():
                self.assertTrue(0.6 / len(c) <= v / n <= 1.5 / len(c), (k, v))

    def test_flag_off(self):
        es.OZGURLUK_DOGRULAMA = False
        self.assertFalse(es.dogrulama_on(L))
        rows = _sequence(L, 20, 3)
        self.assertEqual(len(rows), 20)   # hepsi deneme: aday tükenmez


class TestB3toB10Texts(_Quiet):
    def test_key(self):
        self.assertEqual(es.EVENT_KEY_VISUAL[L], KEY)
        self.assertNotIn(L, ox.OPENINGS)   # tek açılış

    def test_pools(self):
        b = es.EVENT_BEATS[L]
        self.assertEqual({k: v["text"] for k, v in b["slice_2"].items()}, {k: "the tornado " + v for k, v in B_POOL.items()})
        want3 = {k: ("the tornado " + v) for k, v in C_POOL.items()}
        self.assertEqual({k: v["text"] for k, v in b["slice_3"].items()}, want3)
        self.assertEqual(set(es.LIBERTY_HELD_BEATS), {"C5"})   # 4 Kas (2): B4, B6 yeni metinle havuzda
        self.assertEqual(set(es.LIBERTY_RETIRED_TEXTS), {"B4", "B6"})
        self.assertTrue({("B4", "C6"), ("B6", "C3"), ("B2", "C1")} <= b["excluded_pairs"])   # 4 Kas (3): ek dışlamalar

    def test_frames(self):
        self.assertEqual(set(sk.EVENT_SKELETONS[L]["spots"]), set(K))
        for spot in K:
            frames = fx.all_frames(L, spot, list(K))
            self.assertEqual(len(frames), 1)
            self.assertEqual(frames[0]["pos_spot"], spot)
            cam = sk.camera_rules(fx.frame_camera(L, spot, frames[0], legacy=sk.legacy_camera))
            self.assertIn(STATUE, cam)
            low = cam.lower()
            for w in ("high", "wide", "fixed", "never descending"):
                self.assertIn(w, low)
            for w in ("eye level", "pans to follow", "follows the", "normal lens"):
                self.assertNotIn(w, low)

    def test_light_vehicle_people_setting(self):
        self.assertEqual(sk.EVENT_SKELETONS[L]["weather"], LIGHTS)
        self.assertEqual([v for v, _ in es.EVENT_VEHICLES[L]], ["yellow taxi", "red SUV", "blue sedan"])
        self.assertEqual(es.FALLBACK_PEOPLE[L], P_LINES)
        self.assertEqual(sk.count_range(L, None), (3, 6))
        for li in LIGHTS:
            spec = _lib_spec(light=li)
            self.assertIn(f"Setting: Battery Park and the harbor waterfront at the southern tip of Manhattan, {li}, "
                          f"no readable signs, text or flags.", spec["suffix"])
        for seed in range(1, 21):
            r = ps.snapshot_event(L, seed)
            self.assertIn(f", {r['axes']['weather']}, no readable signs", r["prompt"])


class TestB11Gate(_Quiet):
    def _clean(self, spec):
        return es.build_fallback(spec, line="P1")

    def test_code_text_passes(self):
        for b2 in B_POOL:
            for b3 in C_POOL:
                spec = {**_lib_spec(b2, b3), "people_line": "P1"}
                sl = self._clean(spec)
                self.assertEqual(es.liberty_gate_issues(spec, sl), [])
                self.assertEqual(es.final_prompt_issues(spec, sl, es.assemble_prompt(spec, sl),
                                                        es.assemble_story(spec, sl)), [], (b2, b3))

    def test_gpt_rejected(self):
        spec = {**_lib_spec("B1", "C3"), "people_line": "P1"}
        sl = self._clean(spec)
        for bad in ("Four people run as a taxi spins.", "A car flips upside down.", "A van is lifted off the road.",
                    "A truck stands on its nose.", "People run past a skyscraper.", "Four people flee the tower.",
                    "The twin buildings shake.", "Smoke rises over the World Trade Center."):
            with self.subTest(bad=bad):
                self.assertIn("liberty_banned_root", {i["rule"] for i in es.liberty_gate_issues(
                    spec, {**sl, "slice_1_rest": bad})})
        for bad in ("The statue topples into the harbor.", "The statue collapses.", "The tornado rips the statue apart.",
                    "The statue falls.", "Debris damages the statue."):
            with self.subTest(bad=bad):
                self.assertIn("liberty_statue_damage", {i["rule"] for i in es.liberty_gate_issues(
                    spec, {**sl, "slice_2": bad})})
        self.assertEqual(es.liberty_gate_issues(spec, {**sl, "slice_1_rest": "Four people run past the statue."}), [])
        self.assertIn("liberty_anchor", {i["rule"] for i in es.liberty_gate_issues(
            {**spec, "key_visual": "A tornado hits."}, sl)})

    def test_only_this_event(self):
        spec = es.build_spec(es.AVENUE, None, "High balcony over a downtown avenue", None, "P1", "Q1", "pickup truck", 4)
        self.assertEqual(es.liberty_gate_issues(spec, {"slice_1_rest": "The tower spins.", "slice_2": "", "slice_3": ""}),
                         [])


class TestB12Acceptance(_Quiet):
    def test_lint_and_scores(self):
        for bid, beat in list(es.EVENT_BEATS[L]["slice_2"].items()) + list(es.EVENT_BEATS[L]["slice_3"].items()):
            self.assertEqual(es.pool_lint_hits(beat["text"].replace("{vehicle}", "vehicle")), [], bid)
            self.assertGreaterEqual(min(es.LIBERTY_BEAT_SCORES[bid]), 3, bid)
        self.assertTrue(es.pool_lint_hits(es.LIBERTY_RETIRED_TEXTS["B4"][0]))
        self.assertTrue(es.pool_lint_hits(es.LIBERTY_RETIRED_TEXTS["B6"][0]))
        self.assertLess(min(es.LIBERTY_BEAT_SCORES["C5"]), 3)
        for t in P_LINES:
            self.assertEqual(es.people_scatter(t), [])

    def test_budget(self):
        self.assertEqual(es.max_prompt_words(L), 205)
        self.assertEqual(es.max_prompt_chars(L), 1400)
        self.assertEqual(es.TOTAL_WORDS_BY_EVENT[L], (40, 85))
        n = 0
        for li in LIGHTS:
            for spec in _all_specs(L, light=li):
                spec = {**spec, "frame": fx.all_frames(L, spec["spot"], [spec["spot"]])[0]}
                spec["suffix"] = sk.style_suffix(L, None, spec["spot"], None, None, None, spec["frame"], None, None, li)
                ids = [i for i, _ in es.fallback_candidates_ids(spec)]
                self.assertEqual(ids, ["P1", "P2", "P3"], (spec["spot"], spec["beat_2"], spec["beat_3"]))
                n += 1
        self.assertGreater(n, 100)


if __name__ == "__main__":
    unittest.main()
