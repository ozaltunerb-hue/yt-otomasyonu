# 21 Kas 2026, Bahadır: Şehir Afeti "⭐ Hit kopyası (ani sel)" modu (core/hit_prompts.py HIT_KOPYA_SEL).
# Kaynak: 4 Kas 2026 01:57 üretimi (5 Kas paylaşımı, 355K izlenme), V12+D17, north_european_seaside. Orman Hit
# kopyası akışı örnek alındı. Şablon Bahadır'ın metni, süslü parantez dışı birebir. GPT yok, metni kod üretir.
# Yasaklar: "bus" ve "GPT" tüm çıktıda alt dize; "building", "facade", "collapse" yalnız M ve F cümlelerinde (görünüm
# metinleri 6'sı da aynen kalır, ikisinde "buildings" geçer). LRU: görünüm (rastgele) son 2, M son 1, F son 2, araç son
# 1, ışık son 1, kişi son 1; kadraj ve ön plan sabit. Diğer bütün olaylar ve modlar 40 tohum birebir aynı. Ağ yok.
import asyncio
import hashlib
import itertools
import json
import logging
import os
import random
import sys
import unittest
from unittest.mock import AsyncMock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts"), os.path.dirname(os.path.abspath(__file__))):
    if p not in sys.path:
        sys.path.insert(0, p)

import test_hit_kopya_orman as tho   # noqa: E402  (önce: core.* döngüsel import sırası)
import core.event_structure as es   # noqa: E402
import core.creative_pipeline as cp   # noqa: E402
import core.hit_prompts as hp   # noqa: E402
import core.prompt_generator as pg   # noqa: E402

FL = es.FLOOD
DOMAIN = "urban_city_disasters"
HKS = hp.HIT_KOPYA_SEL
# Bahadır'ın şablonu, birebir
TEMPLATE = (
    "0-4s: A waist-high wall of brown muddy floodwater surges into the street. {People} people immediately flee from "
    "the overpowering surge. 4-9s: Water rises past the car windows. {M} 9-15s: A second surge, first-floor high, slams "
    "in. {F} Handheld footage filmed on a flat rooftop above a dense downtown street, high vantage; slight hand shake, "
    "the camera stays fixed, tilting only slightly, never descending, the floodwater always in frame, an empty "
    "foreground; one continuous shot, no zoom, no cuts, no person or face close to the camera. All people are ordinary "
    "civilians in everyday clothes, no hazmat suits, natural light, never CGI. Everything moves in real time, never in "
    "slow motion, people run at full speed. Setting: {SETTING}, in {LIGHT}, no readable signs, text or flags.")
# 4 Kas 01:57 üretiminin (5 Kas paylaşımı, 355K) Kie prompt'u, birebir
HIT_PROMPT = (
    "0-4s: A waist-high wall of brown muddy floodwater surges into the street. Five people immediately flee from the "
    "overpowering surge. 4-9s: Water rises past the car windows. The orange delivery truck floats free and is carried "
    "fast down the middle of the street. 9-15s: A second surge, first-floor high, slams in. The surge tips a city bus "
    "onto its side and pushes it along the street. Handheld footage filmed on a flat rooftop above a dense downtown "
    "street, high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never descending, the "
    "floodwater always in frame, an empty foreground; one continuous shot, no zoom, no cuts, no person or face close to "
    "the camera. All people are ordinary civilians in everyday clothes, no hazmat suits, natural light, never CGI. "
    "Everything moves in real time, never in slow motion, people run at full speed. Setting: a city district with "
    "brick terraced houses, narrow streets, bay windows, wet slate roofs, in a dark storm light, no readable signs, "
    "text or flags.")
HIT_F = "The surge tips a city bus onto its side and pushes it along the street."
WATER = ("A waist-high wall of brown muddy floodwater surges into the street.", "Water rises past the car windows.",
         "A second surge, first-floor high, slams in.")
PEOPLE = {5: "Five", 6: "Six", 7: "Seven"}
VEHICLES = ("orange delivery truck", "green delivery van", "white SUV")
MIDS = {"M1": "The {vehicle} floats free and is carried fast down the middle of the street.",
        "M2": "The {vehicle} is caught by the current, turns sideways and is dragged down the street.",
        "M3": "The {vehicle} is lifted, spins around and slams into the parked cars along the street."}
FINALS = {"F1": "The surge lifts the parked cars and carries them down the street, crashing into each other.",
          "F2": "The surge flips a parked car onto its roof and carries it down the street.",
          "F3": "The surge tips a large box truck onto its side and pushes it along the street."}
