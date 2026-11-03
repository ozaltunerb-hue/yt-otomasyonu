#!/usr/bin/env python3
"""3 Kasım 2026, Bahadır: sel su kontrolü (Caddelerde ani sel). Ağ yok, Kie/GPT çağrısı yok (sahte GPT).

- Su profili: açılış A aynen (bel hizası); 4-9s ve 9-15s başında koddan birebir su seviyesi cümlesi (VERBATIM).
- Pasifler (silinmedi): açılış B, C; V3, V5, V6, V7, V8; D3, D8, D9 (+ eski V4, D2, D4). Yeni öğeler DENEME.
- Araç renkleri (sel + dev dalga ortak liste), ortam metinlerinde araç tarifi yok.
- Işık: sel ve dev dalgada seçilen ışık Setting satırında birebir.
- Sel kapısı: yasak kökler GPT çıktısında; çöküş kökleri sadece 9-15s VERBATIM havuz metninde serbest.
- SEL_DOGRULAMA: selde deneme payı en fazla %50, art arda deneme yok.
- Kod yedeği her çiftte son denetimden geçer. Dev dalga pasifleri UYGULANMADI (9-15s aktif öğe 4'ün altına düşerdi).
"""
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
import core.opening_axis as ox   # noqa: E402
import core.proven_axes as pa   # noqa: E402
import core.skeleton_pipeline as sk   # noqa: E402
from test_toplu_3kas import _sequence   # noqa: E402

F, T = es.FLOOD, es.TIDAL
L2 = "Water rises past the car windows."
L3 = "A second surge, first-floor high, slams in."
ACTIVE_2 = {"V1", "V2", "V9", "V10", "V11", "V12"}
ACTIVE_3 = {"D5", "D10", "D12", "D13", "D14", "D15", "D16", "D17", "D18"}
PASSIVE = {"D2", "D4", "V4", "V3", "V5", "V6", "V7", "V8", "D3", "D8", "D9"}
TRIAL = {"D10", "V9", "V10", "V11", "V12", "D12", "D13", "D14", "D15", "D16", "D17", "D18"}
NEW_TEXTS = {
    "V9": "the {vehicle} is shoved hard against the side of a parked city bus and pinned there",
    "V10": "the {vehicle} is rammed against a building front and pinned there by the current",
    "V11": "the {vehicle} is swept into a corner shop and its doors burst open as water pours inside",
    "V12": "the {vehicle} floats free and is carried fast down the middle of the street",
    "D10": "the current shoves parked cars into a shopfront and its wall caves in",
    "D13": "the street becomes a fast brown river and the {vehicle} is carried away toward the intersection",
    "D14": "the current pushes a parked city bus against a shopfront and floodwater pours in through its doors",
    "D15": "the flood bursts open a row of shop shutters and pours into the stores",
    "D16": "the surge tears the ground-floor fronts off the shops across the street",
    "D17": "the surge tips a city bus onto its side and pushes it along the street",
    "D18": "the surge slams the {vehicle} into a building front and the shopfront caves in around it",
}
VEHICLE_WORDS = re.compile(r"\b(suvs?|vans?|trucks?|pickups?|scooters?|cars?|sedans?|buses|bus|taxis?)\b", re.I)


class _Quiet(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.WARNING)

    def tearDown(self):
        logging.disable(logging.NOTSET)


def _pool(e):
    b = es.EVENT_BEATS[e]
    return {**b["slice_2"], **b["slice_3"]}


def _spec(b2="V1", b3="D10", view="riviera", vehicle="red SUV", light="heavy rain"):
    return es.build_spec(F, None, "Commercial city streets", view, b2, b3, vehicle, 4, light=light)


