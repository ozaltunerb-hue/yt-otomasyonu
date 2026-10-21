#!/usr/bin/env python3
"""Kadraj ekseni (21 Eki 2026, Gece 1 / Aşama 4): kadraj tipi, ön plan, kamera modu.

- Kütüphane: her tip ana şablondan; yasaklı ifade yok, yükseklik ve sabitlik var; direkte el titremesi yok; depremde
  "strong hand shake from the ground tremor" korunur.
- İzinli tipler görev listesiyle birebir (+ teras: mevcut teras/promenat/basamak noktaları).
- Mod A bugünkü cümle kelimesi kelimesine; volkan/çığ/deprem korkuluk ön planı bugünkü cümleyle birebir.
- Alçak kamera spotlarında bugünkü cümle hiç kullanılmaz.
- LRU (kadraj son 2 / 3 ve daha az seçenekte son 1, ön plan ve mod son 1), direk ağırlığı 1.
- Ayrı rastgele akış ana akışı tüketmez; Notion "Eksenler" alanları; K5 sığma koruması.
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
import core.frame_axis as fx   # noqa: E402
import core.skeleton_pipeline as sk   # noqa: E402
import prompt_rules as pr   # noqa: E402
import prompt_snapshot as ps   # noqa: E402

TASK_TYPES = {   # görev metni (Aşama 4, madde 2)
    es.FLOOD: {"balkon", "çatı", "pencere", "direk"}, es.TIDAL: {"balkon", "çatı", "pencere", "direk"},
    es.MUDSLIDE: {"balkon", "çatı", "pencere"}, es.SLOPE: {"balkon", "çatı", "tepe"},
    es.VILLAGE: {"balkon", "çatı", "tepe"}, es.LANDFALL: {"balkon", "çatı", "pencere", "direk"},
    es.MARINA_TORNADO: {"balkon", "çatı", "pencere", "direk"}, es.AVENUE: {"balkon", "çatı", "pencere", "direk"},
    es.WILDFIRE: {"balkon", "çatı", "tepe"}, es.FACADE_FIRE: {"balkon", "çatı", "pencere"},
    es.FIRE_TORNADO: {"balkon", "çatı", "tepe"}, es.HELICOPTER: {"balkon", "çatı", "tepe"},
    es.PYROCLASTIC: {"balkon", "çatı", "tepe", "pencere"}, es.VOLCANIC_BOMBS: {"balkon", "çatı", "tepe", "pencere"},
    **{e: {"balkon", "teras", "pencere"} for e in es.AVALANCHE_EVENTS},
    **{e: {"balkon", "çatı", "pencere"} for e in es.EARTHQUAKE_EVENTS},
}
EXTRA_TERAS = {es.TIDAL, es.VILLAGE}   # mevcut teras/promenat/seawall/basamak noktaları kendi tipleriyle


def pool(event, spot, view=None):
    if event == es.FIRE_TORNADO:
        return list(es.FIRE_TOR_ENVS[es.fire_env_of_spot(spot)]["spots"])
    return sk.view_spots(event, view)


class TestLibrary(unittest.TestCase):
    def check(self, cam, ftype="x"):
        item = {"style_suffix": cam, "prompt": cam}
        out = pr.check("x", item)
        self.assertFalse({"K1", "K2", "K3"} & set(out), (cam, out))

    def test_every_type_follows_master_template(self):
        for t in ("balkon", "çatı", "pencere", "tepe", "teras", "direk"):
            pos, perch = fx.LIB_POS.get(t, ("on a terrace", "terrace"))
            fg = fx.FG_TEXT[fx.FRAME_FG[t][0]] if fx.FRAME_FG[t] else None
            cam = fx.generic_camera(t, pos.format(scene="the street"), perch, "the street", "the tornado", fg)
            with self.subTest(type=t):
                self.check(cam)
                self.assertTrue(cam.endswith("one continuous shot, no zoom, no cuts."))
                self.assertIn("never" if t != "direk" else "fixed", cam)
                if t == "direk":
                    self.assertNotIn("slight hand shake", cam)
                    self.assertIn("no on-screen text, no timestamp", cam)
                else:
                    self.assertIn("slight hand shake", cam)

    def test_foreground_options(self):
        self.assertEqual(fx.FRAME_FG["pencere"], ("pencere",))
        self.assertEqual(fx.FRAME_FG["direk"], ())
        for t in ("balkon", "çatı", "tepe"):
            self.assertIn("boş", fx.FRAME_FG[t])
        self.assertEqual(fx.FRAME_WEIGHTS["direk"], 1)
        self.assertTrue(all(w == 2 for t, w in fx.FRAME_WEIGHTS.items() if t != "direk"))

    def test_earthquake_keeps_strong_shake(self):
        for e in es.EARTHQUAKE_EVENTS:
            for spot in sk.view_spots(e, None):
                for f in fx.all_frames(e, spot, pool(e, spot)):
                    cam = pr.camera_sentence(sk.style_suffix(e, None, spot, frame=f))
                    self.assertIn("strong hand shake from the ground tremor", cam)


class TestAllowedTypes(unittest.TestCase):
    def test_types_match_task(self):
        self.assertEqual(set(fx.FRAME_EVENTS), set(es.structured_events()))
        for e, types in TASK_TYPES.items():
            got = set(fx.FRAME_EVENTS[e]["types"]) - ({"teras"} if e in EXTRA_TERAS else set())
            self.assertEqual(got, types, e)

    def test_every_spot_has_native_frame(self):
        for e in ps.active_events():
            self.assertTrue(set(sk.EVENT_SKELETONS[e]["spots"]) <= set(fx.SPOT_FRAME[e]), e)
            for spot, (t, kind, _, _) in fx.SPOT_FRAME[e].items():
                self.assertIn(t, fx.FRAME_EVENTS[e]["types"], (e, spot))

    def test_no_bridge_on_slope(self):
        for spot, (_, _, pos, _) in fx.SPOT_FRAME[es.SLOPE].items():
            self.assertNotIn("bridge", (pos or "").lower())
            self.assertNotIn("overpass", (pos or "").lower())

    def test_marina_has_four_frames(self):
        spot = next(iter(sk.EVENT_SKELETONS[es.MARINA_TORNADO]["spots"]))
        types = {f["type"] for f in fx.all_frames(es.MARINA_TORNADO, spot, [spot])}
        self.assertEqual(types, {"balkon", "çatı", "pencere", "direk"})


class TestModeAndNative(unittest.TestCase):
    def test_mode_a_is_todays_sentence_verbatim(self):
        n = 0
        for e in ps.active_events():
            for spot, (t, kind, _, _) in fx.SPOT_FRAME[e].items():
                if kind != fx.AB:
                    continue
                f = {"type": t, "pos_spot": spot, "fg": None, "mode": "A"}
                view = next(v for v in es.structure_views(e) if spot in sk.view_spots(e, v))
                fire_env = es.fire_env_of_spot(spot) if e == es.FIRE_TORNADO else None
                self.assertEqual(sk.style_suffix(e, None, spot, view, frame=f, fire_env=fire_env),
                                 sk.style_suffix(e, None, spot, view), (e, spot))
                n += 1
        self.assertEqual(n, 26)   # kıyı dalga 3, yamaç 2, köy 3, marina 1, cadde 3, orman 2, cephe 4, ateş 6, heli 2

    def test_native_railing_is_todays_sentence_verbatim(self):
        n = 0
        for e in ps.active_events():
            if fx.family(e) not in ("volcano", "avalanche", "earthquake"):
                continue
            for spot in sk.EVENT_SKELETONS[e]["spots"]:
                t = fx.SPOT_FRAME[e][spot][0]
                for venv in (list(sk.VOLC_ENVS) if e in es.VOLC_ENV_EVENTS else [None]):
                    f = {"type": t, "pos_spot": spot, "fg": "korkuluk", "mode": None}
                    self.assertEqual(sk.style_suffix(e, None, spot, volc_env=venv, frame=f),
                                     sk.style_suffix(e, None, spot, volc_env=venv), (e, spot, venv))
                    empty = dict(f, fg="boş")
                    other = sk.style_suffix(e, None, spot, volc_env=venv, frame=empty)
                    self.assertNotEqual(other, sk.style_suffix(e, None, spot, volc_env=venv))
                    self.assertNotIn("railing", pr.camera_sentence(other))
                    n += 1
        self.assertEqual(n, 2 * 3 * 4 + 7 + 4)

    def test_low_spots_never_use_todays_camera(self):
        fixed = [(e, s) for e in ps.active_events() for s, v in fx.SPOT_FRAME[e].items() if v[1] == fx.FIXED]
        self.assertEqual(len(fixed), 10)   # sel 4, karaya 3, yamaç çökmesi 2, yamaç sokağı merdiven 1
        for e, spot in fixed:
            for view in es.structure_views(e):
                if spot not in sk.view_spots(e, view):
                    continue
                old = pr.camera_sentence(sk.style_suffix(e, None, spot, view))
                for f in fx.all_frames(e, spot, pool(e, spot, view)):
                    # 21 Eki (Aşama 5): sabit spotta mod A hiç yok, ödünç de alınmaz; hiçbir K1 ifadesi yok
                    self.assertNotEqual(f["mode"], "A", (e, spot, f))
                    cam = pr.camera_sentence(sk.style_suffix(e, None, spot, view, frame=f))
                    self.assertNotEqual(cam, old)
                    self.assertEqual(pr._has(pr.CAMERA_BANNED, cam), [], (e, spot, f))

    def test_mode_a_only_own_spot(self):
        # 21 Eki (Aşama 5): mod A sadece kendi spotunun kendi eski cümlesi; ödünç noktada mod ekseni yok
        for e in ps.active_events():
            for spot in sk.EVENT_SKELETONS[e]["spots"]:
                for f in fx.all_frames(e, spot, pool(e, spot)):
                    if f["mode"] == "A":
                        self.assertEqual(f["pos_spot"], spot, (e, spot, f))
                    if f["pos_spot"] and f["pos_spot"] != spot:
                        self.assertIsNone(f["mode"], (e, spot, f))
        for i in range(60):
            f, _ = fx.choose_frame(es.AVENUE, "High balcony over a downtown avenue", sk.view_spots(es.AVENUE, None),
                                   set(), [], random.Random(i))
            if f["pos_spot"] != "High balcony over a downtown avenue":
                self.assertIsNone(f["mode"])

    def test_fixed_spot_prompts_have_no_k1(self):
        logging.disable(logging.WARNING)
        try:
            fixed = {(e, s) for e in ps.active_events() for s, v in fx.SPOT_FRAME[e].items() if v[1] == fx.FIXED}
            n = 0
            for e in {e for e, _ in fixed}:
                for seed in range(30):
                    item = ps.snapshot_event(e, seed)
                    if (e, item["axes"]["spot"]) in fixed:
                        n += 1
                        self.assertEqual(pr._has(pr.CAMERA_BANNED, pr.camera_sentence(item["style_suffix"])), [])
            self.assertGreater(n, 50)
        finally:
            logging.disable(logging.NOTSET)

    def test_new_sentences_pass_camera_rules(self):
        for e, items in pr.camera_items().items():
            for key, item in items.items():
                out = pr.check(e, item)
                if item["frame"]["mode"] == "A":
                    continue
                self.assertFalse({"K1", "K2", "K3"} & set(out), (e, key, out))


class TestSelection(unittest.TestCase):
    def test_side_rng_does_not_consume_main_stream(self):
        random.seed(11)
        before = random.getstate()
        fx.side_rng().random()
        self.assertEqual(random.getstate(), before)
        random.seed(11)
        a = fx.side_rng().random()
        random.seed(11)
        self.assertEqual(fx.side_rng().random(), a)

    def test_frame_depth(self):
        self.assertEqual([fx.frame_depth(n) for n in (1, 2, 3, 4, 5)], [0, 1, 1, 2, 2])

    def test_kadraj_lru_last_two_and_mode_alternates(self):
        e, spot = es.AVENUE, "High balcony over a downtown avenue"
        p = sk.view_spots(e, None)
        hist = []
        for i in range(40):
            f, _ = fx.choose_frame(e, spot, p, set(), hist, random.Random(i))
            if len(hist) >= 2:
                self.assertNotIn(f["type"], {hist[-1]["kadraj"], hist[-2]["kadraj"]})
            hist.append({"kadraj": f["type"], "on_plan": f["fg"], "kamera_modu": f["mode"]})
        modes = [h["kamera_modu"] for h in hist if h["kamera_modu"]]
        self.assertFalse([i for i in range(1, len(modes)) if modes[i] == modes[i - 1]])

    def test_three_types_last_one(self):
        e, spot = es.WILDFIRE, "Balcony of a hillside house"
        hist = [{"kadraj": "çatı"}, {"kadraj": "balkon"}]
        seen = {fx.choose_frame(e, spot, sk.view_spots(e, None), set(), hist, random.Random(i))[0]["type"]
                for i in range(40)}
        self.assertEqual(seen, {"çatı", "tepe"})   # 3 tip: sadece son 1 (balkon) elenir

    def test_foreground_last_one(self):
        e, spot = es.VOLCANIC_BOMBS, "Balcony of a village house facing the erupting volcano"
        p = sk.view_spots(e, None)
        for i in range(30):
            f, _ = fx.choose_frame(e, spot, p, set(), [{"on_plan": "korkuluk"}], random.Random(i))
            self.assertNotEqual(f["fg"], "korkuluk")

    def test_pole_weight_one(self):
        e, spot = es.FLOOD, "Downtown city center"
        c = collections.Counter(fx.choose_frame(e, spot, sk.view_spots(e, None), set(), [], random.Random(i))[0]["type"]
                                for i in range(4000))
        self.assertAlmostEqual(c["balkon"] / c["direk"], 2, delta=0.35)

    def test_risky_spot_not_borrowed(self):
        e = es.VOLCANIC_BOMBS
        hill = "Hillside terrace facing the erupting volcano"
        risky = {"Balcony of a village house facing the erupting volcano", "Rooftop terrace facing the erupting volcano"}
        for i in range(30):
            f, _ = fx.choose_frame(e, hill, sk.view_spots(e, None), risky, [], random.Random(i))
            self.assertEqual(f["type"], "tepe")   # balkon/çatı riskli, pencere balkon riskini taşır


class TestNotionAndApproval(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.WARNING)
        ps.reset_memory()

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_axes_json_has_frame_fields(self):
        for k in ("kadraj", "on_plan", "kamera_modu", "kamera_noktasi"):
            self.assertIn(k, ah.AXIS_KEYS)
        random.seed(3)
        scene = ps.build(es.AVENUE)
        data = json.loads(scene["axes_json"])
        self.assertIn(data["axes"]["kadraj"], fx.FRAME_EVENTS[es.AVENUE]["types"])
        line = scene["structure"]["axes_line"]
        self.assertIn("kadraj=", line)
        self.assertIn("kamera modu=", line)
        old = ah.parse_record({"combo_key": "urban_city_disasters|none|flash flooding in city streets|"
                                            "downtown city center##V1+D2|c"})
        self.assertIsNone(old["axes"]["kadraj"])
        self.assertIsNone(old["axes"]["kamera_modu"])

    def test_notion_history_drives_frame_lru(self):
        e = es.MARINA_TORNADO
        spot = next(iter(sk.EVENT_SKELETONS[e]["spots"]))
        rec = lambda k: {"combo_key": f"coastal_tornado_landfall|none|{e.lower()}|{spot.lower()}##C1+E1|c",
                         "eksenler": ah.axes_json(e, {"spot": spot, "kadraj": k}), "status": "❌ İptal"}
        for seed in range(15):
            random.seed(seed)
            scene = ps.build(e, axes_loader=lambda d: [rec("balkon"), rec("direk")])
            self.assertNotIn(scene["structure"]["axes"]["kadraj"], ("balkon", "direk"))

    def test_spec_frame_rebuilt_by_final_check(self):
        random.seed(5)
        scene = ps.build(es.FACADE_FIRE)
        spec = scene["structure"]["spec"]
        self.assertIn("frame", spec)
        self.assertEqual(es.final_prompt_issues(spec, scene["structure"]["slices"], scene["prompt"], scene["story"]), [])
        spec2 = dict(spec, frame=dict(spec["frame"], fg="boş" if spec["frame"].get("fg") != "boş" else "korkuluk"))
        if spec["frame"].get("mode") != "A" and fx.FRAME_FG[spec["frame"]["type"]]:
            codes = [i["rule"] for i in es.final_prompt_issues(spec2, scene["structure"]["slices"], scene["prompt"],
                                                                scene["story"])]
            self.assertIn("suffix", codes)


class TestBudget(unittest.TestCase):
    def test_fit_guard_never_leaves_combo_without_fallback(self):
        import frame_budget as fb
        logging.disable(logging.WARNING)
        try:
            for e in (es.FIRE_TORNADO, es.AVALANCHE_SKI, es.PYROCLASTIC):
                with self.subTest(event=e):
                    m = fb.measure(e)
                    self.assertEqual(m["after_fail"], 0)
                    self.assertEqual(m["before_fail"], 0)
        finally:
            logging.disable(logging.NOTSET)


if __name__ == "__main__":
    unittest.main()
