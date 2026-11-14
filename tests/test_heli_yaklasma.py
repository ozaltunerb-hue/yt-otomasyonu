# 13 Kas 2026, Bahadır: helikopter "⭐ Hit kalıbı · Yaklaşma" modu (core/hit_prompts.py YAKLASMA_HELIKOPTER).
# Göl kenarındaki kasabada yangın; helikopter çelik halatın ucundaki büyük kovayı gölden doldurup yangının üstüne boşaltır.
# GPT yok, zaman etiketleri var. Suyun öznesi her zaman kova ("helicopter's" yok). Helikopterin normal yolu ve diğer
# bütün olay/modlar değişmez. Ağ yok.
# 14 Kas 2026: su yangına kovadan; helikopter kameraya gelmez, kamera her zaman sabit, finallerde "terrace"/"toward the camera" yok.
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
PLACES = {"L1": ("Kanada", "a Canadian lakeside town of timber houses"),
          "L2": ("Kaliforniya", "a lakeside mountain town of wooden cabins"),
          "L3": ("İtalya", "an Italian lakeside town of terracotta-roofed stone houses"),
          "L4": ("İsviçre", "a Swiss lakeside village of wooden chalets"),
          "L5": ("Yunanistan", "a Greek lakeside village of whitewashed houses"),
          "L6": ("Avustralya", "an Australian lakeside town of weatherboard houses")}
MIDS = {
    "H1": "The helicopter lifts off the lake, the full bucket swinging far below on its cable, and flies low over the "
          "rooftops toward the flames.",
    "H2": "Just ahead of the flames, a burning pine crashes onto a fleeing {vehicle}, crushing its hood, as the "
          "helicopter passes overhead with the full bucket swinging far below it.",
    "H3": "Just ahead of the flames, the wall of fire swallows a parked {vehicle} as the helicopter passes overhead with "
          "the full bucket swinging far below it.",
}
FINALS = {
    "J1": "The helicopter hovers over the burning houses down the street and the hanging bucket opens, a massive "
          "curtain of water falling from it onto the flames and bursting into white steam.",
    "J2": "The helicopter stops over the burning roof of a house down the street and the bucket far below it dumps its "
          "water straight onto the flames, the roof hissing into steam as it caves in.",
    "J3": "The helicopter sweeps along the wall of flames at the lakeshore and the bucket empties onto it, a long sheet "
          "of water crashing onto the fire and bursting into steam.",
}
OPENING = ("The burning forest has already reached {place}, a towering wall of flames racing down the street toward the "
           "camera, as a firefighting helicopter skims the lake below the terrace, filling the big orange bucket "
           "hanging on a long steel cable far below it.")
