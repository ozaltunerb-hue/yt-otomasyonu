# 16 Kas 2026, Bahadır: ateş hortumu "⭐ Hit kopyası" modu (core/hit_prompts.py HIT_KOPYA_ATES).
# Sebep: Yaklaşma modundan çıkan video (Portekiz, 16 Kas paylaşımı) zayıf kaldı. En iyi ateş hortumu (6 Kas paylaşımı,
# 5 Kas 00:13 üretimi, T4+U11, çatı terası) hit'in Kie prompt'u kelimesi kelimesine kopyalanarak kullanılır. GPT yok.
# 26 Kas 2026 (v3): 6 Kas hiti (370 bin) yeniden temel. YALNIZ üç değişiklik: (a) "into a residential area of
# {coğrafya},", (b) "Neighbors flee down the street below as cars speed away past them.", (c) "people and cars
# fleeing below". Coğrafya menüsü H1-H5 + 🎲 Rastgele, araç her zaman pickup truck. v2 (17 Kas) ve v1 (16 Kas) pasif.
# Diğer olaylar ve modlar birebir aynı (40 tohum). Ağ yok.
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
import prompt_snapshot as ps   # noqa: E402

FT = "Fire tornado tears across a burning roadside"
DOMAIN = "fire_disasters"
HK = hp.HIT_KOPYA_ATES
# 5 Kas 00:13 üretiminin (6 Kas paylaşımı, 370 bin) Kie prompt'u, birebir (Notion üretim kaydı
# 40ed048d-625e-81db-a114-c29e14ecd258 "Prompt" alanı; 26 Kas'ta yeniden karşılaştırıldı: aynı, 175 kelime)
HIT_PROMPT = (
    "0-4s: A colossal spinning fire tornado, a twisting funnel several times taller than the houses and "
    "trees, tears out of a burning forest into a residential area, its wide base engulfing the houses. Two "
    "people run away in the street below. 4-9s: The pickup truck is shoved sideways as the huge base of the "
    "fire tornado sweeps past right behind it. 9-15s: A wooden garage beside a house across the street bursts"
    " apart, burning boards spiraling up. Handheld footage filmed on a rooftop terrace above a wooded "
    "residential area, high vantage, the tornado filling half the frame, top never cut off, two or three "
    "people fleeing below; slight hand shake, the camera stays fixed, an empty foreground; one continuous "
    "shot, no zoom, no cuts, no person or face close to the camera. Civilians in everyday clothes, no hazmat "
    "suits, never CGI. A rotating funnel of flame with orbiting debris, never a straight plume or explosion. "
    "Everything moves in real time, never in slow motion, people run at full speed. No readable signs, text "
    "or flags.")
# v3'ün üç değişikliği (hit metni → yeni metin)
CHANGE_A = ("into a residential area,", "into a residential area of {place},")
CHANGE_B = ("Two people run away in the street below.",
            "Neighbors flee down the street below as cars speed away past them.")
CHANGE_C = ("two or three people fleeing below", "people and cars fleeing below")
# Kilitler (bayt bayt)
ANGLE_1 = ("Handheld footage filmed on a rooftop terrace above a wooded residential area, high vantage, the tornado "
           "filling half the frame, top never cut off,")
ANGLE_2 = ("; slight hand shake, the camera stays fixed, an empty foreground; one continuous shot, no zoom, no cuts, "
           "no person or face close to the camera.")
TORNADO_1 = ("A colossal spinning fire tornado, a twisting funnel several times taller than the houses and trees, "
             "tears out of a burning forest")
TORNADO_2 = "A rotating funnel of flame with orbiting debris, never a straight plume or explosion."
PLACES = {"H1": "British Columbia", "H2": "the Australian bush", "H3": "central Portugal", "H4": "Greece",
          "H5": "southern Chile"}
NAMES = {"H1": "Britanya Kolumbiyası", "H2": "Avustralya çalılığı", "H3": "Orta Portekiz", "H4": "Yunanistan",
         "H5": "Güney Şili"}