# Caddelerde ani sel olayının mevcut 6 görünüm metni (skeleton_pipeline.view_district), aynen
SETTINGS = {
    "gulf_metropolis": "a city district with glass towers behind palm-lined boulevards, sand-colored low buildings",
    "north_african_coast": "a city district with sand-colored flat-roofed buildings, narrow streets, cloth awnings, "
                           "arched doorways",
    "us_coastal_town": "a city district with wide asphalt roads, low wooden and brick houses, power lines",
    "north_european_seaside": "a city district with brick terraced houses, narrow streets, bay windows, wet slate roofs",
    "riviera": "a city district with cream stone buildings with shuttered windows, cobbled streets, plane trees",
    "east_asian_coast": "a city district with dense mid-rise apartment blocks with air-conditioners and tangled wires, "
                        "narrow lanes",
}
LIGHTS = ("heavy rain", "driving rain and wind", "a dark storm light")   # sel olayının ışık havuzu, aynen
FORBIDDEN_ALL = ("bus", "GPT")
FORBIDDEN_BEAT = ("building", "facade", "collapse")
VERSION_LINE = "Sürüm: hit_sel v1"
CAMERA_LINE = "Kamera: sabit çatı, boş ön plan (hit ile aynı)"
SOURCE = "Kaynak: 4 Kas 01:57 üretimi (5 Kas paylaşımı, 355K), V12+D17, north_european_seaside, iskelet ve dil"
REPEAT = ("Tekrar önleme: görünüm son 2 (yalnız rastgele) · araç son 1 · M son 1 · F son 2 · ışık son 1 · kişi son 1 · "
          "kadraj ve ön plan sabit")
CAMERA_FIXED = ("Handheld footage filmed on a flat rooftop above a dense downtown street, high vantage; slight hand "
                "shake, the camera stays fixed, tilting only slightly, never descending, the floodwater always in frame, "
                "an empty foreground;")
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "hit_kopya_sel_v1_runs_40.json")

# Değişiklikten önceki kod (1f6a24d): test_hit_kopya_orman kaydı (19 olay + 16 mod) + ⭐ Hit kopyası (orman) v3; 40 tohum
OTHERS_SHA256 = "5aeb3fb1150949f7bed4264588d50ba05bf821a9770911771ea7122d34f457ab"
# ⭐ Hit kopyası (ani sel) v1, 40 tohum kilidi (prompt / hikâye / stil eki / combo / eksenler; caption hariç)
HIT_KOPYA_SEL_SHA256 = "ecdaac4c460778176ea27a535b82a422f1bd94c0c3f8afa01c18880cddf2bb90"


class _Quiet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.disable(logging.WARNING)
        cls._rec = patch.object(cp, "record_story_source", lambda entry: None)
        cls._rec.start()

    @classmethod
    def tearDownClass(cls):
        cls._rec.stop()
        logging.disable(logging.NOTSET)


reset = tho.reset
snapshot_hash = tho.snapshot_hash


def gen(**extra) -> dict:
    return asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": FL, "hit_kopya_sel": True,
                                                     "used_combos": [], "recent_topics": [], **extra}))


def expected(view: str, vehicle: str, mid: str, final: str, n: int, light: str) -> str:
    """Bahadır'ın şablonundan bağımsız kurulum."""
    return TEMPLATE.format(People=PEOPLE[n], M=MIDS[mid].format(vehicle=vehicle), F=FINALS[final],
                           SETTING=SETTINGS[view], LIGHT=light)


def combos():
    return list(itertools.product(SETTINGS, VEHICLES, MIDS, FINALS, PEOPLE, LIGHTS))


def others_snapshot() -> dict:
    """test_hit_kopya_orman kaydı (19 olay + modlar) + ⭐ Hit kopyası (orman yangını) v3; 40 tohum."""
    snap = tho.others_snapshot()
    snap["modes"]["hit_kopya_orman"] = tho.hko_snapshot()
    return snap


def hks_snapshot() -> dict:
    """⭐ Hit kopyası (ani sel) 40 tohum (🎲 Rastgele): prompt, hikâye, stil eki, combo, eksenler (caption hariç)."""
    runs = {}
    for s in range(1, 41):
        reset()
        random.seed(s)
        with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT"))):
            d = gen()
        sc = d["scenes"][0]
        axes = json.loads(d["axes_json"])
        axes.pop("caption", None)
        runs[str(s)] = {"prompt": sc["prompt"], "story": sc["story"], "suffix": sc["style_suffix"],
                        "combo": d["combo_key"], "axes": axes}
    return runs


