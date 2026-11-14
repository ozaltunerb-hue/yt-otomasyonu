# 13 Kas 2026, Bahadır: helikopter "⭐ Hit kalıbı · Yaklaşma" modu (core/hit_prompts.py YAKLASMA_HELIKOPTER).
# Göl kenarındaki kasabada yangın; helikopter çelik halatın ucundaki büyük kovayı gölden doldurup yangının üstüne boşaltır.
# GPT yok, zaman etiketleri var. Suyun öznesi her zaman kova ("helicopter's" yok). Helikopterin normal yolu ve diğer
# bütün olay/modlar değişmez. Ağ yok.
# 14 Kas 2026: su yangına kovadan; helikopter kameraya gelmez, kamera her zaman sabit, finallerde "terrace"/"toward the camera" yok.
# 14 Kas 2026 (2): kova kaldırıldı; gövde tanklı ağır helikopter (hortumla emer, "belly tank"tan boşaltır), yangın evlerin
# içinde. "bucket", "cable", "helicopter's" ve "toward the camera" hiçbir prompt'ta yok. Kovalı metinler *_V2 (pasif).
# 14 Kas 2026 (3) v4: S-64 Skycrane, hedef terasın karşısındaki yanan evler, ortalar "Across the street" ve hepsi araçlı,
# finaller J1/J2. "streaming"/"sucking" yok, "S-64 Skycrane" ve "belly tank" zorunlu. 97d3b76 metinleri *_V3 (pasif).
# 14 Kas 2026 (4) v5: kamera yangın tarafında yüksek binanın en üst kat balkonunda ("high vantage"), göl uzakta, hortumun
# ucu suya batık, su kameranın önündeki yanan çatılara. "terrace", "spray", "pouring" yasak. b925c79 metinleri *_V4.
# 14 Kas 2026 (5) v6: göl sahnesi gölden kalkan, hortumundan su damlayan Skycrane; ortalar aşağıdaki caddede ve sert (hepsi
# "Down in the street"), finalde çatı çöküyor. "sunk" ve "a SUV" yasak; H2'de artikel kodda. 5a78f75 metinleri *_V5.
import asyncio
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

import core.event_structure as es   # noqa: E402
import core.creative_pipeline as cp   # noqa: E402
import core.hit_prompts as hp   # noqa: E402
import core.prompt_generator as pg   # noqa: E402
import core.skeleton_pipeline as sk   # noqa: E402
import prompt_snapshot as ps   # noqa: E402
from core.trace_format import format_final_prompt, format_generation, sections_to_text   # noqa: E402

HE = es.HELICOPTER
HL = hp.YAKLASMA_HELIKOPTER
DOMAIN = "fire_disasters"
FOLLOW = "the camera turns slightly to follow the helicopter"
FIXED = "the camera stays fixed"
PLACES = {"L1": ("Kanada", "a Canadian lakeside town of log houses below snowy peaks"),
          "L2": ("Kaliforniya", "a lakeside mountain town of wooden cabins among tall pines"),
          "L3": ("İtalya", "an Italian lakeside town of terracotta villas and cypress trees"),
          "L4": ("İsviçre", "a Swiss lakeside village of wooden chalets below the Alps"),
          "L5": ("Yunanistan", "a Greek lakeside village of whitewashed houses and olive trees"),
          "L6": ("Avustralya", "an Australian lakeside town of weatherboard houses among eucalyptus")}
MIDS = {
    "H1": "Down in the street, a wall of flames engulfs a fleeing {vehicle}, as the Skycrane flies in from the lake.",
    "H2": "Down in the street, a huge burning pine crashes onto {art} {vehicle} trying to escape, as the Skycrane "
          "flies in from the lake.",
    "H3": "Down in the street, the flames reach a parked {vehicle} and it explodes into a fireball, as the Skycrane "
          "flies in from the lake.",
}
FINALS = {
    "J1": "The Skycrane stops right above the burning houses below, in front of the camera, and dumps its belly tank "
          "onto a burning roof, the roof caving in with a blast of steam and sparks.",
    "J2": "The Skycrane sweeps low over the burning roofs below, in front of the camera, releasing its belly tank onto "
          "the flames, a roof collapsing in a blast of steam and sparks.",
}
OPENING = ("Wildfire is burning through {place}, the houses right below engulfed in flames, embers raining onto the "
           "street, while on the distant lake an orange S-64 Skycrane rises off the water, water dripping from the "
           "long hose hanging from its belly.")
TAIL = ("Handheld footage from the top-floor balcony of a tall building, high vantage looking steeply down on the "
        "burning houses and the street, the lake far in the distance beyond them, the Skycrane large in frame, never "
        "flying over the camera, a corner of the balcony railing in the foreground; slight hand shake, the camera stays "
        "fixed; one continuous shot, no zoom, no cuts. Water comes only out of the belly tank and lands right on the "
        "burning roofs, never on the camera. Realistic wildfire: towering, roaring flames and thick smoke, never thin "
        "lines of fire. Real time, never slow motion. No readable signs, text or flags.")
