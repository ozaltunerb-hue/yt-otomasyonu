# 13 Kas 2026, Bahadır: orman yangını "⭐ Hit kalıbı · Yaklaşma" modu (core/hit_prompts.py YAKLASMA_ORMAN).
# Orman yangını hit'i (9 Eki 21:52, K5+L4) + kül bulutu Yaklaşma yapısı. GPT yok, zaman etiketleri var. Orman yangınının
# normal yolu, kayıtlı orman hit prompt'u ve diğer bütün olay/modlar değişmez. Ağ yok.
import asyncio
import hashlib
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

WF = es.WILDFIRE
OR = hp.YAKLASMA_ORMAN
DOMAIN = "fire_disasters"
FOLLOW = "the camera pans to follow the wall of flames as it approaches"
FIXED = "the camera stays fixed"
ACTION = "Burning embers and thick smoke blow across the street from the very first frame."
BANNED = {("M2", "N3"), ("M2", "N2"), ("M3", "N2")}
VEHICLE_WORDS = ("van", "truck", "SUV", "car", "vehicle", "{")


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
    for m in (hp._ORMAN_GEO_MEMORY, hp._ORMAN_VEHICLE_MEMORY, hp._KUL_GEO_MEMORY, hp._KUL_VEHICLE_MEMORY,
              hp._DZ_GEO_MEMORY, hp._GEO_MEMORY):
        m.clear()


def gen(**extra) -> dict:
    return asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": WF, "orman_yaklasma": True,
                                                     "used_combos": [], "recent_topics": [], **extra}))


def build(seed: int) -> dict:
    reset()
    random.seed(seed)
    return gen()


def all_combos():
    for g in OR["geos"]:
        for ppl in (3, 4):
            for v in OR["vehicles"]:
                for m in OR["mids"]:
                    for f in OR["finals"]:
                        if (m, f) in BANNED:
                            continue
                        for follow in (True, False):
                            yield (g, ppl, v, m, f, follow), hp.orman_prompt(g, ppl, m, v, f, follow)