class TestTemplate(_Quiet):
    def test_template_verbatim(self):
        self.assertEqual(HKS["template"], TEMPLATE)
        for ph in ("{People}", "{M}", "{F}", "{SETTING}", "{LIGHT}"):
            self.assertEqual(TEMPLATE.count(ph), 1, ph)
        self.assertEqual(HKS["tail_start"], "Handheld footage filmed on a flat rooftop")

    def test_constants(self):
        self.assertEqual(hp.HIT_KOPYA_SEL_MODE_LABEL, "⭐ Hit kopyası (ani sel)")
        self.assertEqual(hp.HIT_KOPYA_SEL_EVENTS, (FL,))
        self.assertEqual(hp.HIT_KOPYA_SEL_DOMAIN, DOMAIN)
        self.assertEqual(hp.HIT_KOPYA_SEL_MOD, "hit_kopya_sel")
        self.assertEqual(hp.HIT_KOPYA_SEL_SURUM, "v1")
        self.assertEqual(hp.HIT_KOPYA_SEL_VERSION_LINE, VERSION_LINE)
        self.assertEqual("Kamera: " + hp.HIT_KOPYA_SEL_CAMERA, CAMERA_LINE)
        self.assertEqual(hp.HIT_KOPYA_SEL_SOURCE, SOURCE)
        self.assertEqual((hp.HIT_KOPYA_SEL_MAX_WORDS, hp.HIT_KOPYA_SEL_MAX_CHARS), (230, 1400))
        self.assertEqual((hp.HIT_KOPYA_SEL_VIEW_BLOCK, hp.HIT_KOPYA_SEL_MID_BLOCK, hp.HIT_KOPYA_SEL_FINAL_BLOCK,
                          hp.HIT_KOPYA_SEL_VEHICLE_BLOCK, hp.HIT_KOPYA_SEL_LIGHT_BLOCK, hp.HIT_KOPYA_SEL_PEOPLE_BLOCK),
                         (2, 1, 2, 1, 1, 1))
        self.assertEqual(HKS["people"], ("Five", "Six", "Seven"))
        self.assertEqual(HKS["vehicles"], VEHICLES)
        self.assertEqual(HKS["mids"], MIDS)
        self.assertEqual(HKS["finals"], FINALS)
        self.assertEqual(hp.HIT_KOPYA_SEL_WATER, WATER)
        self.assertEqual(hp.HIT_KOPYA_SEL_FORBIDDEN, FORBIDDEN_ALL)
        self.assertEqual(hp.HIT_KOPYA_SEL_BEAT_FORBIDDEN, FORBIDDEN_BEAT)
        for t in (hp.HIT_KOPYA_SEL_CONFIRM_DESC, hp.HIT_KOPYA_SEL_WARNING, SOURCE, VERSION_LINE, CAMERA_LINE):
            self.assertNotIn("—", t)

    def test_settings_and_lights_are_flood_pools_verbatim(self):
        """SETTING = normal sel hattının 6 görünüm cümlesi, LIGHT = sel ışık havuzu; ikisi de aynen."""
        from core.skeleton_pipeline import EVENT_SKELETONS, REGION_VIEWS, view_district
        self.assertEqual(hp.hit_kopya_sel_views(), list(REGION_VIEWS))
        self.assertEqual(set(SETTINGS), set(REGION_VIEWS))
        for v, text in SETTINGS.items():
            self.assertEqual(hp.hit_kopya_sel_setting(v), text, v)
            self.assertEqual(view_district(FL, v), text, v)
        self.assertEqual(tuple(hp.hit_kopya_sel_lights()), LIGHTS)
        self.assertEqual(tuple(EVENT_SKELETONS[FL]["weather"]), LIGHTS)

    def test_hit_comparison(self):
        """Five + orange delivery truck + M1 + north_european_seaside + a dark storm light: F cümlesi hariç 4 Kas hit
        prompt'uyla birebir."""
        for f, text in FINALS.items():
            p = hp.hit_kopya_sel_prompt("north_european_seaside", "orange delivery truck", "M1", f, 5,
                                        "a dark storm light")
            self.assertEqual(p.count(text), 1)
            self.assertEqual(p.replace(text, HIT_F), HIT_PROMPT, f)
            self.assertEqual(HIT_PROMPT.replace(HIT_F, text), p, f)

    def test_all_combos_within_limits(self):
        words, chars = [], []
        for c in combos():
            p = hp.hit_kopya_sel_prompt(*c)
            self.assertEqual(p, expected(*c), c)
            self.assertEqual(p, hp.hit_kopya_sel_story(*c) + " " + hp.hit_kopya_sel_tail(*c))
            words.append(len(p.split()))
            chars.append(len(p))
        self.assertEqual(len(words), 6 * 3 * 3 * 3 * 3 * 3)
        self.assertEqual(len(words), 1458)
        self.assertLessEqual(max(words), 230)
        self.assertLessEqual(max(chars), 1400)
        self.assertEqual((min(words), max(words)), (165, 173))
        self.assertEqual((min(chars), max(chars)), (993, 1070))

    def test_water_sentences_every_output(self):
        for c in combos():
            p = hp.hit_kopya_sel_prompt(*c)
            for w in WATER:
                self.assertEqual(p.count(w), 1, (c, w))
            self.assertIn(CAMERA_FIXED, p)

    def test_forbidden_words(self):
        """"bus" ve "GPT" hiçbir çıktıda (alt dize, büyük/küçük harf fark etmez); "building", "facade", "collapse" hiçbir
        M ve F cümlesinde."""
        for c in combos():
            view, vehicle, mid, final, n, light = c
            p = hp.hit_kopya_sel_prompt(*c)
            for bad in FORBIDDEN_ALL:
                self.assertNotIn(bad.lower(), p.lower(), (c, bad))
            for beat in (MIDS[mid].format(vehicle=vehicle), FINALS[final]):
                self.assertIn(beat, p)
                for bad in FORBIDDEN_BEAT:
                    self.assertNotIn(bad, beat.lower(), (c, bad))
            self.assertEqual(hp.hit_kopya_sel_text_issues(p, MIDS[mid].format(vehicle=vehicle), FINALS[final]), [], c)
        # görünüm metinleri aynen: ikisinde "buildings" geçer, yasak onlara uygulanmaz
        self.assertIn("buildings", SETTINGS["gulf_metropolis"])
        self.assertIn("buildings", SETTINGS["north_african_coast"])

    def test_mid_final_pools_lock(self):
        """M ve F havuzlarında "building", "facade", "collapse" (ve "bus", "GPT") hiç geçmez; havuzlar 3'er cümle."""
        pools = list(HKS["mids"].values()) + list(HKS["finals"].values())
        self.assertEqual(len(HKS["mids"]), 3)
        self.assertEqual(len(HKS["finals"]), 3)
        for text in pools:
            for v in VEHICLES:
                t = text.format(vehicle=v).lower()
                for bad in FORBIDDEN_BEAT + FORBIDDEN_ALL:
                    self.assertNotIn(bad.lower(), t, (text, bad))
        for text in HKS["mids"].values():
            self.assertEqual(text.count("{vehicle}"), 1)
        for text in HKS["finals"].values():
            self.assertNotIn("{", text)

    def test_text_issues_detect_violations(self):
        c = ("north_european_seaside", "white SUV", "M2", "F3", 6, "heavy rain")
        p = hp.hit_kopya_sel_prompt(*c)
        m, f = MIDS["M2"].format(vehicle="white SUV"), FINALS["F3"]
        for w in WATER:
            self.assertTrue(hp.hit_kopya_sel_text_issues(p.replace(w, "x"), m, f), w)
        for bad in ("a city bus", "GPT", "gpt"):
            self.assertTrue(hp.hit_kopya_sel_text_issues(p + " " + bad, m, f), bad)
        for bad in FORBIDDEN_BEAT:
            self.assertTrue(hp.hit_kopya_sel_text_issues(p, m + f" A {bad}.", f), bad)
            self.assertTrue(hp.hit_kopya_sel_text_issues(p, m, f + f" The {bad.upper()}."), bad)
        # görünüm metnindeki "buildings" ihlal sayılmaz
        g = hp.hit_kopya_sel_prompt("gulf_metropolis", "white SUV", "M2", "F3", 6, "heavy rain")
        self.assertEqual(hp.hit_kopya_sel_text_issues(g, m, f), [])

    def test_bad_ids(self):
        ok = ("riviera", "white SUV", "M1", "F1", 5, "heavy rain")
        for i, bad in ((0, "paris"), (1, "city bus"), (2, "M4"), (3, "F4"), (4, 4), (4, 8), (5, "sunny")):
            args = list(ok)
            args[i] = bad
            with self.assertRaises(es.StructureError, msg=args):
                hp.hit_kopya_sel_prompt(*args)

    def test_event_gate_without_synonym(self):
        for c in combos()[::7]:
            self.assertEqual(pg.event_fidelity_issues(FL, hp.hit_kopya_sel_story(*c)), [], c)
            self.assertEqual(pg.event_fidelity_issues(FL, hp.hit_kopya_sel_prompt(*c)), [], c)