WATER_LINE = "Water comes only out of the belly tank and lands right on the burning roofs, never on the camera."
NEVER_ANY = ("helicopter's", "bucket", "cable", "terrace", "streaming", "sucking", "spray", "pouring", "sunk",
             "toward the camera", "a SUV")
REQUIRED = ("S-64 Skycrane", "belly tank", "high vantage", "water dripping from the long hose")
DRIP = "water dripping from the long hose"


def fill(m: str, v: str) -> str:
    return MIDS[m].format(vehicle=v, art="an" if v == "SUV" else "a")
VEHICLE_WORDS = ("pickup", "truck", "SUV", "van", "car", "vehicle", "{")


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


def reset():
    ps.reset_memory()
    for name in dir(hp):
        if name.startswith("_") and name.endswith("_MEMORY") and isinstance(getattr(hp, name), list):
            getattr(hp, name).clear()


def gen(**extra) -> dict:
    return asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": HE, "heli_yaklasma": True,
                                                     "used_combos": [], "recent_topics": [], **extra}))


def build(seed: int) -> dict:
    reset()
    random.seed(seed)
    return gen()


def all_combos():
    for g in HL["geos"]:
        for ppl in (3, 4):
            for v in HL["vehicles"]:
                for m in HL["mids"]:
                    for f in HL["finals"]:
                        for follow in (True, False):
                            yield (g, ppl, v, m, f, follow), hp.heli_prompt(g, ppl, m, v, f, follow)