class TestTexts(_Quiet):
    def test_verbatim_texts(self):
        self.assertEqual(hp.ORMAN_MODE_LABEL, "⭐ Hit kalıbı · Yaklaşma (orman yangını)")
        self.assertIs(hp.ORMAN_YAKLASMA_KAMERA_TAKIP, True)
        self.assertEqual(sorted(OR["geos"]), ["R1", "R2", "R3", "R4", "R5", "R6"])
        geos = {"R1": ("pine-covered", "a hillside neighborhood of wooden suburban houses"),
                "R2": ("eucalyptus-covered", "a hillside neighborhood of tin-roofed weatherboard houses"),
                "R3": ("pine-covered", "a hillside village of whitewashed terracotta-roofed houses"),
                "R4": ("spruce-covered", "a hillside town of dark-roofed timber houses"),
                "R5": ("eucalyptus-covered", "a hillside village of tile-roofed stone houses"),
                "R6": ("pine-covered", "a hillside town of colorful wooden houses")}
        for g, (forest, place) in geos.items():
            self.assertEqual((OR["geos"][g]["forest"], OR["geos"][g]["place"]), (forest, place))
            self.assertEqual(hp.orman_opening(g),
                             f"A towering wall of flames has already swept down the {forest} slope and is racing "
                             f"halfway down the street through {place} toward the camera, igniting roofs and trees as "
                             "it comes.")
        self.assertEqual([OR["geos"][g]["name"] for g in sorted(OR["geos"])],
                         ["Kaliforniya", "Avustralya", "Yunanistan", "Kanada", "Portekiz", "Şili"])
        self.assertEqual(hp.orman_people(3), "Three people run up the street below, away from the flames.")
        self.assertEqual(hp.orman_people(4), "Four people run up the street below, away from the flames.")
        self.assertEqual(OR["action"], ACTION)
        self.assertEqual(OR["vehicles"], ("white van", "pickup truck", "SUV"))
        self.assertEqual(sorted(OR["mids"]), ["M1", "M2", "M3"])
        self.assertEqual(sorted(OR["finals"]), ["N1", "N2", "N3"])
        self.assertEqual(OR["finals"]["N1"], "Right below the balcony, the flames reach the nearest house and its roof "
                                             "caves in, a fountain of sparks bursting up toward the camera.")
        self.assertEqual(OR["finals"]["N2"], "Right below the balcony, the wall of flames engulfs the garden and wooden "
                                             "deck of the nearest house, burning planks collapsing in a shower of "
                                             "sparks.")
        self.assertEqual(OR["finals"]["N3"], "Right below the balcony, a burning tree topples onto the nearest house, "
                                             "smashing through its roof as flames pour inside.")
        self.assertEqual(hp.ORMAN_PASIF["finals"]["N4"], "Right below the balcony, the fire jumps the street and the "
                                                         "wooden fence and carport below burst into flames, heat and "
                                                         "sparks rushing up toward the camera.")
        self.assertEqual(hp.orman_camera_text(True), FOLLOW)
        self.assertEqual(hp.orman_camera_text(False), FIXED)
        self.assertEqual(hp.orman_tail(True),
                         "Handheld footage shot from the balcony of a hillside house overlooking the street and the "
                         "burning slope, high vantage, normal lens, a corner of the balcony railing in the foreground; "
                         f"slight hand shake, {FOLLOW}; one continuous shot, no zoom, no cuts, no face close to the "
                         "camera. Civilians in everyday clothes, never CGI. Realistic wildfire: towering, roaring "
                         "flames and thick smoke, never thin lines or strips of fire. Raw natural light under an orange "
                         "smoky sky. Real time, never slow motion, people run at full speed. No readable signs, text or "
                         "flags.")
        self.assertEqual((hp.ORMAN_GEO_BLOCK, hp.ORMAN_VEHICLE_BLOCK, hp.ORMAN_MID_BLOCK, hp.ORMAN_FINAL_BLOCK),
                         (3, 2, 1, 1))
        self.assertEqual(set(hp.ORMAN_BANNED_PAIRS), BANNED)

    def test_passive_m4_n4(self):
        """13 Kas (2): M4 ve N4 pasif (ORMAN_PASIF'te, silinmedi); hiç seçilmez; her ortanın en az bir final adayı var."""
        self.assertEqual(sorted(hp.ORMAN_PASIF["mids"]), ["M4"])
        self.assertEqual(sorted(hp.ORMAN_PASIF["finals"]), ["N4"])
        self.assertEqual(hp.ORMAN_PASIF["mids"]["M4"], "Halfway down the street, two houses on either side of the road "
                                                       "catch fire at once, flames pouring out of their windows and "
                                                       "roofs.")
        self.assertEqual(hp.ORMAN_OPENING_V1, "A towering wall of flames sweeps down the {forest} slope at the far end "
                                              "of the street and slams into the edge of {place}, igniting roofs and "
                                              "trees as it races toward the camera.")
        self.assertEqual(hp.ORMAN_OPENING_V2, "A towering wall of flames has already swept down the {forest} slope at "
                                              "the far end of the street and is racing through the edge of {place} "
                                              "toward the camera, igniting roofs and trees as it comes.")
        self.assertEqual(hp.ORMAN_MIDS_V2, {
            "M1": "Halfway down the street, the {vehicle} speeds away as the wall of flames closes the road right "
                  "behind it.",
            "M2": "Halfway down the street, a huge burning pine crashes down onto the {vehicle}, crushing its roof.",
            "M3": "Halfway down the street, the wall of flames swallows a parked {vehicle}, its windows bursting as it "
                  "disappears into the fire."})
        self.assertEqual(set(hp.ORMAN_BANNED_PAIRS), {("M2", "N3"), ("M2", "N2"), ("M3", "N2")})
        for m in ("M1", "M2", "M3"):
            allowed = {f for f in OR["finals"] if (m, f) not in BANNED}
            self.assertTrue(allowed, m)
            for hist_f in OR["finals"]:   # son final hangisi olursa olsun aday kalır
                h = [f"{DOMAIN}|none|{WF.lower()}|x##M1+{hist_f}|y"]
                for s in range(20):
                    self.assertIn(hp.orman_choose_final(h, m, random.Random(s)), allowed)
        for s in range(200):
            r = random.Random(s)
            self.assertNotEqual(hp.orman_choose_mid([], r), "M4")
            for m in ("M1", "M2", "M3"):
                self.assertNotEqual(hp.orman_choose_final([], m, r), "N4")
        for m, f in (("M4", "N1"), ("M1", "N4")):
            with self.assertRaises((es.StructureError, KeyError)):
                hp.orman_story("R2", 3, m, "SUV", f)

    def test_vehicle_fill(self):
        for v in OR["vehicles"]:
            self.assertEqual(hp.orman_mid("M1", v), f"Just ahead of the flames, the {v} speeds away as the wall of "
                                                    "flames closes the road right behind it.")
            self.assertEqual(hp.orman_mid("M2", v), f"Just ahead of the flames, a huge burning pine crashes down onto "
                                                    f"the {v}, crushing its roof.")
            self.assertEqual(hp.orman_mid("M3", v), f"Just ahead of the flames, the wall of flames swallows a parked "
                                                    f"{v}, its windows bursting as it disappears into the fire.")
            with self.assertRaises(es.StructureError):
                hp.orman_mid("M4", v)   # 13 Kas (2): pasif
        for m in ("M1", "M2", "M3"):
            with self.assertRaises(es.StructureError):
                hp.orman_mid(m, None)
        self.assertEqual(OR["vehicle_mids"], ("M1", "M2", "M3"))

    def test_banned_pairs_rejected(self):
        for m, f in BANNED:
            with self.assertRaises(es.StructureError):
                hp.orman_story("R2", 3, m, "SUV", f)
            for s in range(40):
                self.assertNotEqual(hp.orman_choose_final([], m, random.Random(s)), f)

    def test_street_opening_and_mid_prefix(self):
        """13 Kas (3): yangın ilk karede caddenin ortasında; ortalar "Just ahead of the flames," ile başlar."""
        for g in OR["geos"]:
            self.assertIn("racing halfway down the street", hp.orman_opening(g))
            self.assertNotIn("at the far end of the street", hp.orman_opening(g))
        for m in OR["mids"]:
            self.assertTrue(OR["mids"][m].startswith("Just ahead of the flames, "), m)
            self.assertNotIn("Halfway down the street", OR["mids"][m])
            self.assertEqual(OR["mids"][m][len("Just ahead of the flames, "):],
                             hp.ORMAN_MIDS_V2[m][len("Halfway down the street, "):])
        for key, p in all_combos():
            opening = p.split(" 4-9s: ")[0]
            self.assertIn("racing halfway down the street", opening)
            self.assertTrue(p.split(" 4-9s: ")[1].startswith("Just ahead of the flames, "), key)

    def test_every_mid_keeps_a_final(self):
        """Yeni yasak çiftler (M2+N2, M3+N2) + mevcut M2+N3: her ortanın en az bir final adayı var; son final ne olursa
        olsun seçilen orta için LRU'yu bozmayan final kalır; yasak çift hiç çıkmaz."""
        self.assertEqual({m: sorted(f for f in OR["finals"] if (m, f) not in BANNED) for m in OR["mids"]},
                         {"M1": ["N1", "N2", "N3"], "M2": ["N1"], "M3": ["N1", "N3"]})
        reset()   # bellekteki önceki üretimler geçmişe karışmasın
        for pm in OR["mids"]:
            for pf in OR["finals"]:
                if (pm, pf) in BANNED:
                    continue
                h = [f"{DOMAIN}|none|{WF.lower()}|x##{pm}+{pf}|y"]
                for s in range(40):
                    m = hp.orman_choose_mid(h, random.Random(s))
                    self.assertNotEqual(m, pm)
                    f = hp.orman_choose_final(h, m, random.Random(s))
                    self.assertNotIn((m, f), BANNED)
                    self.assertNotEqual(f, pf, (pm, pf, m))

    def test_all_combos_within_limits(self):
        """Coğrafya × kişi × araç × orta × final (yasak çiftler hariç) × kamera: hepsi ≤ 230 kelime, ≤ 1400 karakter."""
        n, over, longest = 0, [], (0, 0, None)
        for key, p in all_combos():
            n += 1
            w, c = len(p.split()), len(p)
            longest = max(longest, (w, c, key))
            if w > hp.ORMAN_MAX_WORDS or c > hp.ORMAN_MAX_CHARS:
                over.append((key, w, c))
            self.assertNotIn("U-turn", p)
            self.assertNotIn("Full action", p)
            self.assertNotIn("Until the last frame", p)
            for lab in ("0-4s: ", " 4-9s: ", " 9-15s: "):
                self.assertIn(lab, p)
            self.assertIn("never thin lines or strips of fire", p)
            self.assertIn("a corner of the balcony railing in the foreground", p)
            opening, rest = p.split(" 4-9s: ")
            self.assertIn("has already swept down", opening)
            self.assertIn("toward the camera", opening)
            self.assertTrue(any(f" {v}" in rest.split(" 9-15s: ")[0] for v in OR["vehicles"]), key)
            self.assertNotIn(hp.ORMAN_PASIF["mids"]["M4"], p)
            self.assertNotIn(hp.ORMAN_PASIF["finals"]["N4"], p)
        self.assertEqual(n, 6 * 2 * 3 * 6 * 2)
        self.assertEqual(over, [], f"en uzun: {longest}")
        self.assertEqual((hp.ORMAN_MAX_WORDS, hp.ORMAN_MAX_CHARS), (230, 1400))

    def test_sentences_only_in_this_mode(self):
        marks = ["has already swept down the", "is racing halfway down the street through", "Just ahead of the flames,",
                 ACTION,
                 "Three people run up the street below, away from the flames.",
                 "Four people run up the street below, away from the flames.",
                 "closes the road right behind it", "a huge burning pine crashes down onto the",
                 "its windows bursting as it disappears into the fire",
                 "two houses on either side of the road catch fire at once",
                 "a fountain of sparks bursting up toward the camera", "burning planks collapsing in a shower of sparks",
                 "a burning tree topples onto the nearest house", "the fire jumps the street and the wooden fence",
                 FOLLOW, "never thin lines or strips of fire", "a corner of the balcony railing in the foreground",
                 "Realistic wildfire: towering, roaring flames and thick smoke"]
        # not: "under an orange smoky sky" normal yangın havasında da var (ortak ifade, bu moda özgü cümle değil)
        pools = json.dumps({e: {s: {k: v["text"] for k, v in b[s].items()} for s in ("slice_2", "slice_3")}
                            for e, b in es.EVENT_BEATS.items()}, ensure_ascii=False)
        others = (pools + json.dumps(hp.HIT_PROMPTS, ensure_ascii=False)
                  + json.dumps(hp.YAKLASMA_ATES_HORTUMU, default=str, ensure_ascii=False)
                  + json.dumps(hp.DALGA_24EYLUL, default=str, ensure_ascii=False)
                  + json.dumps(hp.YAKLASMA_KUL_BULUTU, default=str, ensure_ascii=False))
        for ev in ps.active_events():
            for seed in range(1, 6):
                others += json.dumps(ps.snapshot_event(ev, seed), ensure_ascii=False)
        for m in marks:
            self.assertNotIn(m, others, m)

    def test_recorded_hit_prompt_unchanged(self):
        h = hp.HIT_PROMPTS[WF]
        self.assertEqual(h["source"], "9 Eki 2026 21:52")
        self.assertIn("##K5+L4|", h["combo_key"])
        # 8d9c264'te kaydedilen metnin sha256'sı (birebir aynı kalmalı)
        self.assertEqual(hashlib.sha256(h["prompt"].encode()).hexdigest(),
                         "d6d580d516546710e4026001436750be3f605dcf4c193d9dd4be4eac0aae1ee5")
        self.assertNotIn(WF, hp.HIT_ACTIVE_EVENTS)   # eski orman hit butonu gizli kalır