TAIL = HIT_PROMPT[HIT_PROMPT.index("Handheld footage"):].replace(*CHANGE_C)
REQUIRED = ("several times taller than the houses", "the tornado filling half the frame", "rooftop terrace",
            "never CGI", CHANGE_B[1], CHANGE_C[1])
FORBIDDEN = ("pans to follow", "Full action", "Until the last frame", "approaches from", "in the distance",
             "Two people", "two or three people")
SOURCE = "Kaynak: 5 Kas 00:13 üretimi (6 Kas paylaşımı), birebir"
VERSION_LINE = ("Sürüm: ateş hortumu hit kopyası (6 Kas hit birebir + kalabalık/kaçan arabalar + coğrafya "
                "menüsü)")
WARNING = ("⚠️ Hit karşılaştırması: hortum ilk kareden kadrajın yarısını dolduruyor mu, tepesi kesilmiyor mu, kamera "
           "terasta sabit mi, sokakta kalabalık ve kaçan arabalar var mı?")
# Kullanıcı hesabı (26 Kas): en uzun H2 182 / 1071
LIMITS = {"H1": (181, 1068), "H2": (182, 1071), "H3": (181, 1068), "H4": (180, 1058), "H5": (181, 1066)}
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "ates_hortumu_hit_runs_40.json")   # v3 canlı, 40 tohum (🎲)
FIXTURE_V2 = os.path.join(ROOT, "tests", "fixtures", "hit_kopya_ates_v2_runs_40.json")   # v2 (a4d9673), pasif
# v2 (17 Kas) pasif kayıt
PLACES_V2 = {"G1": ("Kanada", "a Canadian lakeside town"), "G2": ("Avustralya", "an Australian bush town"),
             "G3": ("Portekiz", "a Portuguese hillside village"), "G4": ("ABD", "a Californian suburb"),
             "G5": ("Yunanistan", "a Greek coastal town"), "G6": ("Şili", "a Chilean hillside town")}
VEHICLES_V2 = ("pickup truck", "SUV", "delivery van")
ADD_OPENING_V2 = "racing fast across the neighborhood,"
ADD_TAIL_V2 = "The fire tornado keeps moving fast the whole time, never standing still."
REQUIRED_V2 = ("several times taller than the houses", "the tornado filling half the frame", "rooftop terrace",
               "never CGI", "racing fast across the neighborhood", "never standing still")
# Değişiklikten önceki kod (20124a8): 19 olay (normal yol) + 13 mod + 🌀 Kasırga, 40 tohum
OTHERS_SHA256 = "13591326765059ef0be36cf9b9b75e1ae182c42f21a17c74b61871b99fab17be"


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
    return asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": FT, "hit_kopya_ates": True,
                                                     "used_combos": [], "recent_topics": [], **extra}))


def build(seed: int, **extra) -> dict:
    reset()
    random.seed(seed)
    return gen(**extra)


def expected(g: str) -> str:
    """Hit prompt'unun kendisinden, yalnız üç değişiklikle."""
    out = HIT_PROMPT
    for old, new in (CHANGE_A, CHANGE_B, CHANGE_C):
        assert out.count(old) == 1, old
        out = out.replace(old, new.format(place=PLACES[g]), 1)
    return out


def undo(prompt: str, g: str) -> str:
    """Coğrafya çıkarılır ve üç değişiklik geri alınır: sonuç hit prompt'u olmalı."""
    out = prompt
    for old, new in (CHANGE_A, CHANGE_B, CHANGE_C):
        new = new.format(place=PLACES[g])
        assert out.count(new) == 1, new
        out = out.replace(new, old, 1)
    return out


def v3_snapshot() -> dict:
    """40 tohum (🎲 Rastgele): prompt, hikâye, stil eki, combo, eksenler (caption hariç)."""
    runs = {}
    for s in range(1, 41):
        with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT"))):
            d = build(s)
        sc = d["scenes"][0]
        axes = json.loads(d["axes_json"])
        axes.pop("caption", None)
        runs[str(s)] = {"prompt": sc["prompt"], "story": sc["story"], "suffix": sc["style_suffix"],
                        "combo": d["combo_key"], "axes": axes}
    return runs