class TestScene(_Quiet):
    def _check(self, d, view=None):
        sc, st = d["scenes"][0], d["structure"]
        tb = st["hit_kopya_sel"]
        if view is not None:
            self.assertEqual((tb["view"], tb["view_source"]), (view, "menü"))
        args = (tb["view"], tb["vehicle"], tb["mid"], tb["final"], tb["people"], tb["light"])
        self.assertEqual(sc["prompt"], expected(*args))
        for w in WATER:
            self.assertIn(w, sc["prompt"])
        self.assertIn(CAMERA_FIXED, sc["prompt"])
        for bad in FORBIDDEN_ALL:
            self.assertNotIn(bad.lower(), sc["prompt"].lower())
        self.assertEqual(d["combo_key"], f"{DOMAIN}|none|{FL.lower()}|flat rooftop above a dense downtown street"
                                         f"##HKS:{tb['view']}|bystander_handheld")
        self.assertIsNone(es.beats_of_combo(d["combo_key"]))
        from core.skeleton_pipeline import view_of_combo
        self.assertIsNone(view_of_combo(d["combo_key"]))   # normal sel görünüm LRU'su etkilenmez
        self.assertEqual(cp.submit_issues(st, {"prompt": sc["prompt"], "story": sc["story"],
                                               "style_suffix": sc["style_suffix"]}), [])
        ax = json.loads(d["axes_json"])
        self.assertEqual(ax["event"], FL)
        a = ax["axes"]
        self.assertEqual((a["mod"], a["surum"], a["gorunum"], a["arac"], a["m"], a["f"], a["kisi"], a["isik"]),
                         ("hit_kopya_sel", "v1") + args[:4] + (tb["people"], tb["light"]))
        for k in ("spot", "view", "light", "vehicle", "people", "beats"):   # normal sel LRU'su bu kaydı saymaz
            self.assertIsNone(a[k], k)
        for other in ("hit_kopya_orman", "hit_kopya_ates", "spec", "hit", "approach"):
            self.assertNotIn(other, st)
        return tb

    def test_40_seeds_no_gpt_no_normal_path_no_frame_axis(self):
        import core.frame_axis as fx
        with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT çağrıldı"))) as gpt, \
             patch.object(pg, "_get_openai_client", side_effect=AssertionError("GPT istemcisi istendi")), \
             patch.object(cp, "build_creative_scene", AsyncMock(side_effect=AssertionError("normal hat"))) as normal, \
             patch.object(fx, "choose_frame", side_effect=AssertionError("kadraj LRU")) as frame:
            seen = {k: set() for k in ("view", "vehicle", "mid", "final", "people", "light")}
            for seed in range(1, 41):
                reset()
                random.seed(seed)
                tb = self._check(gen())
                self.assertEqual(tb["view_source"], "rastgele")
                for k in seen:
                    seen[k].add(tb[k])
        gpt.assert_not_called()
        normal.assert_not_called()
        frame.assert_not_called()
        self.assertEqual(seen["view"], set(SETTINGS))
        self.assertEqual(seen["vehicle"], set(VEHICLES))
        self.assertEqual(seen["mid"], set(MIDS))
        self.assertEqual(seen["final"], set(FINALS))
        self.assertEqual(seen["people"], set(PEOPLE))
        self.assertEqual(seen["light"], set(LIGHTS))

    def test_lru_memory(self):
        for seed in range(1, 11):
            reset()
            random.seed(seed)
            runs = [self._check(gen()) for _ in range(12)]
            for key, block in (("view", 2), ("vehicle", 1), ("mid", 1), ("final", 2), ("light", 1), ("people", 1)):
                v = [r[key] for r in runs]
                for i in range(len(v)):
                    self.assertNotIn(v[i], v[max(0, i - block):i], (seed, key, v))
            self.assertEqual(hp._HIT_KOPYA_SEL_VIEW_MEMORY[-12:], [r["view"] for r in runs])
        self.assertEqual(hp._HIT_KOPYA_ORMAN_GEO_MEMORY, [])   # orman hafızası etkilenmez

    def test_menu_view_fixed(self):
        """Menüden seçilen görünüm aynen gelir (tekrar olsa bile); LRU yalnız 🎲 Rastgele'de."""
        reset()
        random.seed(4)
        for _ in range(4):
            d = gen(view="riviera")
            self._check(d, view="riviera")
            self.assertEqual(json.loads(d["axes_json"])["axes"]["gorunum_kaynak"], "menü")
        reset()
        random.seed(4)
        d = gen(view="riviera")
        self.assertEqual(json.loads(d["axes_json"])["excluded"]["gorunum"], [])
        self.assertIn("Görünüm: riviera «" + SETTINGS["riviera"] + "» (menü)", d["structure"]["hit_kopya_sel"]["lines"])
        # rastgele: son 2 menü seçimi de sayılır
        r = self._check(gen())
        self.assertNotEqual(r["view"], "riviera")
        with self.assertRaises(es.StructureError):
            hp.hit_kopya_sel_build_scene(DOMAIN, FL, view="paris")

    def test_history_sources(self):
        def rec(event=FL, mod="hit_kopya_sel", **axes):
            return {"eksenler": json.dumps({"event": event, "axes": {"mod": mod, **axes}})}
        recs = [rec(gorunum="riviera", arac="white SUV", m="M1", f="F1", isik="heavy rain", kisi=5),
                {"eksenler": "x"},
                rec(gorunum="east_asian_coast", arac="green delivery van", m="M2", f="F2", isik="a dark storm light",
                    kisi=6),
                rec(mod="hit_kopya_orman", gorunum="us_coastal_town", arac="orange delivery truck", m="M3", f="F3"),
                rec(event=es.WILDFIRE, gorunum="gulf_metropolis", m="M3", f="F3")]
        self.assertEqual(hp.hit_kopya_sel_axes_history(recs, "gorunum"), ["riviera", "east_asian_coast"])
        self.assertEqual(hp.hit_kopya_sel_axes_history(recs, "kisi"), [5, 6])
        self.assertIsNone(hp.hit_kopya_sel_axes_history(None, "m"))
        calls = []
        for seed in range(1, 11):
            reset()
            random.seed(seed)
            d = gen(axes_loader=lambda dom: calls.append(dom) or recs)
            tb = self._check(d)
            self.assertNotIn(tb["view"], ("riviera", "east_asian_coast"))
            self.assertNotEqual(tb["vehicle"], "green delivery van")
            self.assertNotEqual(tb["mid"], "M2")
            self.assertEqual(tb["final"], "F3")   # son 2 (F1, F2) elenir
            self.assertNotEqual(tb["light"], "a dark storm light")
            self.assertNotEqual(tb["people"], 6)
            ex = json.loads(d["axes_json"])["excluded"]
            self.assertEqual(ex, {"gorunum": ["riviera", "east_asian_coast"], "arac": ["green delivery van"],
                                  "m": ["M2"], "f": ["F1", "F2"], "isik": ["a dark storm light"], "kisi": [6]})
            self.assertEqual(d["trace"]["axes_source"], "notion")
        self.assertEqual(set(calls), {DOMAIN})

        def broken(dom):
            raise RuntimeError("Notion yok")
        reset()
        random.seed(3)
        d = gen(axes_loader=broken)
        self.assertEqual(d["trace"]["axes_source"], "bellek")
        self._check(d)

    def test_kie_final_check(self):
        reset()
        random.seed(5)
        d = gen()
        st, sc = d["structure"], d["scenes"][0]
        tb = st["hit_kopya_sel"]
        good = {"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"]}
        self.assertEqual(cp.submit_issues(st, good), [])
        for w in WATER:
            self.assertTrue(cp.submit_issues(st, {**good, "prompt": sc["prompt"].replace(w, "x")}), w)
        self.assertTrue(cp.submit_issues(st, {**good, "prompt": sc["prompt"] + " A bus."}))
        self.assertTrue(cp.submit_issues(st, {**good, "style_suffix": "x"}))
        self.assertTrue(cp.submit_issues(st, {**good, "story": sc["story"] + " x"}))
        for key, val in (("mid", "M4"), ("final", "F9"), ("people", 8), ("vehicle", "city bus"), ("light", "sun"),
                         ("view", "paris")):
            self.assertTrue(cp.submit_issues({**st, "hit_kopya_sel": {**tb, key: val}}, good), key)
        other = next(f for f in FINALS if f != tb["final"])
        self.assertTrue(cp.submit_issues({**st, "hit_kopya_sel": {**tb, "final": other}}, good))
        long = sc["prompt"] + " word" * 80
        self.assertTrue(any("kelime" in x for x in hp.hit_kopya_sel_issues(st, {**good, "prompt": long})))
        self.assertEqual(asyncio.run(cp.rewrite_structured(st, "ret", AsyncMock(side_effect=AssertionError("GPT")))),
                         sc["story"])

    def test_approval_lines(self):
        reset()
        random.seed(7)
        d = gen()
        tb = d["structure"]["hit_kopya_sel"]
        lines = tb["lines"].split("\n")
        self.assertEqual(lines[0], "Mod: ⭐ Hit kopyası (ani sel)")
        self.assertEqual(lines[1], VERSION_LINE)
        self.assertEqual(lines[2], SOURCE)
        self.assertEqual(lines[3], f"Görünüm: {tb['view']} «{SETTINGS[tb['view']]}» (rastgele)")
        self.assertEqual(lines[4], f"Araç: {tb['vehicle']}")
        self.assertTrue(lines[5].startswith(f"M (4-9s): {tb['mid']} "))
        self.assertTrue(lines[6].startswith(f"F (9-15s): {tb['final']} "))
        self.assertEqual(lines[7], f"Kişi: {tb['people']}")
        self.assertEqual(lines[8], f"Işık: {tb['light']}")
        self.assertEqual(lines[9], CAMERA_LINE)
        p = tb["prompt"]
        self.assertEqual(lines[10], f"Kelime: {len(p.split())} (en fazla 230) · karakter: {len(p)} (en fazla 1400)")
        self.assertTrue(lines[11].startswith("Eksenler (⭐ Hit kopyası (ani sel)): sürüm=v1 · görünüm="))
        for part in (f"araç={tb['vehicle']}", f"M={tb['mid']}", f"F={tb['final']}", f"kişi={tb['people']}",
                     f"ışık={tb['light']}", "kamera modu=sabit çatı, boş ön plan"):
            self.assertIn(part, lines[11])
        self.assertEqual(lines[12], REPEAT)
        self.assertEqual(lines[13], hp.HIT_KOPYA_SEL_WARNING)
        self.assertEqual(len(lines), 14)
        self.assertNotIn("—", tb["lines"])
        from core.trace_format import format_generation
        text = "\n".join(b for _, b in format_generation(d["trace"]))
        self.assertIn(CAMERA_LINE + "\n", text)