class TestOrmanMode(_Quiet):
    def _check(self, d):
        sc, st = d["scenes"][0], d["structure"]
        ob = st["orman_yaklasma"]
        prompt = sc["prompt"]
        g = OR["geos"][ob["geo"]]
        self.assertIn(f"the {g['forest']} slope", prompt)
        self.assertIn(g["place"], prompt)
        opening = prompt.split(" 4-9s: ")[0]
        self.assertTrue(prompt.startswith(f"0-4s: {hp.orman_opening(ob['geo'])} "))
        self.assertIn("has already swept down", opening)
        self.assertIn("toward the camera", opening)
        self.assertIn(f" {hp.orman_people(ob['people'])} {ACTION} 4-9s: ", prompt)
        self.assertIn(ob["vehicle"], OR["vehicles"])
        self.assertIn(ob["mid"], OR["mids"])
        self.assertIn(ob["final"], OR["finals"])
        self.assertNotIn((ob["mid"], ob["final"]), BANNED)
        mid_text = hp.orman_mid(ob["mid"], ob["vehicle"])
        self.assertIn(f"4-9s: {mid_text} 9-15s: {OR['finals'][ob['final']]} ", prompt)
        self.assertIn(ob["mid"], ("M1", "M2", "M3"))
        self.assertIn(f" {ob['vehicle']}", mid_text)   # her prompt'ta araçlı orta
        for lab in ("0-4s: ", " 4-9s: ", " 9-15s: "):
            self.assertIn(lab, prompt)
        for bad in ("Full action", "Until the last frame", "U-turn"):
            self.assertNotIn(bad, prompt)
        self.assertIn("never thin lines or strips of fire", prompt)
        self.assertIn("a corner of the balcony railing in the foreground", prompt)
        self.assertTrue(prompt.endswith(" " + hp.orman_tail(ob["follow"])))
        self.assertEqual(sc["style_suffix"], hp.orman_tail(ob["follow"]))
        pos = [prompt.find(x) for x in ("0-4s: ", ACTION, " 4-9s: ", " 9-15s: ", " Handheld footage")]
        self.assertNotIn(-1, pos)
        self.assertEqual(pos, sorted(pos))
        self.assertLessEqual(len(prompt.split()), 230)
        self.assertLessEqual(len(prompt), 1400)
        self.assertIn(f"#{ob['mid']}+{ob['final']}|", d["combo_key"])
        for slot in ("slice_2", "slice_3"):   # normal orman havuzu (K*/L*) metni yok
            for bid in es.EVENT_BEATS[WF][slot]:
                self.assertNotIn(es.beat_text(WF, slot, bid)[4:], prompt)
        self.assertNotIn(es.EVENT_KEY_VISUAL[WF], prompt)
        self.assertEqual(cp.submit_issues(st, {"prompt": prompt, "story": sc["story"],
                                               "style_suffix": sc["style_suffix"]}), [])
        return ob

    def test_50_seeds_each_geo_sees_every_mid_and_final(self):
        seen = {g: {"mid": set(), "final": set()} for g in OR["geos"]}
        pairs = set()
        for seed in range(1, 51):
            reset()
            random.seed(seed)
            for i in range(4):
                with self.subTest(seed=seed, i=i):
                    ob = self._check(gen())
                    if i == 0:
                        self.assertNotEqual(ob["geo"], "R1")   # ilk üretimde R1 yok
                    seen[ob["geo"]]["mid"].add(ob["mid"])
                    seen[ob["geo"]]["final"].add(ob["final"])
                    pairs.add((ob["mid"], ob["final"]))
        for g, s in seen.items():
            self.assertEqual(s["mid"], set(OR["mids"]), g)
            self.assertEqual(s["final"], set(OR["finals"]), g)
        self.assertEqual(pairs & BANNED, set())
        self.assertIsNone(es.HIT_OVERRIDE.get())

    def test_consecutive_lru(self):
        for seed in range(1, 16):
            reset()
            random.seed(seed)
            runs = [self._check(gen()) for _ in range(8)]
            for key, block in (("geo", 3), ("vehicle", 2), ("mid", 1), ("final", 1)):
                vals = [r[key] for r in runs]
                for i in range(len(vals)):
                    self.assertNotIn(vals[i], vals[max(0, i - block):i], (seed, key, vals))
            self.assertNotEqual(runs[0]["geo"], "R1")
            self.assertTrue({r["people"] for r in runs} <= {3, 4})

    def test_history_sources(self):
        def combo(tag):
            return f"{DOMAIN}|none|{WF.lower()}|balcony of a hillside house##{tag}|bystander_handheld"
        reset()
        hist = [combo("M1+N1"), combo("K5+L4"), combo("M3+N2")]
        for s in range(30):
            self.assertIn(hp.orman_choose_mid(hist, random.Random(s)), ("M1", "M2"))   # son 1: M3 elenir
            self.assertEqual(hp.orman_choose_final(hist, "M2", random.Random(s)), "N1")   # N3 yasak, N2 son 1
        recs = [{"eksenler": json.dumps({"event": WF, "axes": {"mod": "orman_yaklasma", "cografya": g, "arac": v}})}
                for g, v in (("R2", "SUV"), ("R3", "white van"), ("R4", "SUV"))] + [{"eksenler": "x"}]
        self.assertEqual(hp.orman_axes_history(recs, "cografya"), ["R2", "R3", "R4"])
        self.assertEqual(hp.orman_axes_history(recs, "arac"), ["SUV", "white van", "SUV"])
        self.assertIsNone(hp.orman_axes_history(None, "arac"))
        for seed in range(1, 11):
            reset()
            random.seed(seed)
            d = gen(axes_loader=lambda dom: recs)
            ob = d["structure"]["orman_yaklasma"]
            self.assertIn(ob["geo"], ("R1", "R5", "R6"))
            self.assertEqual(ob["vehicle"], "pickup truck")
            axes = json.loads(d["axes_json"])["axes"]
            self.assertEqual((axes["mod"], axes["cografya"], axes["arac"]), ("orman_yaklasma", ob["geo"], ob["vehicle"]))

    def test_camera_follow_and_fixed(self):
        for seed in range(1, 6):
            p = build(seed)["scenes"][0]["prompt"]
            self.assertIn(f"slight hand shake, {FOLLOW}; one continuous shot", p)
        with patch.object(hp, "ORMAN_YAKLASMA_KAMERA_TAKIP", False):
            for seed in range(1, 11):
                d = build(seed)
                self._check(d)
                p = d["scenes"][0]["prompt"]
                self.assertIn(f"slight hand shake, {FIXED}; one continuous shot", p)
                self.assertNotIn(FOLLOW, p)
                self.assertIn("Kamera: sabit", d["structure"]["orman_yaklasma"]["lines"])

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
        for bad in ({"geo": "R9"}, {"mid": "K5"}, {"final": "L4"}, {"people": 6}, {"mid": "M2", "final": "N3"},
                    {"mid": "M4"}, {"final": "N4"}, {"mid": "M4", "final": "N1"}):
            self.assertTrue(cp.submit_issues({**st, "orman_yaklasma": {**st["orman_yaklasma"], **bad}}, info), bad)
        story = asyncio.run(cp.rewrite_structured(st, "test", AsyncMock(side_effect=AssertionError("GPT"))))
        self.assertEqual(story, sc["story"])

    def test_approval_lines_and_display(self):
        d = build(1)
        sc, st = d["scenes"][0], d["structure"]
        ob = st["orman_yaklasma"]
        lines = ob["lines"].split("\n")
        self.assertEqual(lines[0], "Mod: ⭐ Hit kalıbı · Yaklaşma (orman yangını)")
        self.assertEqual(lines[1], f"Coğrafya: {ob['geo']} {OR['geos'][ob['geo']]['name']}")
        self.assertEqual(lines[2], f"Araç: {ob['vehicle']}")
        self.assertTrue(lines[3].startswith(f"Orta (4-9s): {ob['mid']} «Just ahead of the flames, "))
        self.assertTrue(lines[4].startswith(f"Final (9-15s): {ob['final']} «Right below the balcony"))
        self.assertEqual(lines[5], "Kamera: takip (alev duvarını izlemek için döner)")
        self.assertEqual(lines[6], f"Kelime: {len(sc['prompt'].split())} (en fazla 230) · karakter: "
                                   f"{len(sc['prompt'])} (en fazla 1400)")
        self.assertEqual(len(lines), 7)
        # Onay görüntüsü: 1. Seçim / 3. Hikâye / Eksenler gerçek parçalar
        shown = sections_to_text(format_generation(d["trace"])) + "\n" + st["axes_line"]
        sel, _, rest = shown.partition("🔍 2.")
        story = rest.split("🔍 3. Hikâye\n", 1)[1]
        for part in (hp.orman_opening(ob["geo"]), hp.orman_mid(ob["mid"], ob["vehicle"]), OR["finals"][ob["final"]]):
            self.assertIn(part, sc["prompt"])
            self.assertIn(part, sel)
            self.assertIn(part, story)
        self.assertIn(hp.orman_camera_text(True), sel)
        self.assertIn("Mod: ⭐ Hit kalıbı · Yaklaşma (orman yangını)", sel)
        self.assertIn("kamera modu=takip", st["axes_line"])
        self.assertIn(f"araç={ob['vehicle']}", st["axes_line"])
        self.assertIn(f"orta={ob['mid']}", st["axes_line"])
        self.assertIn(f"final={ob['final']}", st["axes_line"])
        self.assertIn(f"coğrafya={ob['geo']} {OR['geos'][ob['geo']]['name']}", st["axes_line"])
        for absent in (st["spec"]["key_visual"], "kamera modu=A", "kamera modu=B"):
            self.assertNotIn(absent, shown)
        _, body = format_final_prompt({"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"],
                                       "hit_lines": ob["lines"], "environment": st["environment"]})
        self.assertIn("\nMod: ⭐ Hit kalıbı · Yaklaşma (orman yangını)\n", body)
        self.assertIn("\n\n" + sc["prompt"], body)

    def test_normal_wildfire_untouched(self):
        reset()
        random.seed(5)
        d = asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": WF, "used_combos": [],
                                                     "recent_topics": []}))
        self.assertNotIn("orman_yaklasma", d["structure"])
        self.assertNotIn("mode_label", d["trace"])
        for x in (ACTION, "races toward the camera", "Right below the balcony", "never thin lines or strips of fire"):
            self.assertNotIn(x, d["scenes"][0]["prompt"])


