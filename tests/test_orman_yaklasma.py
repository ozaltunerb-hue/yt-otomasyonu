# 13 Kas 2026, Bahadır: orman yangını "⭐ Hit kalıbı · Yaklaşma" modu (core/hit_prompts.py YAKLASMA_ORMAN).
# Orman yangını hit'i (9 Eki 21:52, K5+L4) + kül bulutu Yaklaşma yapısı. GPT yok, zaman etiketleri var. Orman yangınının
# normal yolu, kayıtlı orman hit prompt'u ve diğer bütün olay/modlar değişmez. Ağ yok.
# 20 Kas 2026 v4 ("ilk 3 saniye olay kuralı"): ilk karede yanan ev, büyük kadraj, action hikâyede yok, M1/N2 pasif.
# 20 Kas 2026 v5: ev balkonun tam karşısında ve yakın, alevler yolda sıvı gibi akmaz (v4 metinleri pasif, kayıt fixture).
# 20 Kas 2026 v6: ateş yoldan çıktı, araç garaj yolunda (v5 ortaları ve stil eki pasif, v5 kaydı fixture).
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
# 20 Kas 2026 v5 (yakın ev, akan ateş yasağı, Bahadır): açılış ve stil eki birebir
OPENING = ("From the very first frame {place} is burning: the house right across from the balcony, close and big in "
           "frame, bursts into flames from ground to roof, windows blowing out, as a towering wall of flames races down "
           "the {forest} slope behind it.")
# 20 Kas 2026 v6 (ateş yolda yok, araç garaj yolunda, Bahadır): ortalar ve stil eki birebir
TAIL = ("Handheld footage shot from the balcony of a hillside house overlooking the street and the burning slope, high "
        "vantage, normal lens, a corner of the balcony railing in the foreground; slight hand shake, {camera}; one "
        "continuous shot, no zoom, no cuts. The fire spreads only through trees, yards and houses, never along the "
        "asphalt; burning vehicles stay whole. Never a calm moment. Civilians in everyday clothes, never CGI. Realistic "
        "wildfire: towering, roaring flames and thick smoke, never thin lines or strips of fire. Raw natural light under "
        "an orange smoky sky. Real time, never slow motion, people run at full speed.")
MIDS = {"M2": "Beside the street, big in frame, a burning tree crashes down onto a {vehicle} parked in a driveway, "
              "crushing its roof in a burst of sparks.",
        "M3": "Beside the street, big in frame, flames from a burning house pour over the {vehicle} in its driveway, "
              "its windows bursting as it catches fire."}
CALM = ("The fire spreads only through trees, yards and houses, never along the asphalt; burning vehicles stay whole. "
        "Never a calm moment.")   # v6
TAIL_V5 = ("Handheld footage shot from the balcony of a hillside house overlooking the street and the burning slope, high "
        "vantage, normal lens, a corner of the balcony railing in the foreground; slight hand shake, {camera}; one "
        "continuous shot, no zoom, no cuts. The fire keeps spreading through trees and houses the whole time, never "
        "flowing along the road like liquid, never a calm moment. Civilians in everyday clothes, never CGI. Realistic "
        "wildfire: towering, roaring flames and thick smoke, never thin lines or strips of fire. Raw natural light under "
        "an orange smoky sky. Real time, never slow motion, people run at full speed.")
# 20 Kas 2026 v4 ("ilk 3 saniye olay kuralı", Bahadır): metinler birebir (v5'te açılış pasif, ortalar/finaller aynen)
OPENING_V4 = ("From the very first frame {place} is burning: the house across the street, big in frame, bursts into flames "
           "from ground to roof, windows blowing out, as a towering wall of flames races down the {forest} slope toward "
           "the camera.")
MIDS_V5 = {"M2": "In the middle of the street, big in frame, a huge burning tree crashes down onto the {vehicle}, crushing "
              "its roof in a burst of sparks.",
        "M3": "In the middle of the street, big in frame, the wall of flames swallows a parked {vehicle}, its windows "
              "bursting as it disappears into the fire."}
FINALS = {"N1": "Right below the balcony, big in frame, the flames reach the nearest house and its roof caves in, a "
                "fountain of sparks bursting up toward the camera.",
          "N3": "Right below the balcony, big in frame, a burning tree topples onto the nearest house, smashing through "
                "its roof as flames pour inside."}
CALM_V5 = "The fire keeps spreading through trees and houses the whole time, never flowing along the road like liquid, never a calm moment."
CALM_V4 = "The fire keeps spreading the whole time, never a calm moment."
ACTION = "Burning embers and thick smoke blow across the street from the very first frame."   # v4: hikâyede yok
BANNED = {("M2", "N3")}
BANNED_V3 = {("M2", "N3"), ("M2", "N2"), ("M3", "N2")}
REQUIRED = ("From the very first frame", "big in frame", "right across from the balcony", "Beside the street",
            "never along the asphalt", "Never a calm moment")   # v6
REQUIRED_V5 = ("From the very first frame", "big in frame", "never a calm moment", "right across from the balcony",
               "never flowing along the road like liquid")