class TestWaterProfile(_Quiet):
    def test_opening_a_unchanged(self):
        self.assertEqual(es.EVENT_KEY_VISUAL[F], "A waist-high wall of brown muddy floodwater surges into the street.")
        self.assertEqual(es.WATER_LEVEL_LINES, {F: {"slice_2": L2, "slice_3": L3}})

    def test_level_lines_lead_each_slice(self):
        spec = _spec("V2", "D5")
        self.assertEqual(es.fallback_beat_slice(spec, "slice_2"),
                         L2 + " The red SUV is swept into another parked car and both are shoved along.")
        self.assertEqual(es.fallback_beat_slice(spec, "slice_3"), L3 + " A city bus is shoved sideways by the current.")

    def test_verbatim_keeps_level_lines(self):
        """GPT dilimi ne yazarsa yazsın 4-9s / 9-15s koddan (su cümlesi dahil)."""
        spec = _spec()
        out = es.apply_verbatim(spec, {"slice_1_rest": "Four people run for the doorways.",
                                       "slice_2": "The SUV drifts.", "slice_3": "Water rises."})
        self.assertTrue(out["slice_2"].startswith(L2 + " "))
        self.assertTrue(out["slice_3"].startswith(L3 + " "))

    def test_snapshot_prompts(self):
        for seed, r in ps.snapshot_all([F])[F].items():
            self.assertNotIn("error", r, seed)
            self.assertIn(f"4-9s: {L2} ", r["prompt"])
            self.assertIn(f"9-15s: {L3} ", r["prompt"])
            self.assertLessEqual(len(r["prompt"].split()), 185)

    def test_limits_only_flood(self):
        self.assertEqual(es.slice_words(F, "slice_2"), (10, 26))
        self.assertEqual(es.slice_words(F, "slice_3"), (10, 30))
        self.assertEqual(es.TOTAL_WORDS_BY_EVENT[F], (40, 80))
        self.assertEqual(es.max_prompt_words(F), 185)
        for e in es.EVENT_KEY_VISUAL:
            if e != F:
                self.assertEqual(es.slice_words(e, "slice_2"), es.SLICE_WORDS["slice_2"])
                self.assertEqual(es.slice_words(e, "slice_3"), es.SLICE_WORDS["slice_3"])
                self.assertNotIn(e, es.WATER_LEVEL_LINES)
        self.assertEqual(es.max_prompt_words(T), 175)


class TestPassiveAndActive(_Quiet):
    def test_sets(self):
        self.assertEqual(es.DISABLED_BEATS[F], PASSIVE)
        self.assertEqual(es.TRIAL_BEATS[F], TRIAL)
        b = es.EVENT_BEATS[F]
        self.assertEqual(set(b["slice_2"]) - PASSIVE, ACTIVE_2)
        self.assertEqual(set(b["slice_3"]) - PASSIVE, ACTIVE_3)
        self.assertGreaterEqual(len(ACTIVE_2), 6)
        self.assertGreaterEqual(len(ACTIVE_3), 6)
        self.assertTrue(PASSIVE <= set(_pool(F)))   # silinmedi
        for bid, text in NEW_TEXTS.items():
            self.assertEqual(_pool(F)[bid]["text"], text)
        self.assertNotIn("D11", _pool(F))

    def test_never_selected(self):
        for view in es.structure_views(F):
            for spot in sk.view_spots(F, view):
                pairs = es.allowed_pairs(F, view, spot)
                self.assertTrue(pairs)
                self.assertFalse([p for p in pairs if set(p) & PASSIVE])

    def test_openings(self):
        self.assertEqual(ox.DISABLED_OPENINGS, {F: {"B", "C"}})
        self.assertEqual(ox.options(F), ["A", "D", "E", "F"])
        self.assertIn("B", ox.OPENINGS[F])   # silinmedi
        self.assertIn("C", ox.OPENINGS[F])
        self.assertEqual(ox.OPENINGS[F]["E"], "A wall of brown floodwater swings around the corner of an intersection "
                                              "and shoves parked cars sideways.")
        self.assertEqual(ox.OPENINGS[F]["F"], "A surge of brown floodwater pours down the sloping street and drags "
                                              "parked cars along with it.")
        self.assertEqual(pa.GUARD["acilis"][F][0], "E")
        self.assertEqual(ox.options(T), ["A", "B", "C", "D"])   # dev dalga aynı

    def test_tidal_passives_not_applied(self):
        """9-15s aktif öğe 4'ün altına düşeceği için dev dalga pasifleri (T4, T8, W9, W3) uygulanmadı."""
        self.assertEqual(es.DISABLED_BEATS[T], {"W2", "W6", "W8", "T6"})
        self.assertEqual(es.TRIAL_BEATS[T], {"W9"})
        active_3 = set(es.EVENT_BEATS[T]["slice_3"]) - es.DISABLED_BEATS[T]
        self.assertLess(len(active_3 - {"W3", "W9"}), 4)