class TestPipelineAndBot(_Quiet):
    def _run(self, approve=True, view=None):
        import main
        from test_tur29_infra import TestPipelineTur29, _Reporter
        seen = {}

        async def fake_gen(config):
            seen["config"] = dict(config)
            reset()
            random.seed(21)
            cfg = {k: v for k, v in config.items() if k not in ("axes_loader", "caption_loader")}
            return await pg.generate_creative_prompts(cfg)
        t = TestPipelineTur29("test_test_mode_never_uploads_and_archives_full_meta")
        t.setUp()
        try:
            rep = _Reporter(approve=approve, needs_approval=True)
            orig = main.run_pipeline

            async def run_with(**kw):
                return await orig(**{**kw, "domain": DOMAIN, "view": view}, hit_kopya_sel=True)
            with patch.object(main, "run_pipeline", run_with):
                r = t.run_pipe(gen=AsyncMock(side_effect=fake_gen), reporter=rep, event=FL)
        finally:
            t.doCleanups()
        return r, rep, seen, t

    def test_pipeline_sends_verbatim_prompt_after_approval(self):
        r, rep, seen, t = self._run(view="us_coastal_town")
        self.assertTrue(r["success"], r)
        self.assertIs(seen["config"]["hit_kopya_sel"], True)
        self.assertEqual(seen["config"]["view"], "us_coastal_town")
        for other in ("hit_kopya_orman", "hit_kopya_ates", "kasirga", "donma_firtina", "approach_env", "hit_env"):
            self.assertNotIn(other, seen["config"])
        approve = [c[1] for c in rep.calls if c[0] == "approve"]
        self.assertEqual(len(approve), 1)
        info = approve[0]
        self.assertTrue(info["hit_lines"].startswith("Mod: ⭐ Hit kopyası (ani sel)\n" + VERSION_LINE + "\n"))
        self.assertIn(CAMERA_LINE, info["hit_lines"])
        self.assertEqual(t.create.await_count, 1)
        self.assertEqual(t.create.await_args.args[1], info["prompt"])
        ax = json.loads(t.tracker.record_axes.call_args_list[0].args[0])["axes"]
        self.assertEqual((ax["mod"], ax["surum"], ax["gorunum"]), ("hit_kopya_sel", "v1", "us_coastal_town"))
        self.assertEqual(info["prompt"], expected(ax["gorunum"], ax["arac"], ax["m"], ax["f"], ax["kisi"], ax["isik"]))

    def test_rejected_approval_no_kie(self):
        r, _, _, t = self._run(approve=False)
        self.assertFalse(r["success"])
        self.assertEqual(t.create.await_count, 0)

    def test_menu_flow(self):
        import bot
        from test_tur29_infra import _context, _update
        di = str(bot.DOMAIN_KEYS.index(DOMAIN))
        ctx = _context()
        upd = _update(data=f"uret:d:{di}")
        asyncio.run(bot.on_callback(upd, ctx))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        rows = [[b.text for b in r] for r in kb.inline_keyboard]
        self.assertEqual(rows[-2:], [["⭐ Hit kopyası (ani sel)"], ["🔙 Geri"]])
        self.assertEqual(rows[-3], ["🎲 Rastgele"])
        self.assertEqual(kb.inline_keyboard[-2][0].callback_data, "uret:hks")
        # görünüm menüsü: 6 görünüm + 🎲 Rastgele + Geri
        upd = _update(data="uret:hks")
        asyncio.run(bot.on_callback(upd, ctx))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        btns = [b for r in kb.inline_keyboard for b in r]
        self.assertEqual([b.text for b in btns], [bot.VIEW_LABELS[v] for v in bot.VIEW_KEYS] + ["🎲 Rastgele", "⬅️ Geri"])
        self.assertEqual([b.callback_data for b in btns],
                         [f"uret:hks:{i}" for i in range(6)] + ["uret:hks:r", f"uret:d:{di}"])
        vi = str(bot.VIEW_KEYS.index("north_european_seaside"))
        upd = _update(data=f"uret:hks:{vi}")
        asyncio.run(bot.on_callback(upd, ctx))
        call = upd.callback_query.edit_message_text.await_args
        text = call.args[0]
        for part in ("Bölge: 🏘️ Kuzey Avrupa sahili", "Mod: ⭐ Hit kopyası (ani sel)", VERSION_LINE, SOURCE,
                     CAMERA_LINE, hp.HIT_KOPYA_SEL_CONFIRM_DESC, "✋ Onay"):
            self.assertIn(part, text)
        self.assertNotIn("—", text)
        self.assertEqual([b.callback_data for r in call.kwargs["reply_markup"].inline_keyboard for b in r],
                         [f"uret:hksok:{vi}", "uret:x"])
        for vid, view in ((vi, "north_european_seaside"), ("r", None)):
            upd = _update(data=f"uret:hksok:{vid}")
            runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
            with patch.object(bot.pipeline, "run_pipeline", runner), \
                 patch.object(bot, "_production_lock", asyncio.Lock()):
                asyncio.run(bot.on_callback(upd, ctx))
            kw = runner.await_args.kwargs
            self.assertEqual((kw["domain"], kw["event"], kw["view"], kw["hit_kopya_sel"]), (DOMAIN, FL, view, True))
            for other in ("hit_kopya_orman", "hit_kopya_ates", "kasirga", "donma_firtina", "dalga24", "hit_env"):
                self.assertNotIn(other, kw)
            self.assertTrue(kw["reporter"].needs_approval)
            self.assertIn("/ ⭐ Hit kopyası (ani sel)", upd.callback_query.edit_message_text.await_args_list[0].args[0])
        for bad in ("uret:hks:9", "uret:hks:x", "uret:hksok", "uret:hksok:7", "uret:hksok:1:2"):
            upd = _update(data=bad)
            asyncio.run(bot.on_callback(upd, ctx))
            self.assertIn("Geçersiz", upd.callback_query.edit_message_text.await_args.args[0], bad)
        busy = asyncio.Lock()
        asyncio.run(busy.acquire())
        with patch.object(bot, "_production_lock", busy):
            upd = _update(data="uret:hksok:r")
            asyncio.run(bot.on_callback(upd, ctx))
            self.assertEqual(upd.callback_query.edit_message_text.await_args.args[0], bot.BUSY_TEXT)
        for m in (bot.hit_kopya_sel_view_keyboard(), bot.hit_kopya_sel_produce_keyboard("r")):
            for b in (b for r in m.inline_keyboard for b in r):
                self.assertLessEqual(len(b.callback_data.encode()), 64)

    def test_other_domains_no_button(self):
        import bot
        for i, d in enumerate(bot.DOMAIN_KEYS):
            if d == DOMAIN or not bot.domain_active(d):
                continue
            cbs = [b.callback_data for r in bot.event_keyboard(i).inline_keyboard for b in r]
            self.assertNotIn("uret:hks", cbs, d)

    def test_normal_flood_flow_unchanged(self):
        """Normal sel akışı (olay → bölge menüsü) aynen: Hit kopyası düğmesi orada yok."""
        import bot
        from test_tur29_infra import _context, _update
        di, ei = str(bot.DOMAIN_KEYS.index(DOMAIN)), str(bot.domain_events(DOMAIN).index(FL))
        upd = _update(data=f"uret:e:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, _context()))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        self.assertEqual([b.callback_data for r in kb.inline_keyboard for b in r],
                         [b.callback_data for r in bot.view_keyboard(di, ei).inline_keyboard for b in r])

    def test_only_flood(self):
        for e in es.EVENT_SKELETONS:
            self.assertEqual(hp.hit_kopya_sel_is_active(e), e == FL, e)
        with self.assertRaises(es.StructureError):
            hp.hit_kopya_sel_build_scene(DOMAIN, es.WILDFIRE)
        with self.assertRaises(es.StructureError):
            hp.hit_kopya_sel_build_scene("fire_disasters", FL)