TAIL = ("Handheld footage shot from a high terrace of a lakeside house overlooking the lake and the street, the "
        "helicopter clearly visible in the middle distance, crossing the frame sideways, never flying toward or over "
        "the camera, a corner of the terrace railing in the foreground; slight hand shake, the camera stays fixed; one "
        "continuous shot, no zoom, no cuts. Water falls only out of the bottom of the hanging bucket, never from the "
        "body of the helicopter. Never CGI. Realistic wildfire: towering, roaring flames and thick smoke, never thin "
        "lines of fire. Real time, never slow motion. No readable signs, text or flags.")
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
        self.assertEqual(hp.heli_people(3), "Three people run along the lakeshore below.")
        self.assertEqual(hp.heli_people(4), "Four people run along the lakeshore below.")
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
        self.assertEqual((hp.HELI_GEO_BLOCK, hp.HELI_VEHICLE_BLOCK, hp.HELI_MID_BLOCK, hp.HELI_FINAL_BLOCK),
                         (3, 2, 1, 1))
        self.assertEqual((hp.HELI_MAX_WORDS, hp.HELI_MAX_CHARS), (230, 1400))

    def test_vehicle_fill(self):
        for v in HL["vehicles"]:
            self.assertEqual(hp.heli_mid("H2", v), MIDS["H2"].format(vehicle=v))
            self.assertEqual(hp.heli_mid("H3", v), MIDS["H3"].format(vehicle=v))
            self.assertIn(f"a fleeing {v}, crushing its hood", hp.heli_mid("H2", v))
            self.assertIn(f"a parked {v} as the helicopter", hp.heli_mid("H3", v))
            self.assertEqual(hp.heli_mid("H1", v), MIDS["H1"])   # H1'de araç yok
        for m in ("H2", "H3"):
            with self.assertRaises(es.StructureError):
                hp.heli_mid(m, None)
        h1 = hp.heli_mid("H1", None)
        for w in VEHICLE_WORDS:
            self.assertNotIn(w, h1)
        self.assertEqual(HL["vehicle_mids"], ("H2", "H3"))
        for bad in ("M1", "H4", "F1"):
            with self.assertRaises(es.StructureError):
                hp.heli_mid(bad, "SUV")
        with self.assertRaises(es.StructureError):
            hp.heli_final("J4")

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
            for bad in ("Turkish", "Turkey", "helicopter's", "Full action", "Until the last frame"):
                self.assertNotIn(bad, p)
            self.assertIn("never from the body of the helicopter", p)
            self.assertIn("never thin lines of fire", p)
            for need in ("never flying toward or over the camera", "Water falls only out of the bottom of the hanging "
                         "bucket", "the camera stays fixed"):
                self.assertIn(need, p)
            self.assertNotIn("turns slightly to follow", p)
            self.assertEqual(hp.heli_camera_issues(p, g), [], key)
            self.assertIn("a corner of the terrace railing in the foreground", p)
            self.assertTrue(p.startswith("0-4s: "))
            for lab in (" 4-9s: ", " 9-15s: "):
                self.assertIn(lab, p)
            opening, rest = p.split(" 4-9s: ")
            self.assertIn("toward the camera", opening)
            self.assertIn("bucket hanging on a long steel cable far below it", opening)
            mid_part, final_part = rest.split(" 9-15s: ")
            final_part = final_part.split(" Handheld footage")[0]
            self.assertEqual(final_part, FINALS[f])
            for bad in ("terrace", "toward the camera", "over the camera"):
                self.assertNotIn(bad, final_part, key)
                self.assertNotIn(bad, mid_part, key)
            if m == "H1":
                for word in VEHICLE_WORDS:
                    self.assertNotIn(word, mid_part, key)
            else:
                self.assertIn(f" {v}", mid_part, key)
                self.assertEqual(sum(f" {x}" in mid_part for x in HL["vehicles"]), 1, key)
            self.assertIn(f"slight hand shake, {FIXED}; one continuous shot", p)   # takip parametresi etkisiz
            pos = [p.find(x) for x in ("0-4s: ", " people run along the lakeshore below.", " 4-9s: ", " 9-15s: ",
                                       " Handheld footage")]
            self.assertNotIn(-1, pos)
            self.assertEqual(pos, sorted(pos))
        self.assertEqual(n, 6 * 2 * 3 * 3 * 3 * 2)
        self.assertEqual(over, [], f"en uzun: {longest}")

    def test_water_subject_is_always_the_bucket(self):
        """Eski üretimde "the helicopter's water" suyu gövdeden döktü: suyun öznesi her zaman kova."""
        for f, text in FINALS.items():
            self.assertIn("bucket", text, f)
            for bad in ("terrace", "toward the camera", "camera"):
                self.assertNotIn(bad, text, f)
        self.assertIn("never from the body of the helicopter", TAIL)
        for text in list(MIDS.values()) + list(FINALS.values()) + [OPENING, TAIL]:
            self.assertNotIn("helicopter's", text)
            self.assertNotIn("helicopter drops", text)
            self.assertNotIn("helicopter releases", text)

    def test_sentences_only_in_this_mode(self):
        marks = [OPENING.split("{place}")[1], "The burning forest has already reached",
                 "Three people run along the lakeshore below.", "Four people run along the lakeshore below.",
                 MIDS["H1"], MIDS["H2"].split("{vehicle}")[1], MIDS["H3"].split("{vehicle}")[1],
                 "a burning pine crashes onto a fleeing", "the wall of fire swallows a parked",
                 *FINALS.values(), "never from the body of the helicopter",
                 "bucket hanging on a long steel cable far below it", "Water falls only out of the bottom of the hanging",
                 "Handheld footage shot from a high terrace of a lakeside house", *[p for _, p in PLACES.values()]]
        # not: "a corner of the terrace railing in the foreground" başka bir modun stil ekinde de var (ortak ifade)
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
        for bad in ("Full action", "Until the last frame", "helicopter's", "Turkish", "Turkey", sk.FULL_MOTION):
            self.assertNotIn(bad, prompt)
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
        self.assertEqual(finals, {"J1", "J2", "J3"})
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
            self.assertIn(hp.heli_choose_final(hist, random.Random(s)), ("J1", "J3"))   # son 1: J2 elenir
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
        for old_s, new_s in ((" 9-15s: The helicopter", " 9-15s: Right below the terrace, the helicopter"),
                             (" 9-15s: The helicopter", " 9-15s: Moving toward the camera, the helicopter"),
                             (" 9-15s: The helicopter", " 9-15s: Flying over the camera, the helicopter"),
                             ("No readable signs", "The camera turns slightly to follow the helicopter. No readable signs")):
            bad_prompt = sc["prompt"].replace(old_s, new_s, 1)
            self.assertNotEqual(bad_prompt, sc["prompt"])
            self.assertTrue(cp.submit_issues(st, {**info, "prompt": bad_prompt}), new_s)
            self.assertTrue(hp.heli_issues(st, {**info, "prompt": bad_prompt}), new_s)
        self.assertTrue(hp.heli_camera_issues(sc["prompt"].replace(" 9-15s: The helicopter",
                                                                   " 9-15s: Right below the terrace, the helicopter", 1),
                                              st["heli_yaklasma"]["geo"]))
        self.assertTrue(cp.submit_issues(st, {**info, "prompt": sc["prompt"].replace("the big orange bucket",
                                                                                     "the helicopter's bucket", 1)}))
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
        self.assertEqual(lines[2], f"Araç: {hb['vehicle']}" + (" (bu ortada araç yok)" if hb["mid"] == "H1" else ""))
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
        self.assertIn("araç=yok" if hb["mid"] == "H1" else f"araç={hb['vehicle']}", st["axes_line"])
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
            for x in ("bucket hanging on a long steel cable far below it", "never from the body of the helicopter",
                      "never flying toward or over the camera", "run along the lakeshore below", FOLLOW):
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