REQUIRED_V4 = ("From the very first frame", "big in frame", "never a calm moment")
FORBIDDEN = ("Full action", "Until the last frame", "U-turn", "speeds away", "wooden deck", "halfway down the street",
             "Burning embers", "In the middle of the street", "disappears into the fire")   # v6: +2
VEHICLE_WORDS = ("van", "truck", "SUV", "car", "vehicle", "{")
# 40 tohum kilidi (prompt / hikâye / stil eki / combo / eksenler; caption hariç). v3 kaydı fixtures/orman_v3_runs_40.json
ORMAN_SHA256 = "d5da37441edc312cd2df6cac06cbef275ef5abb2aba2d9b63d9a5d68ef27cf54"      # 20 Kas v6
ORMAN_V5_SHA256 = "956522fb613affb0da8469de9648f80989cc37eae8ecb05dd612aa2a2231e87d"   # bbce59c (v5)
ORMAN_V4_SHA256 = "f1fe3b66f3a905b331974265d31dc9282a6811a7686f656c1401231ab931d62f"   # 903c6ab (v4)
ORMAN_V3_SHA256 = "95661aaea8cc185c6d836a658337575e5ca6390abd061f1e41569831cb4741a9"   # 3c0369c (v3)
V3_FIXTURE = os.path.join(ROOT, "tests", "fixtures", "orman_v3_runs_40.json")
V4_FIXTURE = os.path.join(ROOT, "tests", "fixtures", "orman_v4_runs_40.json")   # 20 Kas v5: v4 kaydı
V5_FIXTURE = os.path.join(ROOT, "tests", "fixtures", "orman_v5_runs_40.json")   # 20 Kas v6: v5 kaydı


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