class TestLocks(_Quiet):
    """Bu mod dışındaki bütün olaylar ve modlar (önceki kod 1f6a24d) 40 tohum birebir; bu modun kilidi
    HIT_KOPYA_SEL_SHA256 + fixture hit_kopya_sel_v1_runs_40.json."""

    def test_others_verbatim_40_seeds(self):
        snap = others_snapshot()
        self.assertEqual(len(snap["events"]), 19)
        for name, runs in snap["modes"].items():
            for s, r in runs.items():
                self.assertNotIn("error", r, (name, s))
        self.assertNotIn("hit_kopya_sel", snap["modes"])
        self.assertEqual(snapshot_hash(snap), OTHERS_SHA256)

    def test_hit_kopya_sel_lock_and_fixture(self):
        runs = hks_snapshot()
        self.assertEqual(len(runs), 40)
        with open(FIXTURE, encoding="utf-8") as f:
            fixture = json.load(f)
        self.assertEqual(runs, fixture)
        self.assertEqual(snapshot_hash(fixture), HIT_KOPYA_SEL_SHA256)
        for s, r in runs.items():
            ax = r["axes"]["axes"]
            self.assertEqual((ax["mod"], ax["surum"]), ("hit_kopya_sel", "v1"))
            self.assertEqual(r["prompt"], expected(ax["gorunum"], ax["arac"], ax["m"], ax["f"], ax["kisi"], ax["isik"]))
            self.assertTrue(r["combo"].endswith(f"##HKS:{ax['gorunum']}|bystander_handheld"), s)

    def test_locked_events_hash_file(self):
        import locked_prompts as lp
        self.assertEqual(lp.hashes(), lp.load())


if __name__ == "__main__":
    unittest.main()