class TestTexts(_Quiet):
    def test_verbatim_texts(self):
        self.assertEqual(hp.HELI_MODE_LABEL, "⭐ Hit kalıbı · Yaklaşma (helikopter)")
        self.assertIs(hp.HELI_YAKLASMA_KAMERA_TAKIP, False)
        self.assertEqual({g: (HL["geos"][g]["name"], HL["geos"][g]["place"]) for g in HL["geos"]}, PLACES)
        for g, (_, place) in PLACES.items():
            self.assertEqual(hp.heli_opening(g), OPENING.format(place=place))
        self.assertEqual(hp.heli_people(3), "Three people run below.")
        self.assertEqual(hp.heli_people(4), "Four people run below.")
        for n in (2, 5):
            with self.assertRaises(es.StructureError):
                hp.heli_people(n)
        self.assertEqual(HL["vehicles"], ("pickup truck", "SUV", "white van"))
        self.assertEqual(HL["mids"], MIDS)
        self.assertEqual(HL["finals"], FINALS)
        self.assertEqual(hp.heli_camera_text(True), FIXED)   # 14 Kas: takip bu modda yok
        self.assertEqual(hp.heli_camera_text(False), FIXED)
        self.assertEqual(hp.heli_tail(True), TAIL)
        self.assertEqual(hp.heli_tail(False), TAIL)
        self.assertEqual(hp.heli_camera_label(True), "sabit")
        # eski metinler silinmedi, pasif kayıtta
        self.assertIn("Right below the terrace", hp.HELI_FINALS_V1["J1"])
        self.assertEqual(hp.HELI_CAMERA_V1[True], FOLLOW)
        self.assertIn("filling the big bucket on its steel cable", hp.HELI_OPENING_V1)
        self.assertIn("{camera}", hp.HELI_TAIL_V1)
        self.assertIn("water dripping from the bucket", hp.HELI_MIDS_V1["H1"])
        # 14 Kas (2): 96b3d25 kovalı metinler silinmedi, pasif kayıtta
        self.assertIn("bucket hanging on a long steel cable far below it", hp.HELI_OPENING_V2)
        self.assertIn("the full bucket swinging far below on its cable", hp.HELI_MIDS_V2["H1"])
        self.assertIn("the hanging bucket opens", hp.HELI_FINALS_V2["J1"])
        self.assertIn("Water falls only out of the bottom of the hanging bucket", hp.HELI_TAIL_V2)
        self.assertEqual(set(hp.HELI_MIDS_V2), {"H1", "H2", "H3"})
        self.assertEqual(set(hp.HELI_FINALS_V2), {"J1", "J2", "J3"})
        # 14 Kas (3): 97d3b76 gövde tanklı metinler silinmedi, pasif kayıtta
        self.assertIn("sucking water into its belly tank through a thick hanging hose", hp.HELI_OPENING_V3)
        self.assertIn("water streaming from its hanging hose", hp.HELI_MIDS_V3["H1"])
        self.assertEqual(set(hp.HELI_MIDS_V3), {"H1", "H2", "H3"})
        self.assertEqual(set(hp.HELI_FINALS_V3), {"J1", "J2", "J3"})
        self.assertEqual(hp.HELI_VEHICLE_MIDS_V3, ("H2", "H3"))
        self.assertEqual(hp.HELI_PEOPLE_V3[3], "Three people run along the lakeshore below.")
        self.assertEqual(hp.HELI_GEOS_V3["L1"], "a Canadian lakeside town of timber houses")
        self.assertIn("never flying toward or over the camera", hp.HELI_TAIL_V3)
        self.assertIn("Never CGI.", hp.HELI_TAIL_V3)
        self.assertNotIn("Never CGI", TAIL)
        # 14 Kas (4): b925c79 v4 metinleri silinmedi, pasif kayıtta
        self.assertIn("the houses across the street from the terrace are on fire", hp.HELI_OPENING_V4)
        self.assertIn("its snorkel hose dipped into the water", hp.HELI_OPENING_V4)
        self.assertEqual(hp.HELI_PEOPLE_V4[3], "Three people run along the street below.")
        self.assertEqual(set(hp.HELI_MIDS_V4), {"H1", "H2", "H3"})
        self.assertIn("lifts off the lake", hp.HELI_MIDS_V4["H1"])
        self.assertEqual(set(hp.HELI_FINALS_V4), {"J1", "J2"})
        self.assertIn("burning houses across the street", hp.HELI_FINALS_V4["J1"])
        self.assertIn("Handheld footage shot from a high terrace", hp.HELI_TAIL_V4)
        self.assertIn("never over the camera", hp.HELI_TAIL_V4)
        # 14 Kas (5): 5a78f75 v5 metinleri silinmedi, pasif kayıtta
        self.assertIn("its end sunk deep in the water, filling its belly tank", hp.HELI_OPENING_V5)
        self.assertEqual(set(hp.HELI_MIDS_V5), {"H1", "H2", "H3"})
        self.assertIn("as a {vehicle} speeds away", hp.HELI_MIDS_V5["H3"])
        self.assertEqual(set(hp.HELI_FINALS_V5), {"J1", "J2"})
        self.assertIn("a massive curtain of water exploding into white steam", hp.HELI_FINALS_V5["J1"])
        self.assertIn("its end sunk deep in the water", hp.HELI_REQUIRED_V5)
        self.assertEqual(hp.HELI_FORBIDDEN, NEVER_ANY)
        self.assertEqual(hp.HELI_REQUIRED, REQUIRED)
        self.assertEqual((hp.HELI_NO_FLY_PHRASE, hp.HELI_NO_WATER_ON_CAMERA),
                         ("never flying over the camera", "never on the camera"))
        self.assertEqual((hp.HELI_GEO_BLOCK, hp.HELI_VEHICLE_BLOCK, hp.HELI_MID_BLOCK, hp.HELI_FINAL_BLOCK),
                         (3, 2, 1, 1))
        self.assertEqual((hp.HELI_MAX_WORDS, hp.HELI_MAX_CHARS), (230, 1400))

    def test_vehicle_fill(self):
        """14 Kas (5) v6: üç orta da araçlı ve "Down in the street" ile başlar; H2'de SUV için "an SUV"."""
        for v in HL["vehicles"]:
            for m in ("H1", "H2", "H3"):
                self.assertEqual(hp.heli_mid(m, v), fill(m, v))
                self.assertTrue(hp.heli_mid(m, v).startswith("Down in the street, "))
                self.assertTrue(hp.heli_mid(m, v).endswith(", as the Skycrane flies in from the lake."))
                self.assertNotIn("a SUV", hp.heli_mid(m, v))
            self.assertIn(f"engulfs a fleeing {v}, as the Skycrane", hp.heli_mid("H1", v))
            self.assertIn(f"reach a parked {v} and it explodes into a fireball", hp.heli_mid("H3", v))
        self.assertIn("crashes onto an SUV trying to escape", hp.heli_mid("H2", "SUV"))
        self.assertIn("crashes onto a pickup truck trying to escape", hp.heli_mid("H2", "pickup truck"))
        self.assertIn("crashes onto a white van trying to escape", hp.heli_mid("H2", "white van"))
        self.assertEqual([hp.heli_article(x) for x in ("SUV", "pickup truck", "white van", "ambulance")],
                         ["an", "a", "a", "an"])
        for m in ("H1", "H2", "H3"):
            with self.assertRaises(es.StructureError):
                hp.heli_mid(m, None)
        self.assertEqual(HL["vehicle_mids"], ("H1", "H2", "H3"))
        for bad in ("M1", "H4", "F1"):
            with self.assertRaises(es.StructureError):
                hp.heli_mid(bad, "SUV")
        for bad in ("J3", "J4"):
            with self.assertRaises(es.StructureError):
                hp.heli_final(bad)

    def test_all_combos_within_limits(self):
        """Coğrafya × kişi × araç × orta × final × kamera: hepsi ≤ 230 kelime, ≤ 1400 karakter + metin kuralları."""
        n, over, longest = 0, [], (0, 0, None)
        for key, p in all_combos():
            n += 1
            g, _, v, m, f, follow = key
            w, c = len(p.split()), len(p)
            longest = max(longest, (w, c, key))
            if w > hp.HELI_MAX_WORDS or c > hp.HELI_MAX_CHARS:
                over.append((key, w, c))
            self.assertIn(PLACES[g][1], p)
            for bad in ("Turkish", "Turkey", "Full action", "Until the last frame"):
                self.assertNotIn(bad, p)
            for bad in NEVER_ANY:
                self.assertNotIn(bad.lower(), p.lower())
            self.assertIn(WATER_LINE, p)
            self.assertIn("never thin lines of fire", p)
            for need in ("never flying over the camera", "never on the camera", "the camera stays fixed") + REQUIRED:
                self.assertIn(need, p)
            self.assertEqual(p.count("over the camera"), 1, key)   # sadece "never flying over the camera"
            self.assertEqual(p.count("on the camera"), 1, key)   # sadece "never on the camera"
            self.assertNotIn("turns slightly to follow", p)
            self.assertEqual(hp.heli_camera_issues(p, g), [], key)
            self.assertIn("a corner of the balcony railing in the foreground", p)
            self.assertTrue(p.startswith("0-4s: "))
            for lab in (" 4-9s: ", " 9-15s: "):
                self.assertIn(lab, p)
            opening, rest = p.split(" 4-9s: ")
            self.assertNotIn("belly tank", opening)   # v6: açılışta tank yok, su hortumdan damlar
            self.assertIn("hanging from its belly.", opening)
            self.assertIn("the houses right below engulfed in flames", opening)
            self.assertIn("S-64 Skycrane", opening)
            self.assertIn("rises off the water", opening)
            self.assertIn("embers raining onto the street", opening)
            self.assertIn(DRIP, opening)
            self.assertNotIn("terrace", p.lower(), key)
            mid_part, final_part = rest.split(" 9-15s: ")
            final_part = final_part.split(" Handheld footage")[0]
            self.assertEqual(final_part, FINALS[f])
            self.assertIn("belly tank", final_part, key)
            self.assertIn(" below, in front of the camera, ", final_part, key)
            self.assertIn("blast of steam and sparks", final_part, key)
            self.assertTrue(mid_part.startswith("Down in the street, "), key)
            self.assertEqual(mid_part, fill(m, v), key)
            self.assertIn("flies in from the lake", mid_part, key)
            for bad in ("terrace", "toward the camera", "over the camera", "on the camera"):
                self.assertNotIn(bad, final_part, key)
                self.assertNotIn(bad, mid_part, key)
            self.assertIn(f" {v}", mid_part, key)
            self.assertEqual(sum(f" {x}" in mid_part for x in HL["vehicles"]), 1, key)
            self.assertIn(f"slight hand shake, {FIXED}; one continuous shot", p)   # takip parametresi etkisiz
            pos = [p.find(x) for x in ("0-4s: ", " people run below.", " 4-9s: ", " 9-15s: ",
                                       " Handheld footage")]
            self.assertNotIn(-1, pos)
            self.assertEqual(pos, sorted(pos))
        self.assertEqual(n, 6 * 2 * 3 * 3 * 2 * 2)
        self.assertEqual(over, [], f"en uzun: {longest}")

    def test_water_source_is_always_the_belly_tank(self):
        """14 Kas (4): kova yok; su gövde altındaki tanktan ("belly tank"), kameranın önündeki aşağıdaki yanan çatılara."""
        for f, text in FINALS.items():
            self.assertIn("belly tank", text, f)
            self.assertIn("in front of the camera", text, f)
            for bad in ("terrace", "toward the camera", "over the camera", "on the camera"):
                self.assertNotIn(bad, text, f)
            self.assertIn("blast of steam and sparks", text, f)
            self.assertIn("roof", text, f)
        self.assertIn("belly tank", TAIL)
        self.assertIn(DRIP, OPENING)
        self.assertIn("rises off the water", OPENING)
        self.assertIn("high vantage", TAIL)
        self.assertIn(WATER_LINE, TAIL)
        for text in list(MIDS.values()) + list(FINALS.values()) + [OPENING, TAIL]:
            for bad in NEVER_ANY:
                self.assertNotIn(bad.lower(), text.lower())

    def test_sentences_only_in_this_mode(self):
        marks = [OPENING.split("{place}")[1], "S-64 Skycrane", "Skycrane",
                 "Three people run below.", "Four people run below.",
                 MIDS["H1"].split("{vehicle}")[1], MIDS["H2"].split("{vehicle}")[1], MIDS["H3"].split("{vehicle}")[1],
                 *FINALS.values(), WATER_LINE, DRIP,
                 "Handheld footage from the top-floor balcony of a tall building, high vantage",
                 *[p for _, p in PLACES.values()]]
        # not: "a corner of the ... railing in the foreground" kalıbı başka modların stil ekinde de var (ortak ifade)
        pools = json.dumps({e: {s: {k: v["text"] for k, v in b[s].items()} for s in ("slice_2", "slice_3")}
                            for e, b in es.EVENT_BEATS.items()}, ensure_ascii=False)
        others = (pools + json.dumps(hp.HIT_PROMPTS, ensure_ascii=False)
                  + json.dumps(hp.YAKLASMA_ATES_HORTUMU, default=str, ensure_ascii=False)
                  + json.dumps(hp.DALGA_24EYLUL, default=str, ensure_ascii=False)
                  + json.dumps(hp.YAKLASMA_KUL_BULUTU, default=str, ensure_ascii=False)
                  + json.dumps(hp.KUL_PASIF, default=str, ensure_ascii=False)
                  + json.dumps(hp.YAKLASMA_ORMAN, default=str, ensure_ascii=False)
                  + json.dumps(hp.ORMAN_PASIF, default=str, ensure_ascii=False)
                  + json.dumps(es.EVENT_KEY_VISUAL, ensure_ascii=False))
        for ev in ps.active_events():
            for seed in range(1, 6):
                others += json.dumps(ps.snapshot_event(ev, seed), ensure_ascii=False)
        for m in marks:
            self.assertNotIn(m, others, m)