class TestColorsAndSettings(_Quiet):
    def test_vehicle_colors(self):
        colors = ("red", "yellow", "blue", "green", "orange")
        for view, vehicles in es.REGION_VEHICLES.items():
            names = [v for v, _ in vehicles]
            first = [n.split()[0] for n in names]
            self.assertTrue(all(c in colors for c in first), names)
            self.assertEqual(len(set(first)), len(first), view)   # görünüm içinde renkler ayrışır
        self.assertEqual({n for vs in es.REGION_VEHICLES.values() for n, _ in vs},
                         {"red SUV", "yellow pickup truck", "blue sedan", "green delivery van", "orange box truck",
                          "orange delivery truck"})
        self.assertNotIn("white SUV", es.REGION_VEHICLE_COLOR_RENAMES.values())

    def test_settings_have_no_vehicles(self):
        for view, text in sk.REGION_VIEWS.items():
            self.assertIsNone(VEHICLE_WORDS.search(text), (view, text))

    def test_light_in_setting(self):
        for e in (F, T):
            for seed, r in ps.snapshot_all([e])[e].items():
                light = r["axes"]["weather"]
                self.assertIn(f", in {light}, no readable signs", r["prompt"], (e, seed))
        self.assertEqual(set(sk.VIEW_LIGHT_EVENTS), {F, T})
        self.assertFalse(set(sk.VIEW_LIGHT_EVENTS) & set(es.LOCKED_EVENTS))


class TestFloodGate(_Quiet):
    def _issues(self, spec, slices):
        return [i for i in es.flood_root_issues(spec, slices)]

    def test_gpt_roots_rejected(self):
        spec = _spec("V1", "D5")
        base = {"slice_1_rest": "Four people run for the doorways.",
                "slice_2": es.fallback_beat_slice(spec, "slice_2"), "slice_3": es.fallback_beat_slice(spec, "slice_3")}
        self.assertEqual(self._issues(spec, base), [])
        bad = ("the car is spinning", "a van spun away", "the SUV flips", "a car lands upside down",
               "the van lifts off the street", "a car is lifted off the ground", "a car is ripped off its wheels",
               "a truck slides off the road", "a car stands on its nose", "a tree is uprooted",
               "the wall collapses", "the shop caves in", "the facade crumbles", "the bus tips over",
               "the car rolls onto its side")
        for phrase in bad:
            with self.subTest(phrase=phrase):
                self.assertTrue(self._issues(spec, {**base, "slice_1_rest": f"Four people run as {phrase}."}))
                self.assertTrue(self._issues(spec, {**base, "slice_2": f"Water rises as {phrase}."}))

    def test_collapse_only_in_verbatim_slice_3(self):
        for b3 in ("D10", "D17", "D18"):
            spec = _spec("V1", b3)
            v3 = es.fallback_beat_slice(spec, "slice_3")
            self.assertTrue(es.flood_root_words(v3))   # çöküş / yan yatma kökü var
            sl = {"slice_1_rest": "Four people run for the doorways.",
                  "slice_2": es.fallback_beat_slice(spec, "slice_2"), "slice_3": v3}
            self.assertEqual(self._issues(spec, sl), [], b3)
            # GPT'nin yazdığı aynı kökler (birebir havuz metni değil) reddedilir
            self.assertTrue(self._issues(spec, {**sl, "slice_3": "The surge hits and the shop wall caves in."}))
            self.assertTrue(self._issues(spec, {**sl, "slice_3": "The bus tips over onto its side."}))

    def test_code_texts_clean(self):
        texts = [es.EVENT_KEY_VISUAL[F], L2, L3] + [ox.OPENINGS[F][o] for o in ox.options(F) if o != "A"]
        texts += [p.format(N="Four") for p in es.FALLBACK_PEOPLE[F]]
        texts += [es.EVENT_BEATS[F]["slice_2"][b]["text"] for b in ACTIVE_2]
        for t in texts:
            self.assertEqual(es.flood_root_words(t), [], t)
        for b in ACTIVE_3:   # 9-15s: sadece çöküş kökleri serbest
            self.assertEqual(es.flood_root_words(es.EVENT_BEATS[F]["slice_3"][b]["text"], collapse=False), [], b)

    def test_gate_only_flood(self):
        self.assertEqual(es.FLOOD_GATE_EVENTS, (F,))
        spec = es.build_spec(T, None, "Coastal street of low shopfronts", "riviera", "T2", "W1", "red SUV", 4, None,
                             None, None, None, "D", "heavy rain")
        self.assertIn("collapses", spec["key_visual"])
        sl = es.build_fallback(spec, random.Random(1))
        self.assertFalse([i for i in es.final_prompt_issues(spec, sl, es.assemble_prompt(spec, sl),
                                                            es.assemble_story(spec, sl))
                          if i["rule"] == "flood_banned_root"])

    def test_float_only_in_verbatim(self):
        """V12 'floats' havuz metninde geçer (yüzdürme izinli); GPT kişi cümlesinde 'floats' reddedilir."""
        spec = _spec("V12", "D5")
        sl = es.build_fallback(spec, random.Random(1))
        self.assertIn("floats", sl["slice_2"])
        self.assertEqual(es.final_prompt_issues(spec, sl, es.assemble_prompt(spec, sl), es.assemble_story(spec, sl)),
                         [])
        bad = {**sl, "slice_1_rest": "Four people run as a car floats past."}
        rules = {i["rule"] for i in es.final_prompt_issues(spec, bad, es.assemble_prompt(spec, bad),
                                                           es.assemble_story(spec, bad))}
        self.assertIn("d_no_scale_reducers", rules)