def others_snapshot() -> dict:
    import test_kasirga as tk
    snap = tk.others_snapshot()
    # 21 Kas (2): 🌀 Kasırga v2 bilerek değişti (açılış + F2). Bu kilit diğer olay/modlar içindir; kasırga kaydı v1
    # (35411fc) fixture'ından gelir (tk.KASIRGA_V1_SHA256), canlı v2 test_kasirga KASIRGA_SHA256 ile kilitli.
    with open(tk.FIXTURE_V1, encoding="utf-8") as fh:
        snap["modes"]["kasirga"] = json.load(fh)
    return snap


def snapshot_hash(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


class TestPassiveVersions(_Quiet):
    def test_v2_passive(self):
        """17 Kas v2 (a4d9673) HIT_KOPYA_ATES_V2 pasif kayıtta: şablon, coğrafya, araç, zorunlu liste aynen; 40 tohum
        kaydı (fixture) bu şablondan birebir kurulur."""
        v2 = hp.HIT_KOPYA_PASIF["HIT_KOPYA_ATES_V2"]
        self.assertIs(v2, hp.HIT_KOPYA_ATES_V2)
        self.assertIsNot(v2, HK)
        self.assertEqual({g: (x["name"], x["place"]) for g, x in v2["geos"].items()}, PLACES_V2)
        self.assertEqual(v2["vehicles"], VEHICLES_V2)
        self.assertEqual(v2["required"], REQUIRED_V2)
        self.assertEqual((v2["geo_block"], v2["geo_seed"], v2["vehicle_block"]), (3, ("G3",), 2))
        t = v2["template"]
        self.assertEqual(t.replace(" of {place}", "", 1).replace("{vehicle}", "pickup truck")
                         .replace(" " + ADD_OPENING_V2, "", 1).replace(" " + ADD_TAIL_V2, "", 1), HIT_PROMPT)
        with open(FIXTURE_V2, encoding="utf-8") as fh:
            runs = json.load(fh)
        self.assertEqual(len(runs), 40)
        for s, r in runs.items():
            g, v = r["axes"]["axes"]["cografya"], r["axes"]["axes"]["arac"]
            self.assertEqual(r["prompt"], t.format(place=PLACES_V2[g][1], vehicle=v), s)
            self.assertEqual(r["axes"]["axes"]["mod"], "hit_kopya_ates")

    def test_v1_passive(self):
        v1 = hp.HIT_KOPYA_PASIF["HIT_KOPYA_ATES_V1"]
        self.assertIs(v1, hp.HIT_KOPYA_ATES_V1)
        self.assertEqual(v1["template"].replace(" of {place}", "", 1).replace("{vehicle}", "pickup truck"), HIT_PROMPT)
        self.assertEqual(v1["tail_start"], HK["tail_start"])
        self.assertEqual(set(hp.HIT_KOPYA_PASIF), {"HIT_KOPYA_ATES_V1", "HIT_KOPYA_ATES_V2"})


class TestOthersUntouched(_Quiet):
    """Diğer 19 olay (normal yol), 13 mod ve 🌀 Kasırga: 40 tohum prompt / hikâye / stil eki / combo / eksenler birebir
    (önceki kod 20124a8)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.snap = others_snapshot()

    def test_other_prompts_verbatim_40_seeds(self):
        self.assertEqual(len(self.snap["events"]), 19)
        self.assertEqual(len(self.snap["modes"]), 14)
        for name, runs in self.snap["modes"].items():
            for s, r in runs.items():
                self.assertNotIn("error", r, (name, s))
        self.assertEqual(snapshot_hash(self.snap), OTHERS_SHA256)

    def test_locked_events_hash_file(self):
        import locked_prompts as lp
        self.assertEqual(lp.hashes(), lp.load())


if __name__ == "__main__":
    unittest.main()