class TestHeliMode(_Quiet):
    def _check(self, d):
        sc, st = d["scenes"][0], d["structure"]
        hb = st["heli_yaklasma"]
        prompt = sc["prompt"]
        self.assertIn(hb["geo"], PLACES)
        self.assertIn(PLACES[hb["geo"]][1], prompt)
        self.assertEqual(sum(pl in prompt for _, pl in PLACES.values()), 1)
        self.assertTrue(prompt.startswith(f"0-4s: {hp.heli_opening(hb['geo'])} {hp.heli_people(hb['people'])} 4-9s: "))
        self.assertIn(hb["vehicle"], HL["vehicles"])
        self.assertIn(hb["mid"], HL["mids"])
        self.assertIn(hb["final"], HL["finals"])
        mid_text = hp.heli_mid(hb["mid"], hb["vehicle"])
        self.assertIn(f" 4-9s: {mid_text} 9-15s: {FINALS[hb['final']]} Handheld footage", prompt)
        for bad in ("Full action", "Until the last frame", "Turkish", "Turkey", sk.FULL_MOTION):
            self.assertNotIn(bad, prompt)
        for bad in NEVER_ANY:
            self.assertNotIn(bad, prompt.lower())
        for need in REQUIRED:
            self.assertIn(need, prompt)
        self.assertTrue(prompt.endswith(" " + hp.heli_tail(hb["follow"])))
        self.assertEqual(sc["style_suffix"], hp.heli_tail(hb["follow"]))
        self.assertLessEqual(len(prompt.split()), 230)
        self.assertLessEqual(len(prompt), 1400)
        self.assertIn(f"#{hb['mid']}+{hb['final']}|", d["combo_key"])
        for slot in ("slice_2", "slice_3"):   # normal helikopter havuzu (F*/G*) metni yok
            for bid in es.EVENT_BEATS[HE][slot]:
                self.assertNotIn(es.beat_text(HE, slot, bid)[4:], prompt)
        self.assertNotIn(es.EVENT_KEY_VISUAL[HE], prompt)
        self.assertEqual(cp.submit_issues(st, {"prompt": prompt, "story": sc["story"],
                                               "style_suffix": sc["style_suffix"]}), [])
        return hb

    def test_50_seeds_every_mid_and_final(self):
        mids, finals, geos = set(), set(), set()
        for seed in range(1, 51):
            reset()
            random.seed(seed)
            for i in range(3):
                with self.subTest(seed=seed, i=i):
                    hb = self._check(gen())
                    mids.add(hb["mid"])
                    finals.add(hb["final"])
                    geos.add(hb["geo"])
        self.assertEqual(mids, {"H1", "H2", "H3"})
        self.assertEqual(finals, {"J1", "J2"})
        self.assertEqual(geos, set(PLACES))
        self.assertIsNone(es.HIT_OVERRIDE.get())

    def test_consecutive_lru(self):
        """Coğrafya ardışık 3 üretimde tekrar etmez; araç son 2; orta ve final arka arkaya tekrar etmez."""
        for seed in range(1, 16):
            reset()
            random.seed(seed)
            runs = [self._check(gen()) for _ in range(9)]
            for key, block in (("geo", 3), ("vehicle", 2), ("mid", 1), ("final", 1)):
                vals = [r[key] for r in runs]
                for i in range(len(vals)):
                    self.assertNotIn(vals[i], vals[max(0, i - block):i], (seed, key, vals))
            self.assertTrue({r["people"] for r in runs} <= {3, 4})

    def test_history_sources(self):
        def combo(tag):
            return f"{DOMAIN}|none|{HE.lower()}|high terrace##{tag}|bystander_handheld"
        reset()
        hist = [combo("H1+J1"), combo("F2+G6"), combo("H3+J2")]
        for s in range(30):
            self.assertIn(hp.heli_choose_mid(hist, random.Random(s)), ("H1", "H2"))   # son 1: H3 elenir
            self.assertEqual(hp.heli_choose_final(hist, random.Random(s)), "J1")   # son 1: J2 elenir
        recs = [{"eksenler": json.dumps({"event": HE, "axes": {"mod": "heli_yaklasma", "cografya": g, "arac": v}})}
                for g, v in (("L2", "SUV"), ("L3", "white van"), ("L4", "SUV"))] + [{"eksenler": "x"}]
        recs.append({"eksenler": json.dumps({"event": es.WILDFIRE, "axes": {"mod": "orman_yaklasma",
                                                                             "cografya": "L1", "arac": "pickup truck"}})})
        self.assertEqual(hp.heli_axes_history(recs, "cografya"), ["L2", "L3", "L4"])
        self.assertEqual(hp.heli_axes_history(recs, "arac"), ["SUV", "white van", "SUV"])
        self.assertIsNone(hp.heli_axes_history(None, "arac"))
        for seed in range(1, 11):
            reset()
            random.seed(seed)
            d = gen(axes_loader=lambda dom: recs)
            hb = d["structure"]["heli_yaklasma"]
            self.assertIn(hb["geo"], ("L1", "L5", "L6"))
            self.assertEqual(hb["vehicle"], "pickup truck")
            axes = json.loads(d["axes_json"])["axes"]
            self.assertEqual((axes["mod"], axes["cografya"], axes["arac"]), ("heli_yaklasma", hb["geo"], hb["vehicle"]))

    def test_camera_always_fixed(self):
        """14 Kas: kamera her zaman sabit; bayrak True olsa bile takip cümlesi çıkmaz."""
        for seed in range(1, 6):
            d = build(seed)
            p = d["scenes"][0]["prompt"]
            self.assertIn(f"slight hand shake, {FIXED}; one continuous shot", p)
            self.assertNotIn(FOLLOW, p)
            self.assertIs(d["structure"]["heli_yaklasma"]["follow"], False)
        with patch.object(hp, "HELI_YAKLASMA_KAMERA_TAKIP", True):
            for seed in range(1, 11):
                d = build(seed)
                self._check(d)
                p = d["scenes"][0]["prompt"]
                self.assertIn(f"slight hand shake, {FIXED}; one continuous shot", p)
                self.assertNotIn(FOLLOW, p)
                self.assertIn("Kamera: sabit", d["structure"]["heli_yaklasma"]["lines"])

    def test_no_gpt_rewrite_tampering(self):
        with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT çağrıldı"))) as gpt, \
             patch.object(pg, "_get_openai_client", side_effect=AssertionError("GPT istemcisi istendi")):
            d = build(7)
        gpt.assert_not_called()
        sc, st = d["scenes"][0], d["structure"]
        info = {"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"]}
        self.assertEqual(cp.submit_issues(st, info), [])
        self.assertTrue(cp.submit_issues(st, {**info, "prompt": sc["prompt"].replace(
            "No readable signs", f"{sk.FULL_MOTION} No readable signs")}))
        # 14 Kas: Kie öncesi son kontrol, kamera/teras ifadeleri yalnız izinli yerlerde
        for old_s, new_s in ((" 9-15s: The Skycrane", " 9-15s: Right below the terrace, the Skycrane"),
                             (" 9-15s: The Skycrane", " 9-15s: Moving toward the camera, the Skycrane"),
                             (" 9-15s: The Skycrane", " 9-15s: Flying over the camera, the Skycrane"),
                             (" 9-15s: The Skycrane", " 9-15s: Water splashes on the camera, the Skycrane"),
                             ("No readable signs", "The camera turns slightly to follow the helicopter. No readable signs")):
            bad_prompt = sc["prompt"].replace(old_s, new_s, 1)
            self.assertNotEqual(bad_prompt, sc["prompt"])
            self.assertTrue(cp.submit_issues(st, {**info, "prompt": bad_prompt}), new_s)
            self.assertTrue(hp.heli_issues(st, {**info, "prompt": bad_prompt}), new_s)
        self.assertTrue(hp.heli_camera_issues(sc["prompt"].replace(" 9-15s: The Skycrane",
                                                                   " 9-15s: Right below the terrace, the Skycrane", 1),
                                              st["heli_yaklasma"]["geo"]))
        self.assertTrue(cp.submit_issues(st, {**info, "prompt": sc["prompt"].replace("from its belly.",
                                                                                     "from the helicopter's belly.", 1)}))
        # 14 Kas (2): kova/halat ve "toward the camera" hiçbir yerde olamaz (açılış ve stil eki dahil)
        p0 = sc["prompt"]
        for old_s, new_s in (("belly tank", "bucket"), ("the long hose", "the long steel cable"),
                             ("No readable signs", "The water falls from the Bucket. No readable signs"),
                             ("engulfed in flames,", "engulfed in flames racing toward the camera,"),
                             ("never flying over the camera", "flying toward the camera"),
                             # 14 Kas (3) v4: dökme gibi çizilen fiiller ve genel helikopter yasak
                             ("rises off the water,", "rises off the water, sucking water into its belly tank,"),
                             ("rises off the water,", "rises off the water, water streaming from its hose,"),
                             ("S-64 Skycrane", "heavy firefighting helicopter"),
                             # 14 Kas (4) v5: teras, püskürtme, dökme yasak; zorunlu ifadeler
                             ("top-floor balcony", "top-floor terrace"),
                             ("rises off the water,", "rises off the water, spraying water,"),
                             ("rises off the water,", "rises off the water, pouring water,"),
                             ("high vantage", "low vantage"),
                             # 14 Kas (5) v6: "sunk" ve "a SUV" yasak; damlayan hortum zorunlu
                             (DRIP, "water sprinkling from the long hose"),
                             ("rises off the water,", "rises off the water, its hose sunk in the lake,"),
                             ("No readable signs", "Then a SUV burns. No readable signs"),
                             ("never flying over the camera", "flying over the camera"),
                             ("never on the camera", "even on the camera")):
            bad_prompt = p0.replace(old_s, new_s, 1)
            self.assertNotEqual(bad_prompt, p0, old_s)
            self.assertTrue(hp.heli_camera_issues(bad_prompt, st["heli_yaklasma"]["geo"]), new_s)
            self.assertTrue(hp.heli_issues(st, {**info, "prompt": bad_prompt}), new_s)
            self.assertTrue(cp.submit_issues(st, {**info, "prompt": bad_prompt}), new_s)
        no_tank = p0.replace("belly tank", "tank")   # "belly tank" hiç kalmazsa gönderilmez
        self.assertIn('"belly tank" eksik', hp.heli_camera_issues(no_tank, st["heli_yaklasma"]["geo"]))
        for old_s, new_s in ():
            bad_prompt = p0.replace(old_s, new_s, 1)
            self.assertNotEqual(bad_prompt, p0, old_s)
            self.assertTrue(hp.heli_camera_issues(bad_prompt, st["heli_yaklasma"]["geo"]), new_s)
            self.assertTrue(hp.heli_issues(st, {**info, "prompt": bad_prompt}), new_s)
            self.assertTrue(cp.submit_issues(st, {**info, "prompt": bad_prompt}), new_s)
        for bad in ({"geo": "R1"}, {"geo": "L7"}, {"mid": "M1"}, {"final": "N1"}, {"people": 6}, {"mid": "H4"},
                    {"final": "J4"}, {"mid": "H2", "vehicle": None}):
            self.assertTrue(cp.submit_issues({**st, "heli_yaklasma": {**st["heli_yaklasma"], **bad}}, info), bad)
        story = asyncio.run(cp.rewrite_structured(st, "test", AsyncMock(side_effect=AssertionError("GPT"))))
        self.assertEqual(story, sc["story"])

    def _approval(self, d):
        sc, st = d["scenes"][0], d["structure"]
        hb = st["heli_yaklasma"]
        lines = hb["lines"].split("\n")
        self.assertEqual(lines[0], "Mod: ⭐ Hit kalıbı · Yaklaşma (helikopter)")
        self.assertEqual(lines[1], f"Coğrafya: {hb['geo']} {PLACES[hb['geo']][0]}")
        self.assertEqual(lines[2], f"Araç: {hb['vehicle']}")   # 14 Kas (3): üç orta da araçlı
        self.assertEqual(lines[3], f"Orta (4-9s): {hb['mid']} «{hp.heli_mid(hb['mid'], hb['vehicle'])}»")
        self.assertEqual(lines[4], f"Final (9-15s): {hb['final']} «{FINALS[hb['final']]}»")
        self.assertEqual(lines[5], "Kamera: sabit")
        self.assertEqual(lines[6], f"Kelime: {len(sc['prompt'].split())} (en fazla 230) · karakter: "
                                   f"{len(sc['prompt'])} (en fazla 1400)")
        self.assertEqual(len(lines), 7)
        # Onay görüntüsü: 1. Seçim / 3. Hikâye / Eksenler gerçek parçalar
        shown = sections_to_text(format_generation(d["trace"])) + "\n" + st["axes_line"]
        sel, _, rest = shown.partition("🔍 2.")
        story = rest.split("🔍 3. Hikâye\n", 1)[1]
        for part in (hp.heli_opening(hb["geo"]), hp.heli_mid(hb["mid"], hb["vehicle"]), FINALS[hb["final"]]):
            self.assertIn(part, sc["prompt"])
            self.assertIn(part, sel)
            self.assertIn(part, story)
        self.assertIn(FIXED, sel)
        self.assertNotIn(FOLLOW, shown)
        self.assertIn("Mod: ⭐ Hit kalıbı · Yaklaşma (helikopter)", sel)
        self.assertIn("kamera modu=sabit", st["axes_line"])
        self.assertIn(f"orta={hb['mid']}", st["axes_line"])
        self.assertIn(f"final={hb['final']}", st["axes_line"])
        self.assertIn(f"coğrafya={hb['geo']} {PLACES[hb['geo']][0]}", st["axes_line"])
        self.assertIn(f"araç={hb['vehicle']}", st["axes_line"])
        for absent in (st["spec"]["key_visual"], "kamera modu=A", "kamera modu=B"):
            self.assertNotIn(absent, shown)
        _, body = format_final_prompt({"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"],
                                       "hit_lines": hb["lines"], "environment": st["environment"]})
        self.assertIn("\nMod: ⭐ Hit kalıbı · Yaklaşma (helikopter)\n", body)
        self.assertIn("\n\n" + sc["prompt"], body)
        return hb["mid"]

    def test_approval_lines_and_display(self):
        seen = set()
        for seed in range(1, 30):
            seen.add(self._approval(build(seed)))
            if seen == {"H1", "H2", "H3"}:
                break
        self.assertEqual(seen, {"H1", "H2", "H3"})

    def test_normal_helicopter_untouched(self):
        for seed in range(1, 6):
            reset()
            random.seed(seed)
            d = asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": HE, "used_combos": [],
                                                         "recent_topics": []}))
            self.assertNotIn("heli_yaklasma", d["structure"])
            self.assertNotIn("mode_label", d["trace"])
            p = d["scenes"][0]["prompt"]
            for x in ("S-64 Skycrane", DRIP, WATER_LINE, "high vantage looking steeply down",
                      "never flying over the camera", "people run below.", FOLLOW):
                self.assertNotIn(x, p)