class TestTrialShare(_Quiet):
    def test_flag(self):
        self.assertTrue(es.SEL_DOGRULAMA)
        self.assertEqual(es.trial_beat_share(F), 0.50)
        for e in es.EVENT_KEY_VISUAL:
            if e != F:
                self.assertEqual(es.trial_beat_share(e), es.TRIAL_BEAT_SHARE)
        self.assertEqual(es.TRIAL_BEAT_SHARE, 0.20)

    def test_share_lru_no_repeat(self):
        rows = _sequence(F, 100, 7)
        flags = [bool(set(r["trace"]["beats"].split("+")) & TRIAL) for r in rows]
        self.assertLessEqual(sum(flags) / len(flags), 0.55)
        self.assertGreater(sum(flags) / len(flags), 0.20)   # %20'den belirgin yüksek
        self.assertFalse(any(a and b for a, b in zip(flags, flags[1:])))   # art arda deneme yok
        tags = [r["trace"]["beats"] for r in rows]
        self.assertFalse([1 for a, b in zip(tags, tags[1:]) if a == b])   # LRU: aynı çift art arda yok
        for r in rows:
            self.assertFalse(set(r["trace"]["beats"].split("+")) & PASSIVE)


class TestFallbackEveryPair(_Quiet):
    def test_every_pair_passes(self):
        """Her görünüm × nokta × izinli çift × araç (en uzun ışıkla): kod yedeği sığar ve son denetimden geçer."""
        light = max(sk.EVENT_SKELETONS[F]["weather"], key=lambda x: len(x.split()))
        n = 0
        for view in es.structure_views(F):
            for spot in sk.view_spots(F, view):
                for b2, b3 in es.allowed_pairs(F, view, spot):
                    for veh, _ in es.event_vehicles(F, view):
                        spec = es.build_spec(F, None, spot, view, b2, b3, veh, 6, light=light)
                        cands = es.fallback_candidates(spec)
                        self.assertTrue(cands, (view, spot, b2, b3, veh))
                        sl = cands[0]
                        prompt = es.assemble_prompt(spec, sl)
                        self.assertLessEqual(len(prompt.split()), 185)
                        self.assertEqual(es.final_prompt_issues(spec, sl, prompt, es.assemble_story(spec, sl)), [],
                                         (view, spot, b2, b3, veh))
                        n += 1
        self.assertGreater(n, 500)


if __name__ == "__main__":
    unittest.main()