def snapshot_hash(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def orman_snapshot() -> dict:
    """Diğer testlerin others_snapshot "orman" kaydıyla aynı biçim (domain None, GPT yok, caption hariç); 40 tohum."""
    def strip(js):
        try:
            d = json.loads(js)
        except (TypeError, ValueError):
            return js
        d.pop("caption", None)
        return d
    runs = {}
    for s in range(1, 41):
        ps.reset_memory()
        for name in dir(hp):
            if name.startswith("_") and name.endswith("_MEMORY") and isinstance(getattr(hp, name), list):
                getattr(hp, name).clear()
        random.seed(s)
        with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT"))):
            d = asyncio.run(pg.generate_creative_prompts({"domain": None, "event": WF, "orman_yaklasma": True,
                                                         "used_combos": [], "recent_topics": []}))
        sc = d["scenes"][0]
        runs[str(s)] = {"prompt": sc["prompt"], "story": sc["story"], "suffix": sc["style_suffix"],
                        "combo": d["combo_key"], "axes": strip(d.get("axes_json", ""))}
    return runs


def load_v5_runs() -> dict:
    """v5 (bbce59c) 40 tohum kaydı (20 Kas v6'da fixture'a alındı)."""
    with open(V5_FIXTURE, encoding="utf-8") as f:
        return json.load(f)


def load_v4_runs() -> dict:
    """v4 (903c6ab) 40 tohum kaydı (20 Kas v5'te fixture'a alındı)."""
    with open(V4_FIXTURE, encoding="utf-8") as f:
        return json.load(f)


def load_v3_runs() -> dict:
    """v3 (3c0369c) 40 tohum kaydı; diğer testlerin OTHERS_SHA256 kilidi orman kaydı olarak bunu kullanır."""
    with open(V3_FIXTURE, encoding="utf-8") as f:
        return json.load(f)


class TestTexts(_Quiet):
    def test_verbatim_texts(self):
        self.assertEqual(hp.ORMAN_MODE_LABEL, "⭐ Hit kalıbı · Yaklaşma (orman yangını)")
        self.assertEqual(hp.ORMAN_VERSION_LABEL, "Sürüm: v6 (ateş yolda yok, araç garaj yolunda)")
        self.assertEqual(hp.ORMAN_VERSION_LABEL_V5, "Sürüm: v5 (yakın ev, akan ateş yok)")
        self.assertEqual(hp.ORMAN_VERSION_LABEL_V4, "Sürüm: v4 (ilk 3 saniye olay)")
        self.assertIs(hp.ORMAN_YAKLASMA_KAMERA_TAKIP, True)
        self.assertEqual(sorted(OR["geos"]), ["R1", "R2", "R3", "R4", "R5", "R6"])
        geos = {"R1": ("pine-covered", "a hillside neighborhood of wooden suburban houses"),
                "R2": ("eucalyptus-covered", "a hillside neighborhood of tin-roofed weatherboard houses"),
                "R3": ("pine-covered", "a hillside village of whitewashed terracotta-roofed houses"),
                "R4": ("spruce-covered", "a hillside town of dark-roofed timber houses"),
                "R5": ("eucalyptus-covered", "a hillside village of tile-roofed stone houses"),
                "R6": ("pine-covered", "a hillside town of colorful wooden houses")}
        self.assertEqual(OR["opening"], OPENING)
        for g, (forest, place) in geos.items():
            self.assertEqual((OR["geos"][g]["forest"], OR["geos"][g]["place"]), (forest, place))
            self.assertEqual(hp.orman_opening(g),
                             f"From the very first frame {place} is burning: the house right across from the "
                             "balcony, close and big in frame, bursts into flames from ground to roof, windows blowing "
                             f"out, as a towering wall of flames races down the {forest} slope behind it.")
        self.assertEqual([OR["geos"][g]["name"] for g in sorted(OR["geos"])],
                         ["Kaliforniya", "Avustralya", "Yunanistan", "Kanada", "Portekiz", "Şili"])
        self.assertEqual(hp.orman_people(3), "Three people run up the street below, away from the flames.")
        self.assertEqual(hp.orman_people(4), "Four people run up the street below, away from the flames.")
        self.assertEqual(OR["action"], ACTION)
        self.assertEqual(OR["vehicles"], ("white van", "pickup truck", "SUV"))
        self.assertEqual(OR["mids"], MIDS)
        self.assertEqual(OR["finals"], FINALS)
        self.assertEqual(OR["vehicle_mids"], ("M2", "M3"))
        self.assertEqual(hp.orman_camera_text(True), FOLLOW)
        self.assertEqual(hp.orman_camera_text(False), FIXED)
        self.assertEqual(hp.orman_tail(True),
                         "Handheld footage shot from the balcony of a hillside house overlooking the street and the "
                         "burning slope, high vantage, normal lens, a corner of the balcony railing in the foreground; "
                         f"slight hand shake, {FOLLOW}; one continuous shot, no zoom, no cuts. {CALM} Civilians in "
                         "everyday clothes, never CGI. Realistic wildfire: towering, roaring flames and thick smoke, "
                         "never thin lines or strips of fire. Raw natural light under an orange smoky sky. Real time, "
                         "never slow motion, people run at full speed.")
        self.assertEqual(OR["tail"], TAIL)
        self.assertEqual(hp.orman_tail(False), TAIL.format(camera=FIXED))
        self.assertNotIn("no face close to the camera", TAIL)
        self.assertNotIn("No readable signs", TAIL)
        self.assertEqual(hp.orman_mid("M2", "pickup truck"),
                         "Beside the street, big in frame, a burning tree crashes down onto a pickup truck parked in a "
                         "driveway, crushing its roof in a burst of sparks.")
        self.assertEqual(hp.orman_mid("M3", "SUV"),
                         "Beside the street, big in frame, flames from a burning house pour over the SUV in its "
                         "driveway, its windows bursting as it catches fire.")
        for x in ("never flowing along the road like liquid", "never a calm moment", "In the middle of the street",
                  "disappears into the fire"):
            self.assertNotIn(x, TAIL + json.dumps(MIDS))
        self.assertEqual((hp.ORMAN_GEO_BLOCK, hp.ORMAN_VEHICLE_BLOCK, hp.ORMAN_MID_BLOCK, hp.ORMAN_FINAL_BLOCK),
                         (3, 2, 1, 1))
        self.assertEqual(hp.ORMAN_BANNED_PAIRS, (("M2", "N3"),))
        self.assertEqual((hp.ORMAN_REQUIRED, hp.ORMAN_FORBIDDEN), (REQUIRED, FORBIDDEN))
        self.assertEqual((hp.ORMAN_MAX_WORDS, hp.ORMAN_MAX_CHARS), (230, 1400))

    def test_passive_texts_kept_never_chosen(self):
        """v4 metinleri (ORMAN_OPENING_V4, ORMAN_TAIL_V2), v3 metinleri (ORMAN_*_V3, ORMAN_ACTION_V1, ORMAN_TAIL_V1)
        ve eski V1/V2 saklı; M1, M4, N2, N4 pasif (ORMAN_PASIF), hiç seçilmez ve hikâye kurulamaz."""
        self.assertEqual(hp.ORMAN_MIDS_V5, MIDS_V5)   # v6: v5 ortaları ve stil eki pasif
        self.assertEqual(hp.ORMAN_TAIL_V3, TAIL_V5)
        self.assertEqual(hp.ORMAN_REQUIRED_V5, REQUIRED_V5)
        self.assertNotEqual(OR["mids"], hp.ORMAN_MIDS_V5)
        self.assertNotEqual(OR["tail"], hp.ORMAN_TAIL_V3)
        self.assertEqual(hp.ORMAN_OPENING_V4, OPENING_V4)
        self.assertEqual(hp.ORMAN_TAIL_V2, hp.ORMAN_TAIL_V1.replace("no face close to the camera.",
                                                                    f"no face close to the camera. {CALM_V4}", 1))
        self.assertEqual(hp.ORMAN_REQUIRED_V4, REQUIRED_V4)
        self.assertNotEqual(OR["opening"], hp.ORMAN_OPENING_V4)
        self.assertNotEqual(OR["tail"], hp.ORMAN_TAIL_V2)
        self.assertEqual(hp.ORMAN_OPENING_V3, "A towering wall of flames has already swept down the {forest} slope and "
                                              "is racing halfway down the street through {place} toward the camera, "
                                              "igniting roofs and trees as it comes.")
        self.assertEqual(hp.ORMAN_ACTION_V1, ACTION)
        self.assertEqual(hp.ORMAN_MIDS_V3, {
            "M1": "Just ahead of the flames, the {vehicle} speeds away as the wall of flames closes the road right "
                  "behind it.",
            "M2": "Just ahead of the flames, a huge burning pine crashes down onto the {vehicle}, crushing its roof.",
            "M3": "Just ahead of the flames, the wall of flames swallows a parked {vehicle}, its windows bursting as it "
                  "disappears into the fire."})
        self.assertEqual(hp.ORMAN_FINALS_V3, {
            "N1": "Right below the balcony, the flames reach the nearest house and its roof caves in, a fountain of "
                  "sparks bursting up toward the camera.",
            "N2": "Right below the balcony, the wall of flames engulfs the garden and wooden deck of the nearest house, "
                  "burning planks collapsing in a shower of sparks.",
            "N3": "Right below the balcony, a burning tree topples onto the nearest house, smashing through its roof as "
                  "flames pour inside."})
        self.assertEqual(hp.ORMAN_TAIL_V1,
                         "Handheld footage shot from the balcony of a hillside house overlooking the street and the "
                         "burning slope, high vantage, normal lens, a corner of the balcony railing in the foreground; "
                         "slight hand shake, {camera}; one continuous shot, no zoom, no cuts, no face close to the "
                         "camera. Civilians in everyday clothes, never CGI. Realistic wildfire: towering, roaring "
                         "flames and thick smoke, never thin lines or strips of fire. Raw natural light under an orange "
                         "smoky sky. Real time, never slow motion, people run at full speed. No readable signs, text or "
                         "flags.")
        self.assertEqual(set(hp.ORMAN_BANNED_PAIRS_V3), BANNED_V3)
        self.assertEqual(hp.ORMAN_OPENING_V1, "A towering wall of flames sweeps down the {forest} slope at the far end "
                                              "of the street and slams into the edge of {place}, igniting roofs and "
                                              "trees as it races toward the camera.")
        self.assertEqual(hp.ORMAN_OPENING_V2, "A towering wall of flames has already swept down the {forest} slope at "
                                              "the far end of the street and is racing through the edge of {place} "
                                              "toward the camera, igniting roofs and trees as it comes.")
        self.assertEqual(hp.ORMAN_MIDS_V2["M1"], "Halfway down the street, the {vehicle} speeds away as the wall of "
                                                 "flames closes the road right behind it.")
        self.assertEqual(sorted(hp.ORMAN_PASIF["mids"]), ["M1", "M4"])
        self.assertEqual(sorted(hp.ORMAN_PASIF["finals"]), ["N2", "N4"])
        self.assertEqual(hp.ORMAN_PASIF["mids"]["M1"], hp.ORMAN_MIDS_V3["M1"])
        self.assertEqual(hp.ORMAN_PASIF["finals"]["N2"], hp.ORMAN_FINALS_V3["N2"])
        self.assertEqual(hp.ORMAN_PASIF["mids"]["M4"], "Halfway down the street, two houses on either side of the road "
                                                       "catch fire at once, flames pouring out of their windows and "
                                                       "roofs.")
        self.assertEqual(hp.ORMAN_PASIF["finals"]["N4"], "Right below the balcony, the fire jumps the street and the "
                                                         "wooden fence and carport below burst into flames, heat and "
                                                         "sparks rushing up toward the camera.")
        for s in range(200):
            r = random.Random(s)
            self.assertIn(hp.orman_choose_mid([], r), ("M2", "M3"))
            for m in ("M2", "M3"):
                self.assertIn(hp.orman_choose_final([], m, r), ("N1", "N3"))
        for m, f in (("M1", "N1"), ("M4", "N1"), ("M2", "N2"), ("M3", "N4")):
            with self.assertRaises((es.StructureError, KeyError)):
                hp.orman_story("R2", 3, m, "SUV", f)

    def test_vehicle_fill(self):
        for v in OR["vehicles"]:
            self.assertEqual(hp.orman_mid("M2", v), MIDS["M2"].format(vehicle=v))
            self.assertEqual(hp.orman_mid("M3", v), MIDS["M3"].format(vehicle=v))
            for m in ("M1", "M4"):   # pasif
                with self.assertRaises(es.StructureError):
                    hp.orman_mid(m, v)
        for m in ("M2", "M3"):
            with self.assertRaises(es.StructureError):
                hp.orman_mid(m, None)

    def test_banned_pair_m2_n3(self):
        """v4: yalnız M2+N3 yasak (iki kez ağaç); M2 yalnız N1'e gider."""
        with self.assertRaises(es.StructureError):
            hp.orman_story("R2", 3, "M2", "SUV", "N3")
        for s in range(60):
            self.assertEqual(hp.orman_choose_final([], "M2", random.Random(s)), "N1")
        self.assertEqual({m: sorted(f for f in OR["finals"] if (m, f) not in BANNED) for m in OR["mids"]},
                         {"M2": ["N1"], "M3": ["N1", "N3"]})
        for m, f in (("M2", "N1"), ("M3", "N1"), ("M3", "N3")):
            hp.orman_story("R2", 3, m, "SUV", f)

    def test_story_order_without_action(self):
        """v4: hikâye sırası "0-4s: {opening} {people} 4-9s: {mid} 9-15s: {final}"; action cümlesi hiç yok."""
        for (g, ppl, v, m, f, follow), p in all_combos():
            story = hp.orman_story(g, ppl, m, v, f)
            self.assertEqual(story, f"0-4s: {hp.orman_opening(g)} {hp.orman_people(ppl)} 4-9s: "
                                    f"{MIDS[m].format(vehicle=v)} 9-15s: {FINALS[f]}")
            self.assertNotIn(ACTION, p)
            self.assertNotIn("Burning embers", p)

    def test_lru_alternates_mid_and_final(self):
        """Orta ve final son 1: iki seçenek dönüşümlü gelir. Son final N1 ise orta M3 (M2 yalnız N1'e gidebilir)."""
        def tag(t):
            return f"{DOMAIN}|none|{WF.lower()}|x##{t}|y"
        reset()
        for s in range(60):
            r = random.Random(s)
            self.assertEqual(hp.orman_choose_mid([tag("M2+N1")], r), "M3")
            self.assertEqual(hp.orman_choose_final([tag("M2+N1")], "M3", r), "N3")
            self.assertEqual(hp.orman_choose_mid([tag("M3+N3")], r), "M2")
            self.assertEqual(hp.orman_choose_final([tag("M3+N3")], "M2", r), "N1")
            self.assertEqual(hp.orman_choose_mid([tag("M3+N1")], r), "M3")   # M2 aday değil (N1 son final)
            self.assertEqual(hp.orman_choose_final([tag("M3+N1")], "M3", r), "N3")
        for seed in range(1, 21):   # ardışık üretimler: ilk çiftten sonra M2+N1 / M3+N3 dönüşümlü
            reset()
            random.seed(seed)
            runs = [gen()["structure"]["orman_yaklasma"] for _ in range(8)]
            pairs = [(r["mid"], r["final"]) for r in runs]
            self.assertEqual(set(pairs) & BANNED, set(), pairs)
            for i in range(2, len(pairs)):
                self.assertNotEqual(pairs[i][0], pairs[i - 1][0], (seed, pairs))
                self.assertNotEqual(pairs[i][1], pairs[i - 1][1], (seed, pairs))
                self.assertIn(pairs[i], (("M2", "N1"), ("M3", "N3")), (seed, pairs))
            for i in range(1, len(pairs)):
                self.assertNotEqual(pairs[i][1], pairs[i - 1][1], (seed, pairs))

    def test_all_combos_within_limits(self):
        """6 coğrafya × 2 orta × 2 final × 3 araç × 3/4 kişi (M2+N3 hariç) = 108 kombinasyon (× 2 kamera): hepsi
        ≤ 230 kelime, ≤ 1400 karakter; v6 en uzun 229 / 1347 (R2, 3 kişi, pickup truck, M2+N1, takip kamerası),
        yedek kısaltma gerekmedi."""
        n, over, longest = 0, [], (0, 0, None)
        for key, p in all_combos():
            n += 1
            w, c = len(p.split()), len(p)
            longest = max(longest, (w, c, key))
            if w > hp.ORMAN_MAX_WORDS or c > hp.ORMAN_MAX_CHARS:
                over.append((key, w, c))
            for bad in FORBIDDEN:
                self.assertNotIn(bad, p, key)
            for need in REQUIRED:
                self.assertIn(need, p, key)
            for lab in ("0-4s: ", " 4-9s: ", " 9-15s: "):
                self.assertIn(lab, p)
            self.assertTrue(p.startswith("0-4s: From the very first frame "), key)
            self.assertIn("never thin lines or strips of fire", p)
            self.assertIn("a corner of the balcony railing in the foreground", p)
            self.assertIn(f"no zoom, no cuts. {CALM} Civilians", p)
            self.assertIn("Civilians in everyday clothes, never CGI.", p)   # v6: yedek kısaltma gerekmedi
            self.assertTrue(p.endswith("people run at full speed."), key)
            self.assertIn("is burning: the house right across from the balcony, close and big in frame, ", p)
            self.assertIn(" slope behind it. ", p)
            rest = p.split(" 4-9s: ")[1]
            self.assertTrue(rest.startswith("Beside the street, big in frame, "), key)
            _, _, v, m, _, _ = key
            self.assertIn({"M2": f" a {v} parked in a driveway, ", "M3": f" the {v} in its driveway, "}[m], rest, key)
            self.assertNotIn("middle of the street", p, key)
            self.assertIn(" 9-15s: Right below the balcony, big in frame, ", rest)
            self.assertTrue(any(f" {v}" in rest.split(" 9-15s: ")[0] for v in OR["vehicles"]), key)
            for txt in (*hp.ORMAN_PASIF["mids"].values(), *hp.ORMAN_PASIF["finals"].values()):
                self.assertNotIn(txt.split("{vehicle}")[-1], p)
        self.assertEqual(n // 2, 108)
        self.assertEqual(n, 6 * 2 * 3 * 3 * 2)
        self.assertEqual(over, [], f"en uzun: {longest}")
        self.assertEqual(longest[:2], (229, 1347))
        self.assertEqual(longest[2], ("R2", 3, "pickup truck", "M2", "N1", True))
        self.assertEqual(max(len(p) for _, p in all_combos()), 1350)

    def test_issues_required_and_forbidden(self):
        """Kie öncesi denetim: zorunlu ifade yoksa ya da yasak ifade varsa gönderilmez; seçenek listeleri güncel."""
        d = build(3)
        sc, st = d["scenes"][0], d["structure"]
        info = {"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"]}
        self.assertEqual(hp.orman_issues(st, info), [])
        for need in REQUIRED:
            bad = {**info, "prompt": sc["prompt"].replace(need, "x")}
            self.assertIn(f"zorunlu ifade eksik: {need}", hp.orman_issues(st, bad))
        self.assertIn("zorunlu ifade eksik: right across from the balcony", hp.orman_issues(st, {
            **info, "prompt": sc["prompt"].replace("right across from the balcony", "across the street")}))
        self.assertIn("zorunlu ifade eksik: Beside the street", hp.orman_issues(st, {
            **info, "prompt": sc["prompt"].replace("Beside the street", "In the middle of the street")}))
        self.assertIn("bu modda olmayan ifade var: In the middle of the street", hp.orman_issues(st, {
            **info, "prompt": sc["prompt"].replace("Beside the street", "In the middle of the street")}))
        self.assertIn("zorunlu ifade eksik: never along the asphalt", hp.orman_issues(st, {
            **info, "prompt": sc["prompt"].replace("never along the asphalt", "never flowing along the road like liquid")}))
        low = hp.orman_issues(st, {**info, "prompt": sc["prompt"].replace("Never a calm moment", "never a calm moment")})
        self.assertIn("zorunlu ifade eksik: Never a calm moment", low)   # büyük N
        for old in ("never flowing along the road like liquid", "never a calm moment"):   # v6: artık zorunlu değil
            self.assertNotIn(old, hp.ORMAN_REQUIRED)
        for word in FORBIDDEN:
            bad = {**info, "prompt": sc["prompt"].replace("Civilians in everyday", f"{word}. Civilians in everyday")}
            self.assertIn(f"bu modda olmayan ifade var: {word}", hp.orman_issues(st, bad))
        ob = st["orman_yaklasma"]
        self.assertEqual(hp.orman_issues({**st, "orman_yaklasma": {**ob, "mid": "M1"}}, info), ["orta M2, M3 değil (M1)"])
        self.assertEqual(hp.orman_issues({**st, "orman_yaklasma": {**ob, "final": "N2"}}, info),
                         ["final N1, N3 değil (N2)"])

    def test_sentences_only_in_this_mode(self):
        marks = ["is burning: the house right across from the balcony", "bursts into flames from ground to roof",
                 "windows blowing out, as a towering wall of flames races down the",
                 "Beside the street, big in frame,", "Right below the balcony, big in frame,",
                 "Three people run up the street below, away from the flames.",
                 "Four people run up the street below, away from the flames.",
                 "a burning tree crashes down onto a", "parked in a driveway, crushing its roof in a burst of sparks",
                 "flames from a burning house pour over the", "in its driveway, its windows bursting as it catches fire",
                 "a fountain of sparks bursting up toward the camera",
                 "a burning tree topples onto the nearest house", "The fire spreads only through trees, yards and houses",
                 "never along the asphalt; burning vehicles stay whole",
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


class TestOwnSnapshot(_Quiet):
    def test_orman_40_seeds_v6_lock(self):
        """20 Kas v6: 40 tohum kilidi ORMAN_SHA256; v3 kaydı (fixture) ORMAN_V3_SHA256 ile saklı ve değişmemiş."""
        snap = orman_snapshot()
        for s, r in snap.items():
            self.assertTrue(r["prompt"].startswith("0-4s: From the very first frame "), s)
            self.assertNotIn(ACTION, r["prompt"])
        self.assertEqual(snapshot_hash(snap), ORMAN_SHA256)
        v3 = load_v3_runs()
        self.assertEqual(snapshot_hash(v3), ORMAN_V3_SHA256)
        self.assertNotEqual(snapshot_hash(snap), ORMAN_V3_SHA256)
        self.assertNotEqual(snapshot_hash(snap), ORMAN_V4_SHA256)
        self.assertNotEqual(snapshot_hash(snap), ORMAN_V5_SHA256)
        self.assertEqual(sorted(v3, key=int), sorted(snap, key=int))
        # coğrafya ve araç seçimi (havuz + LRU aynen) tohum tohum v3 ile birebir
        for s in snap:
            for k in ("cografya", "arac", "people"):
                self.assertEqual(snap[s]["axes"]["axes"][k], v3[s]["axes"]["axes"][k], (s, k))

    def test_v5_fixture_lock_and_only_text_changed(self):
        """20 Kas v6: v5 (bbce59c) 40 tohum kaydı fixtures/orman_v5_runs_40.json, ORMAN_V5_SHA256 ile kilitli. v6'da
        seçim (coğrafya, araç, kişi, orta, final, combo, eksenler) tohum tohum v5 ile birebir; yalnız orta ve stil eki
        değişti: v5 promptunda orta/stil eki v6 metinleriyle değiştirilince v6 promptu çıkar."""
        v5, snap = load_v5_runs(), orman_snapshot()
        self.assertEqual(snapshot_hash(v5), ORMAN_V5_SHA256)
        self.assertEqual(sorted(v5, key=int), sorted(snap, key=int))
        for s in snap:
            self.assertEqual(snap[s]["axes"], v5[s]["axes"], s)
            self.assertEqual(snap[s]["combo"], v5[s]["combo"], s)
            ax = snap[s]["axes"]["axes"]
            mid, v = ax["beats"].split("+")[0], ax["arac"]
            old_mid, new_mid = MIDS_V5[mid].format(vehicle=v), MIDS[mid].format(vehicle=v)
            self.assertIn(old_mid, v5[s]["story"], s)
            self.assertEqual(snap[s]["suffix"], TAIL.format(camera=FOLLOW), s)
            self.assertEqual(v5[s]["suffix"], TAIL_V5.format(camera=FOLLOW), s)
            self.assertEqual(snap[s]["story"], v5[s]["story"].replace(old_mid, new_mid, 1), s)
            self.assertEqual(snap[s]["prompt"], v5[s]["prompt"].replace(old_mid, new_mid, 1)
                             .replace(v5[s]["suffix"], snap[s]["suffix"], 1), s)

    def test_v4_fixture_lock_and_v5_only_text_changed(self):
        """20 Kas v5: v4 (903c6ab) 40 tohum kaydı fixtures/orman_v4_runs_40.json, ORMAN_V4_SHA256 ile kilitli. v5
        kaydında seçim tohum tohum v4 ile birebir; yalnız açılış ve stil eki değişti (v6'da v5 kaydı fixture)."""
        v4, snap = load_v4_runs(), load_v5_runs()
        self.assertEqual(snapshot_hash(v4), ORMAN_V4_SHA256)
        self.assertEqual(sorted(v4, key=int), sorted(snap, key=int))
        for s in snap:
            self.assertEqual(snap[s]["axes"], v4[s]["axes"], s)
            self.assertEqual(snap[s]["combo"], v4[s]["combo"], s)
            g = OR["geos"][snap[s]["axes"]["axes"]["cografya"]]
            old_open = OPENING_V4.format(forest=g["forest"], place=g["place"])
            new_open = OPENING.format(forest=g["forest"], place=g["place"])
            self.assertEqual(snap[s]["suffix"], TAIL_V5.format(camera=FOLLOW), s)
            self.assertEqual(v4[s]["suffix"], hp.ORMAN_TAIL_V2.format(camera=FOLLOW), s)
            self.assertEqual(snap[s]["story"], v4[s]["story"].replace(old_open, new_open, 1), s)
            self.assertEqual(snap[s]["prompt"], v4[s]["prompt"].replace(old_open, new_open, 1)
                             .replace(v4[s]["suffix"], snap[s]["suffix"], 1), s)


class TestOrmanMode(_Quiet):
    def _check(self, d):
        sc, st = d["scenes"][0], d["structure"]
        ob = st["orman_yaklasma"]
        prompt = sc["prompt"]
        g = OR["geos"][ob["geo"]]
        self.assertIn(f"the {g['forest']} slope", prompt)
        self.assertIn(g["place"], prompt)
        self.assertTrue(prompt.startswith(f"0-4s: {hp.orman_opening(ob['geo'])} "))
        self.assertIn(f" {hp.orman_people(ob['people'])} 4-9s: ", prompt)
        self.assertNotIn(ACTION, prompt)
        self.assertIn(ob["vehicle"], OR["vehicles"])
        self.assertIn(ob["mid"], ("M2", "M3"))
        self.assertIn(ob["final"], ("N1", "N3"))
        self.assertNotIn((ob["mid"], ob["final"]), BANNED)
        mid_text = hp.orman_mid(ob["mid"], ob["vehicle"])
        self.assertIn(f"4-9s: {mid_text} 9-15s: {OR['finals'][ob['final']]} ", prompt)
        self.assertIn(f" {ob['vehicle']}", mid_text)   # her prompt'ta araçlı orta
        for lab in ("0-4s: ", " 4-9s: ", " 9-15s: "):
            self.assertIn(lab, prompt)
        for bad in FORBIDDEN:
            self.assertNotIn(bad, prompt)
        for need in REQUIRED:
            self.assertIn(need, prompt)
        self.assertIn("never thin lines or strips of fire", prompt)
        self.assertIn("a corner of the balcony railing in the foreground", prompt)
        self.assertTrue(prompt.endswith(" " + hp.orman_tail(ob["follow"])))
        self.assertEqual(sc["style_suffix"], hp.orman_tail(ob["follow"]))
        pos = [prompt.find(x) for x in ("0-4s: ", " 4-9s: ", " 9-15s: ", " Handheld footage", CALM)]
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
        self.assertEqual(pairs, {("M2", "N1"), ("M3", "N1"), ("M3", "N3")})
        self.assertIsNone(es.HIT_OVERRIDE.get())

    def test_consecutive_lru(self):
        for seed in range(1, 16):
            reset()
            random.seed(seed)
            runs = [self._check(gen()) for _ in range(8)]
            for key, block in (("geo", 3), ("vehicle", 2), ("final", 1)):
                vals = [r[key] for r in runs]
                for i in range(len(vals)):
                    self.assertNotIn(vals[i], vals[max(0, i - block):i], (seed, key, vals))
            mids = [r["mid"] for r in runs]
            for i in range(1, len(mids)):   # orta yalnız M3+N1 sonrasında tekrar eder (M2 N1'e gidemez)
                if mids[i] == mids[i - 1]:
                    self.assertEqual((runs[i - 1]["mid"], runs[i - 1]["final"], mids[i]), ("M3", "N1", "M3"))
            self.assertNotEqual(runs[0]["geo"], "R1")
            self.assertTrue({r["people"] for r in runs} <= {3, 4})

    def test_history_sources(self):
        def combo(tag):
            return f"{DOMAIN}|none|{WF.lower()}|balcony of a hillside house##{tag}|bystander_handheld"
        reset()
        hist = [combo("M2+N1"), combo("K5+L4"), combo("M3+N3")]
        for s in range(30):
            self.assertEqual(hp.orman_choose_mid(hist, random.Random(s)), "M2")   # son 1: M3 elenir
            self.assertEqual(hp.orman_choose_final(hist, "M2", random.Random(s)), "N1")   # N3 yasak
        old = [combo("M1+N2")]   # v3 kayıtları (pasif seçenekler) geçmişte kalabilir: seçimi bozmaz
        for s in range(30):
            m = hp.orman_choose_mid(old, random.Random(s))
            self.assertIn(m, ("M2", "M3"))
            self.assertIn(hp.orman_choose_final(old, m, random.Random(s)), ("N1", "N3"))
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
            "Civilians in everyday", f"{sk.FULL_MOTION} Civilians in everyday")}))
        for bad in ({"geo": "R9"}, {"mid": "K5"}, {"final": "L4"}, {"people": 6}, {"mid": "M2", "final": "N3"},
                    {"mid": "M1"}, {"final": "N2"}, {"mid": "M4"}, {"final": "N4"}, {"mid": "M1", "final": "N1"}):
            self.assertTrue(cp.submit_issues({**st, "orman_yaklasma": {**st["orman_yaklasma"], **bad}}, info), bad)
        story = asyncio.run(cp.rewrite_structured(st, "test", AsyncMock(side_effect=AssertionError("GPT"))))
        self.assertEqual(story, sc["story"])

    def test_approval_lines_and_display(self):
        d = build(1)
        sc, st = d["scenes"][0], d["structure"]
        ob = st["orman_yaklasma"]
        lines = ob["lines"].split("\n")
        self.assertEqual(lines[0], "Mod: ⭐ Hit kalıbı · Yaklaşma (orman yangını)")
        self.assertEqual(lines[1], "Sürüm: v6 (ateş yolda yok, araç garaj yolunda)")
        self.assertEqual(lines[2], f"Coğrafya: {ob['geo']} {OR['geos'][ob['geo']]['name']}")
        self.assertEqual(lines[3], f"Araç: {ob['vehicle']}")
        self.assertTrue(lines[4].startswith(f"Orta (4-9s): {ob['mid']} «Beside the street, big in frame, "))
        self.assertTrue(lines[5].startswith(f"Final (9-15s): {ob['final']} «Right below the balcony, big in frame, "))
        self.assertEqual(lines[6], "Kamera: takip (alev duvarını izlemek için döner)")
        self.assertEqual(lines[7], f"Kelime: {len(sc['prompt'].split())} (en fazla 230) · karakter: "
                                   f"{len(sc['prompt'])} (en fazla 1400)")
        self.assertEqual(len(lines), 8)
        # Onay görüntüsü: 1. Seçim / 3. Hikâye / Eksenler gerçek parçalar
        shown = sections_to_text(format_generation(d["trace"])) + "\n" + st["axes_line"]
        sel, _, rest = shown.partition("🔍 2.")
        story = rest.split("🔍 3. Hikâye\n", 1)[1]
        for part in (hp.orman_opening(ob["geo"]), hp.orman_mid(ob["mid"], ob["vehicle"]), OR["finals"][ob["final"]]):
            self.assertIn(part, sc["prompt"])
            self.assertIn(part, sel)
            self.assertIn(part, story)
        self.assertNotIn(ACTION, shown)
        self.assertNotIn(ACTION, d["plain_story"] if "plain_story" in d else sc.get("plain_story", ""))
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
        self.assertIn("\nMod: ⭐ Hit kalıbı · Yaklaşma (orman yangını)\nSürüm: v6 (ateş yolda yok, araç garaj yolunda)\n", body)
        self.assertIn("\n\n" + sc["prompt"], body)

    def test_normal_wildfire_untouched(self):
        reset()
        random.seed(5)
        d = asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": WF, "used_combos": [],
                                                     "recent_topics": []}))
        self.assertNotIn("orman_yaklasma", d["structure"])
        self.assertNotIn("mode_label", d["trace"])
        for x in (ACTION, "bursts into flames from ground to roof", "Right below the balcony",
                  "never thin lines or strips of fire", CALM):
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
        self.assertTrue(info["hit_lines"].startswith("Mod: ⭐ Hit kalıbı · Yaklaşma (orman yangını)\n"
                                                     "Sürüm: v6 (ateş yolda yok, araç garaj yolunda)\nCoğrafya: R"))
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