class TestHeliPipelineAndBot(_Quiet):
    def test_pipeline_passes_flag_and_sends_prompt(self):
        import main
        from test_tur29_infra import TestPipelineTur29, _Reporter
        seen = {}

        async def fake_gen(config):
            seen["config"] = dict(config)
            reset()
            random.seed(21)
            cfg = {k: v for k, v in config.items() if k not in ("axes_loader", "caption_loader")}
            return await pg.generate_creative_prompts({**cfg, "domain": DOMAIN})
        t = TestPipelineTur29("test_test_mode_never_uploads_and_archives_full_meta")
        t.setUp()
        try:
            rep = _Reporter(approve=True, needs_approval=True)
            orig = main.run_pipeline

            async def run_with(**kw):
                return await orig(**kw, heli_yaklasma=True)
            with patch.object(main, "run_pipeline", run_with):
                r = t.run_pipe(gen=AsyncMock(side_effect=fake_gen), reporter=rep, event=HE)
        finally:
            t.doCleanups()
        self.assertTrue(r["success"], r)
        self.assertIs(seen["config"]["heli_yaklasma"], True)
        approve = [c[1] for c in rep.calls if c[0] == "approve"]
        self.assertEqual(len(approve), 1)
        info = approve[0]
        self.assertTrue(info["hit_lines"].startswith("Mod: ⭐ Hit kalıbı · Yaklaşma (helikopter)\nCoğrafya: L"))
        self.assertEqual(t.create.await_args.args[1], info["prompt"])   # Kie'ye giden = onaydaki

    def test_bot_button_and_flow(self):
        import bot
        from test_tur29_infra import _context, _update
        di = str(bot.DOMAIN_KEYS.index(DOMAIN))
        ei = str(bot.domain_events(DOMAIN).index(HE))
        ctx = _context()
        upd = _update(data=f"uret:e:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, ctx))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        labels = [b.text for r in kb.inline_keyboard for b in r]
        self.assertEqual(labels, ["✅ Üret", "❌ İptal", "⭐ Hit kalıbı · Yaklaşma"])
        self.assertEqual([len(r) for r in kb.inline_keyboard], [2, 1])   # buton Üret/İptal'in altında
        upd = _update(data=f"uret:hy:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, ctx))
        text = upd.callback_query.edit_message_text.await_args.args[0]
        self.assertIn("Mod: ⭐ Hit kalıbı · Yaklaşma (helikopter)", text)
        self.assertIn("Kamera: sabit", text)
        upd = _update(data=f"uret:hyok:{di}:{ei}")
        runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
        with patch.object(bot.pipeline, "run_pipeline", runner), patch.object(bot, "_production_lock", asyncio.Lock()):
            asyncio.run(bot.on_callback(upd, ctx))
        kw = runner.await_args.kwargs
        self.assertEqual((kw["event"], kw["heli_yaklasma"]), (HE, True))
        for other in ("kul_yaklasma", "orman_yaklasma", "dalga24", "approach_env", "hit_env"):
            self.assertNotIn(other, kw)
        self.assertTrue(kw["reporter"].needs_approval)
        # diğer olaylarda bu buton yok
        for i, e in enumerate(bot.domain_events(DOMAIN)):
            if e == HE:
                continue
            upd = _update(data=f"uret:e:{di}:{i}")
            asyncio.run(bot.on_callback(upd, ctx))
            kw = upd.callback_query.edit_message_text.await_args.kwargs
            if "reply_markup" in kw:
                cbs = [b.callback_data for r in kw["reply_markup"].inline_keyboard for b in r]
                self.assertFalse(any(c.startswith("uret:hy") for c in cbs), e)
        self.assertIsNone(bot.parse_heli(di, str(next(i for i, e in enumerate(bot.domain_events(DOMAIN))
                                                      if e != HE))))


if __name__ == "__main__":
    unittest.main()