class TestOrmanPipelineAndBot(_Quiet):
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
                return await orig(**kw, orman_yaklasma=True)
            with patch.object(main, "run_pipeline", run_with):
                r = t.run_pipe(gen=AsyncMock(side_effect=fake_gen), reporter=rep, event=WF)
        finally:
            t.doCleanups()
        self.assertTrue(r["success"], r)
        self.assertIs(seen["config"]["orman_yaklasma"], True)
        approve = [c[1] for c in rep.calls if c[0] == "approve"]
        self.assertEqual(len(approve), 1)
        info = approve[0]
        self.assertTrue(info["hit_lines"].startswith("Mod: ⭐ Hit kalıbı · Yaklaşma (orman yangını)\nCoğrafya: R"))
        self.assertEqual(t.create.await_args.args[1], info["prompt"])   # Kie'ye giden = onaydaki

    def test_bot_button_and_flow(self):
        import bot
        from test_tur29_infra import _context, _update
        di = str(bot.DOMAIN_KEYS.index(DOMAIN))
        ei = str(bot.domain_events(DOMAIN).index(WF))
        ctx = _context()
        upd = _update(data=f"uret:e:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, ctx))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        labels = [b.text for r in kb.inline_keyboard for b in r]
        self.assertEqual(labels, ["✅ Üret", "❌ İptal", "⭐ Hit kalıbı · Yaklaşma"])
        self.assertEqual([len(r) for r in kb.inline_keyboard], [2, 1])   # buton Üret/İptal'in altında
        self.assertNotIn("⭐ Hit kalıbı", labels)   # eski orman hit butonu gizli
        upd = _update(data=f"uret:oy:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, ctx))
        self.assertIn("Mod: ⭐ Hit kalıbı · Yaklaşma (orman yangını)",
                      upd.callback_query.edit_message_text.await_args.args[0])
        upd = _update(data=f"uret:oyok:{di}:{ei}")
        runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
        with patch.object(bot.pipeline, "run_pipeline", runner), patch.object(bot, "_production_lock", asyncio.Lock()):
            asyncio.run(bot.on_callback(upd, ctx))
        kw = runner.await_args.kwargs
        self.assertEqual((kw["event"], kw["orman_yaklasma"]), (WF, True))
        self.assertNotIn("kul_yaklasma", kw)
        self.assertTrue(kw["reporter"].needs_approval)
        # diğer yangın olaylarında bu buton yok (ateş hortumu kendi Hit butonlarını korur)
        for i, e in enumerate(bot.domain_events(DOMAIN)):
            if e == WF:
                continue
            upd = _update(data=f"uret:e:{di}:{i}")
            asyncio.run(bot.on_callback(upd, ctx))
            kw = upd.callback_query.edit_message_text.await_args.kwargs
            if "reply_markup" in kw:
                cbs = [b.callback_data for r in kw["reply_markup"].inline_keyboard for b in r]
                self.assertFalse(any(c.startswith("uret:oy") for c in cbs), e)
        self.assertIsNone(bot.parse_orman(di, str(next(i for i, e in enumerate(bot.domain_events(DOMAIN))
                                                       if e != WF))))


if __name__ == "__main__":
    unittest.main()
