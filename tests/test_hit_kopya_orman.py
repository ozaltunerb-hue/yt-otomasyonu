# 20 Kas 2026, Bahadır: orman yangını "⭐ Hit kopyası" modu (core/hit_prompts.py HIT_KOPYA_ORMAN).
# Sebep: orman Yaklaşma v4-v7 testlerinin hiçbiri paylaşılabilir çıkmadı. Kaynak: 9 Eki 2026 21:52 üretimi (19 Eki
# paylaşımı), Kie prompt'u HIT_PROMPTS[es.WILDFIRE]["prompt"] (Notion 3f4d048d-625e-81f9-a10f-eaf888802f52, değişmez).
# v1 (7df29b5): hit prompt'u kelimesi kelimesine, yalnız coğrafya + araç; artık pasif (HIT_KOPYA_ORMAN_V1, 40 tohum
# kaydı fixtures/hit_kopya_orman_v1_runs_40.json, HIT_KOPYA_ORMAN_V1_SHA256).
# v2 (20 Kas): v1 testi (G6 Şili, SUV) zayıf çıktı. Hit iskeleti ve dili kalır; U dönüşü ve ağaç tepeleri çıktı; 6-8
# kişi; düşen adam + önüne devrilen yanan ağaç / direk (O1/O2 dönüşümlü); final balkonun dibindeki çatı çöker.
# Coğrafya son 3 (G4 tohum), araç son 2, engel son 1 (yalnız v2 kayıtları), kişi rastgele. GPT yok. Orman Yaklaşma v7,
# ateş hortumu Hit kopyası ve diğer 19 olay / tüm modlar birebir aynı (40 tohum). Ağ yok.
# v3 (21 Kas): v2 testinde kamera sürekli döndü, korkuluk önce yoktu sonra şekil değiştirdi. Tek değişiklik: "the
# camera pans to follow the wall of flames" yerine kamera sokağa sabit + koyu metal korkuluk kadrajın altında sabit.
# v2 pasif (HIT_KOPYA_ORMAN_V2, 40 tohum kaydı fixtures/hit_kopya_orman_v2_runs_40.json, HIT_KOPYA_ORMAN_V2_SHA256).
# Engel LRU'su v2 + v3 kayıtlarını sayar.
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

WF = es.WILDFIRE
FT = es.FIRE_TORNADO
DOMAIN = "fire_disasters"
HKO = hp.HIT_KOPYA_ORMAN
# 9 Eki 21:52 üretiminin (19 Eki paylaşımı) Kie prompt'u, birebir (Notion üretim kaydı "Prompt" alanı)
HIT_PROMPT = (
    "0-4s: A towering wall of flames sweeps down the forested slope and slams into the edge of the "
    "neighborhood, igniting roofs and trees. Five people run desperately, scattering in various directions to "
    "escape the rapidly encroaching inferno. 4-9s: The white van accelerates, executing a sharp U-turn and "
    "leaves the scene, just as the flames close in behind. 9-15s: The advancing fire consumes an entire line "
    "of trees, their tops exploding into fiery embers, rising into the swirling sky. Handheld footage shot by "
    "a person standing on a balcony of a hillside house overlooking the street and the burning slope, eye "
    "level, normal lens; slight hand shake, the camera pans to follow the wall of flames; no zoom, no cuts. "
    "Bystanders wear civilian clothes, never hi-vis PPE on civilians; emergency responders wear service "
    "uniforms. Raw natural light matching the weather, never glossy or CGI; no white hazmat suits. No "
    "readable signs, text or flags.")

# ── v2 (pasif, 892fdf9; Bahadır'ın metni, birebir) ──
TEMPLATE_V2 = (
    "0-4s: A towering wall of flames sweeps down the forested slope and slams into the edge of the neighborhood, "
    "igniting roofs and trees. {people} people run desperately up the street toward the camera, scattering to escape "
    "the rapidly encroaching inferno, as {vehicle} speeds past them. 4-9s: One man trips and falls on the road; right "
    "in front of him a {obstacle} crashes down in a burst of sparks, and he scrambles up and keeps running. 9-15s: The "
    "flames reach the house right below the balcony and its roof caves in, a fountain of sparks bursting up toward "
    "the camera. Handheld footage shot by a person standing on a balcony of a hillside house in {place} overlooking "
    "the street and the burning slope, eye level, normal lens; slight hand shake, the camera pans to follow the wall "
    "of flames; no zoom, no cuts. Bystanders wear civilian clothes, never hi-vis PPE on civilians; emergency "
    "responders wear service uniforms. Raw natural light matching the weather, never glossy or CGI; no white hazmat "
    "suits. No readable signs, text or flags.")
# ── v3 (21 Kas, Bahadır): yalnız kamera parçası değişir ──
CAMERA_OLD = "slight hand shake, the camera pans to follow the wall of flames; no zoom, no cuts."
CAMERA_NEW = ("slight hand shake, the camera stays fixed on the street; a dark metal balcony railing stays fixed at the "
              "bottom of the frame the whole time; no zoom, no cuts.")
TEMPLATE = (
    "0-4s: A towering wall of flames sweeps down the forested slope and slams into the edge of the neighborhood, "
    "igniting roofs and trees. {people} people run desperately up the street toward the camera, scattering to escape "
    "the rapidly encroaching inferno, as {vehicle} speeds past them. 4-9s: One man trips and falls on the road; right "
    "in front of him a {obstacle} crashes down in a burst of sparks, and he scrambles up and keeps running. 9-15s: The "
    "flames reach the house right below the balcony and its roof caves in, a fountain of sparks bursting up toward "
    "the camera. Handheld footage shot by a person standing on a balcony of a hillside house in {place} overlooking "
    "the street and the burning slope, eye level, normal lens; slight hand shake, the camera stays fixed on the "
    "street; a dark metal balcony railing stays fixed at the bottom of the frame the whole time; no zoom, no cuts. "
    "Bystanders wear civilian clothes, never hi-vis PPE on civilians; emergency responders wear service uniforms. Raw "
    "natural light matching the weather, never glossy or CGI; no white hazmat suits. No readable signs, text or "
    "flags.")
TAIL_START = "Handheld footage shot by a person standing on a balcony"
PLACES = {"G1": ("Kaliforniya", "a Californian suburb"), "G2": ("Avustralya", "an Australian bush town"),
          "G3": ("Yunanistan", "a Greek village"), "G4": ("Kanada", "a Canadian mountain town"),
          "G5": ("Portekiz", "a Portuguese village"), "G6": ("Şili", "a Chilean town")}
VEHICLES = ("white van", "pickup truck", "SUV")
VEHICLE_PHRASES = {"white van": "a white van", "pickup truck": "a pickup truck", "SUV": "an SUV"}
OBSTACLES = {"O1": "burning tree", "O2": "burning power pole"}
OBSTACLE_NAMES = {"O1": "yanan ağaç", "O2": "yanan direk"}
PEOPLE = {6: "Six", 7: "Seven", 8: "Eight"}
REQUIRED_V2 = ("sweeps down the forested slope and slams into the edge of the neighborhood",
               "run desperately up the street toward the camera", "trips and falls", "right in front of him",
               "scrambles up and keeps running", "its roof caves in", "the camera pans to follow the wall of flames",
               "never glossy or CGI")
FORBIDDEN_V2 = ("U-turn", "their tops exploding", "Full action", "Until the last frame", "big in frame",
                "From the very first frame", "the edge of a", "the edge of an", "onto him", "on top of him")
REQUIRED = ("sweeps down the forested slope and slams into the edge of the neighborhood",
            "run desperately up the street toward the camera", "trips and falls", "right in front of him",
            "scrambles up and keeps running", "its roof caves in", "the camera stays fixed on the street",
            "railing stays fixed at the bottom of the frame", "never glossy or CGI")
FORBIDDEN = FORBIDDEN_V2 + ("pans to follow",)
SOURCE = "Kaynak: 9 Eki 21:52 üretimi (19 Eki paylaşımı, 5,4M), iskelet ve dil"
VERSION_LINE_V2 = "Sürüm: v2 (6-8 kişi, düşen adam + ağaç/direk, çatı çöker)"
VERSION_LINE = "Sürüm: v3 (sabit kamera, sabit korkuluk)"
CAMERA_LINE = "Kamera: sabit kamera (sokağa sabit), korkuluk kadrajın altında"
WARNING_V2 = ("⚠️ Hit karşılaştırması: alev duvarı ilk saniyelerde mahalleye çarpıyor mu, düşen adam ve önüne devrilen "
              "ağaç/direk yakın ve net mi, çatı çöküyor mu?")
WARNING = WARNING_V2[:-1] + ", korkuluk baştan sona aynı yerde ve aynı şekilde mi?"
CONFIRM_DESC = ("9 Eki orman hit'inin (19 Eki paylaşımı, 5,4M) iskeleti ve dili; zayıf betler çıkarıldı. Alev duvarı "
                "yamaçtan inip mahalleye çarpar, 6-8 kişi kameraya doğru kaçar, yanlarından bir araç hızla geçer; kaçan "
                "bir adam düşer, hemen önüne yanan ağaç ya da yanan elektrik direği (dönüşümlü) devrilir, adam kalkıp "
                "kaçmaya devam eder; final: balkonun dibindeki evin çatısı çöker. Coğrafya (G1-G6) ve araç değişir. "
                "Hikâye için GPT çağrılmaz.")
REPEAT = "Tekrar önleme: coğrafya son 3, G4 tohum · araç son 2 · engel son 1 · kişi rastgele 6-8"

# ── v1 (pasif, 7df29b5) ──
PLACES_V1 = {"G1": ("Kaliforniya", "a Californian hillside suburb"), "G2": ("Avustralya", "an Australian bush town"),
             "G3": ("Yunanistan", "a Greek hillside village"), "G4": ("Kanada", "a Canadian mountain town"),
             "G5": ("Portekiz", "a Portuguese hillside village"), "G6": ("Şili", "a Chilean hillside town")}
TAIL_V1 = HIT_PROMPT[HIT_PROMPT.index(TAIL_START):]
REQUIRED_V1 = ("sweeps down the forested slope and slams into the edge of", "rapidly encroaching inferno",
               "sharp U-turn", "the camera pans to follow the wall of flames", "never glossy or CGI")
FORBIDDEN_V1 = ("Full action", "Until the last frame", "big in frame", "From the very first frame",
                "never along the asphalt")
SOURCE_V1 = "Kaynak: 9 Eki 21:52 üretimi (19 Eki paylaşımı, 3M), birebir"
WARNING_V1 = ("⚠️ Hit karşılaştırması: alev duvarı ilk saniyelerde yamaçtan inip mahalleye çarpıyor mu, video 19 Eki "
              "hit'iyle boy ölçüşür mü?")
CONFIRM_DESC_V1 = ("9 Eki 21:52 üretiminin (19 Eki paylaşımı, 3M) Kie prompt'u kelimesi kelimesine; sadece coğrafya "
                   "(G1-G6) ve araç değişir. Alev duvarı ormanlık yamaçtan inip mahalleye çarpar, insanlar kaçar, araç "
                   "U dönüşü yapıp kaçar, ağaç sırası tepeden kıvılcım saçarak yanar. Yamaç evinin balkonu, kamera "
                   "alevleri takip eder. Hikâye için GPT çağrılmaz.")
V1_FIXTURE = os.path.join(ROOT, "tests", "fixtures", "hit_kopya_orman_v1_runs_40.json")
V2_FIXTURE = os.path.join(ROOT, "tests", "fixtures", "hit_kopya_orman_v2_runs_40.json")

# Değişiklikten önceki kod (14063ac): test_yer_yarilmasi kaydı (19 olay + modlar, orman v3 fixture'ı) + 🌍 Yer
# yarılması, 40 tohum. Canlı orman Yaklaşma v7 ayrıca ORMAN_SHA256 ile.
OTHERS_SHA256 = "d719e05d8370ca2d526710ba8814f6860a6d320ffdd3076908fcd36ad76c49f2"
ORMAN_SHA256 = "b3ecda2ac3cb673b68ffb22c1024d978057d64419e993b720e825684c0541fc5"   # orman Yaklaşma v7 (değişmez)
# ⭐ Hit kopyası (orman yangını) 40 tohum kilidi (prompt / hikâye / stil eki / combo / eksenler; caption hariç)
HIT_KOPYA_ORMAN_V1_SHA256 = "f0e9e1576c0142bf102813c3f8e1bccfe0104c71defb61242a3170397d5e4d35"   # v1 (fixture)
HIT_KOPYA_ORMAN_V2_SHA256 = "0ec2bad2481274d595bef3a570ac64df3e2f26cac46d7c1a924d7f545df20959"   # v2 (fixture)
HIT_KOPYA_ORMAN_SHA256 = "d8064175fddf17d86b8114e049659e88bc0d6c175cb6a059486262c7afd9f0fe"   # v3


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
    return asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": WF, "hit_kopya_orman": True,
                                                     "used_combos": [], "recent_topics": [], **extra}))


def build(seed: int) -> dict:
    reset()
    random.seed(seed)
    return gen()


def expected(g: str, v: str, o: str, n: int, template: str = TEMPLATE) -> str:
    """Bahadır'ın metninden (v3 TEMPLATE; v2 için TEMPLATE_V2) bağımsız kurulum."""
    return template.format(people=PEOPLE[n], vehicle=VEHICLE_PHRASES[v], obstacle=OBSTACLES[o], place=PLACES[g][1])


def expected_v1(g: str, v: str) -> str:
    """v1: hit prompt'unun kendisinden, "the edge of the neighborhood" → yer, "The white van" → araç."""
    return HIT_PROMPT.replace("the edge of the neighborhood,", f"the edge of {PLACES_V1[g][1]},", 1) \
                     .replace("The white van accelerates", f"The {v} accelerates", 1)


def combos():
    return [(g, v, o, n) for g in PLACES for v in VEHICLES for o in OBSTACLES for n in PEOPLE]


def snapshot_hash(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def others_snapshot() -> dict:
    """test_yer_yarilmasi kaydı (19 olay + modlar + ⭐ Hit kopyası (ateş hortumu)) + 🌍 Yer yarılması; 40 tohum."""
    import test_yer_yarilmasi as ty
    snap = ty.others_snapshot()
    snap["modes"]["yer_yarilmasi"] = ty.yy_snapshot()
    return snap


def hko_snapshot() -> dict:
    """⭐ Hit kopyası (orman yangını) 40 tohum: prompt, hikâye, stil eki, combo, eksenler (caption hariç)."""
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


class TestV1Passive(_Quiet):
    """v1 (7df29b5) pasif: şablon, listeler, metinler _V1 sabitlerinde aynen; 40 tohum kaydı fixture + V1 SHA."""

    def test_v1_template_is_hit_prompt_verbatim(self):
        self.assertEqual(hp.HIT_PROMPTS[WF]["prompt"], HIT_PROMPT)   # kaynak kayıt değişmez
        self.assertEqual(hp.HIT_PROMPTS[WF]["notion"], "3f4d048d-625e-81f9-a10f-eaf888802f52")
        v1 = hp.HIT_KOPYA_ORMAN_V1
        self.assertIsNot(v1, HKO)
        t = v1["template"]
        self.assertEqual(t.format(place="the neighborhood", vehicle="white van"), HIT_PROMPT)
        self.assertEqual(v1["tail_start"], TAIL_START)
        self.assertEqual({g: (x["name"], x["place"]) for g, x in v1["geos"].items()}, PLACES_V1)
        self.assertEqual(v1["vehicles"], VEHICLES)
        self.assertEqual(hp.HIT_KOPYA_ORMAN_REQUIRED_V1, REQUIRED_V1)
        self.assertEqual(hp.HIT_KOPYA_ORMAN_FORBIDDEN_V1, FORBIDDEN_V1)
        self.assertEqual(hp.HIT_KOPYA_ORMAN_WARNING_V1, WARNING_V1)
        self.assertEqual(hp.HIT_KOPYA_ORMAN_CONFIRM_DESC_V1, CONFIRM_DESC_V1)
        self.assertEqual(hp.HIT_KOPYA_ORMAN_SOURCE_V1, SOURCE_V1)

    def test_v1_all_18_combos(self):
        t = hp.HIT_KOPYA_ORMAN_V1["template"]
        words, chars = [], []
        for g in PLACES_V1:
            for v in VEHICLES:
                p = t.format(place=PLACES_V1[g][1], vehicle=v)
                self.assertEqual(p, expected_v1(g, v))
                self.assertTrue(p.endswith(TAIL_V1))
                words.append(len(p.split()))
                chars.append((len(p), g, v))
        self.assertEqual((min(words), max(words)), (154, 155))
        self.assertEqual(min(chars), (941, "G2", "SUV"))
        self.assertEqual(max(chars), (956, "G5", "pickup truck"))

    def test_v1_fixture_lock(self):
        with open(V1_FIXTURE, encoding="utf-8") as f:
            runs = json.load(f)
        self.assertEqual(len(runs), 40)
        self.assertEqual(snapshot_hash(runs), HIT_KOPYA_ORMAN_V1_SHA256)
        for s, r in runs.items():
            ax = r["axes"]["axes"]
            self.assertEqual(r["prompt"], expected_v1(ax["cografya"], ax["arac"]), s)
            self.assertEqual(r["suffix"], TAIL_V1)
            self.assertNotIn("surum", ax)
            self.assertEqual(ax["mod"], "hit_kopya_orman")


class TestV2Passive(_Quiet):
    """v2 (892fdf9) pasif: şablon, listeler, metinler _V2 sabitlerinde aynen; 40 tohum kaydı fixture + V2 SHA."""

    def test_v2_constants_verbatim(self):
        v2 = hp.HIT_KOPYA_ORMAN_V2
        self.assertIsNot(v2, HKO)
        self.assertEqual(v2["template"], TEMPLATE_V2)
        self.assertEqual(v2["tail_start"], TAIL_START)
        self.assertEqual({g: (x["name"], x["place"]) for g, x in v2["geos"].items()}, PLACES)
        self.assertEqual(v2["vehicles"], ("a white van", "a pickup truck", "an SUV"))
        self.assertEqual(v2["obstacles"], OBSTACLES)
        self.assertEqual(v2["people"], ("Six", "Seven", "Eight"))
        self.assertEqual(hp.HIT_KOPYA_ORMAN_REQUIRED_V2, REQUIRED_V2)
        self.assertEqual(hp.HIT_KOPYA_ORMAN_FORBIDDEN_V2, FORBIDDEN_V2)
        self.assertEqual(hp.HIT_KOPYA_ORMAN_WARNING_V2, WARNING_V2)
        self.assertEqual(hp.HIT_KOPYA_ORMAN_VERSION_LINE_V2, VERSION_LINE_V2)
        self.assertEqual(hp.HIT_KOPYA_ORMAN_SURUM_V2, "v2")
        self.assertEqual(hp.HIT_KOPYA_ORMAN_CAMERA_V2, "hit kamerası (the camera pans to follow the wall of flames); "
                                                       "balcony of a hillside house, eye level, normal lens")
        self.assertEqual(hp.HIT_KOPYA_ORMAN_CAMERA_AXIS_V2, "elde, alevleri takip (hit)")
        self.assertEqual(hp.HIT_KOPYA_ORMAN_SPOT_LABEL_V2, "Balcony of a hillside house (hit kopyası v2)")

    def test_v2_all_108_combos(self):
        t = hp.HIT_KOPYA_ORMAN_V2["template"]
        words, chars = [], []
        for g, v, o, n in combos():
            p = t.format(people=PEOPLE[n], vehicle=VEHICLE_PHRASES[v], obstacle=OBSTACLES[o], place=PLACES[g][1])
            self.assertEqual(p, expected(g, v, o, n, TEMPLATE_V2))
            words.append(len(p.split()))
            chars.append(len(p))
        self.assertEqual(len(words), 108)
        self.assertEqual((min(words), max(words)), (180, 183))
        self.assertEqual((min(chars), max(chars)), (1036, 1062))

    def test_v2_fixture_lock(self):
        with open(V2_FIXTURE, encoding="utf-8") as f:
            runs = json.load(f)
        self.assertEqual(len(runs), 40)
        self.assertEqual(snapshot_hash(runs), HIT_KOPYA_ORMAN_V2_SHA256)
        for s, r in runs.items():
            ax = r["axes"]["axes"]
            self.assertEqual(r["prompt"], expected(ax["cografya"], ax["arac"], ax["engel"], ax["kisi"], TEMPLATE_V2), s)
            self.assertIn("the camera pans to follow the wall of flames", r["suffix"])
            self.assertEqual((ax["mod"], ax["surum"]), ("hit_kopya_orman", "v2"))
            self.assertTrue(r["combo"].endswith(f"##HKO:{ax['cografya']}|bystander_handheld"), s)


class TestTemplate(_Quiet):
    def test_single_change_from_v2(self):
        """v3 = v2 şablonu, yalnız kamera parçası değişmiş (tek yer, birebir)."""
        self.assertEqual(TEMPLATE_V2.count(CAMERA_OLD), 1)
        self.assertEqual(TEMPLATE, TEMPLATE_V2.replace(CAMERA_OLD, CAMERA_NEW))
        self.assertEqual(HKO["template"], hp.HIT_KOPYA_ORMAN_V2["template"].replace(CAMERA_OLD, CAMERA_NEW))
        self.assertEqual((hp.HIT_KOPYA_ORMAN_CAMERA_OLD_V2, hp.HIT_KOPYA_ORMAN_CAMERA_NEW), (CAMERA_OLD, CAMERA_NEW))
        self.assertEqual(HKO["template"].count(CAMERA_NEW), 1)
        self.assertNotIn("pans", HKO["template"])
        story_v2, story_v3 = (t[:t.index(" " + TAIL_START)] for t in (TEMPLATE_V2, HKO["template"]))
        self.assertEqual(story_v3, story_v2)   # hikâye aynen
        for key in ("geos", "vehicles", "obstacles", "people", "tail_start"):
            self.assertEqual(HKO[key], hp.HIT_KOPYA_ORMAN_V2[key], key)
        for g, v, o, n in (("G1", "SUV", "O1", 8), ("G5", "white van", "O2", 7)):
            self.assertEqual(hp.hit_kopya_orman_story(g, v, o, n), expected(g, v, o, n, TEMPLATE_V2).split(
                " " + TAIL_START)[0])

    def test_template_verbatim(self):
        """Şablon = Bahadır'ın v3 metni (v2 + sabit kamera + sabit korkuluk), tek karakter farksız."""
        self.assertEqual(HKO["template"], TEMPLATE)
        self.assertEqual(HKO["tail_start"], TAIL_START)
        for ph in ("{people}", "{vehicle}", "{obstacle}", "{place}"):
            self.assertEqual(TEMPLATE.count(ph), 1, ph)
        self.assertGreater(TEMPLATE.index("{place}"), TEMPLATE.index(TAIL_START))   # yer stil ekinde
        for g, v, o, n in (("G1", "SUV", "O1", 6), ("G6", "white van", "O2", 8)):
            p = hp.hit_kopya_orman_prompt(g, v, o, n)
            self.assertEqual(p, hp.hit_kopya_orman_story(g, v, o, n) + " " + hp.hit_kopya_orman_tail(g))
            self.assertTrue(hp.hit_kopya_orman_tail(g).startswith(TAIL_START))

    def test_constants(self):
        self.assertEqual(hp.HIT_KOPYA_ORMAN_MODE_LABEL, "⭐ Hit kopyası (orman yangını)")
        self.assertEqual(hp.HIT_KOPYA_ORMAN_EVENTS, (WF,))
        self.assertEqual(hp.HIT_KOPYA_ORMAN_DOMAIN, DOMAIN)
        self.assertEqual(hp.HIT_KOPYA_ORMAN_MOD, "hit_kopya_orman")
        self.assertEqual(hp.HIT_KOPYA_ORMAN_SURUM, "v3")
        self.assertEqual(hp.HIT_KOPYA_ORMAN_OBSTACLE_SURUMS, ("v2", "v3"))
        self.assertEqual(hp.HIT_KOPYA_ORMAN_CAMERA, CAMERA_LINE[len("Kamera: "):])
        self.assertEqual(hp.HIT_KOPYA_ORMAN_CAMERA_AXIS, "sabit (sokağa sabit), korkuluk altta")
        self.assertEqual(hp.HIT_KOPYA_ORMAN_SPOT_LABEL, "Balcony of a hillside house (hit kopyası v3)")
        self.assertEqual(hp.HIT_KOPYA_ORMAN_SOURCE, SOURCE)
        self.assertEqual(hp.HIT_KOPYA_ORMAN_VERSION_LINE, VERSION_LINE)
        self.assertEqual((hp.HIT_KOPYA_ORMAN_MAX_WORDS, hp.HIT_KOPYA_ORMAN_MAX_CHARS), (230, 1400))
        self.assertEqual((hp.HIT_KOPYA_ORMAN_GEO_BLOCK, hp.HIT_KOPYA_ORMAN_GEO_SEED, hp.HIT_KOPYA_ORMAN_VEHICLE_BLOCK,
                          hp.HIT_KOPYA_ORMAN_OBSTACLE_BLOCK), (3, ("G4",), 2, 1))
        self.assertEqual({g: (v["name"], v["place"]) for g, v in HKO["geos"].items()}, PLACES)
        self.assertEqual(HKO["vehicles"], ("a white van", "a pickup truck", "an SUV"))
        self.assertEqual(hp.hit_kopya_orman_vehicle_names(), list(VEHICLES))
        self.assertEqual(HKO["obstacles"], OBSTACLES)
        self.assertEqual(hp.HIT_KOPYA_ORMAN_OBSTACLE_NAMES, OBSTACLE_NAMES)
        self.assertEqual(HKO["people"], ("Six", "Seven", "Eight"))
        self.assertEqual(hp.HIT_KOPYA_ORMAN_REQUIRED, REQUIRED)
        self.assertEqual(hp.HIT_KOPYA_ORMAN_FORBIDDEN, FORBIDDEN)
        self.assertEqual(hp.HIT_KOPYA_ORMAN_WARNING, WARNING)
        self.assertEqual(hp.HIT_KOPYA_ORMAN_CONFIRM_DESC, CONFIRM_DESC)
        self.assertNotIn("—", CONFIRM_DESC + WARNING + SOURCE + VERSION_LINE + CAMERA_LINE)
        self.assertIn("the camera pans to follow the wall of flames", REQUIRED_V2)
        self.assertNotIn("the camera pans to follow the wall of flames", REQUIRED)
        self.assertEqual(tuple(x for x in REQUIRED_V2 if "pans" not in x),
                         tuple(x for x in REQUIRED if "stays fixed" not in x))   # diğer zorunlular aynen

    def test_all_108_combos_within_limits(self):
        words, chars = [], []
        for g, v, o, n in combos():
            p = hp.hit_kopya_orman_prompt(g, v, o, n)
            self.assertEqual(p, expected(g, v, o, n), (g, v, o, n))
            words.append(len(p.split()))
            chars.append(len(p))
            self.assertLessEqual(len(p.split()), 230)
            self.assertLessEqual(len(p), 1400)
            self.assertEqual(hp.hit_kopya_orman_camera_issues(p, g), [], (g, v, o, n))
            for bad in FORBIDDEN:
                self.assertNotIn(bad.lower(), p.lower())
        self.assertEqual(len(words), 108)
        self.assertEqual((min(words), max(words)), (194, 197))
        self.assertEqual((min(chars), max(chars)), (1112, 1138))
        longest = max(combos(), key=lambda c: (len(hp.hit_kopya_orman_prompt(*c).split()),
                                               len(hp.hit_kopya_orman_prompt(*c))))
        self.assertEqual(len(hp.hit_kopya_orman_prompt(*longest).split()), 197)
        self.assertEqual(len(hp.hit_kopya_orman_prompt("G4", "pickup truck", "O2", 8)), 1138)

    def test_articles(self):
        self.assertIn("as an SUV speeds past them", hp.hit_kopya_orman_story("G1", "SUV", "O1", 6))
        self.assertIn("as a white van speeds past them", hp.hit_kopya_orman_story("G1", "white van", "O1", 6))
        self.assertIn("as a pickup truck speeds past them", hp.hit_kopya_orman_story("G1", "pickup truck", "O1", 6))
        self.assertIn("right in front of him a burning tree crashes down",
                      hp.hit_kopya_orman_story("G1", "SUV", "O1", 7))
        self.assertIn("right in front of him a burning power pole crashes down",
                      hp.hit_kopya_orman_story("G1", "SUV", "O2", 7))
        self.assertIn(". Eight people run desperately", hp.hit_kopya_orman_story("G1", "SUV", "O2", 8))
        self.assertIn("a hillside house in an Australian bush town overlooking", hp.hit_kopya_orman_tail("G2"))
        for g, v, o, n in combos():
            p = hp.hit_kopya_orman_prompt(g, v, o, n)
            for bad in (" a SUV", " an white", " an pickup", " a an ", " a a ", " an a ", " an Californian"):
                self.assertNotIn(bad, p, (g, v, o, n))

    def test_bad_ids(self):
        for args in (("G7", "SUV", "O1", 6), ("G1", "delivery van", "O1", 6), ("G1", "an SUV", "O1", 6),
                     ("G1", "SUV", "O3", 6), ("G1", "SUV", "O1", 5), ("G1", "SUV", "O1", 9)):
            with self.assertRaises(es.StructureError, msg=args):
                hp.hit_kopya_orman_prompt(*args)

    def test_event_gate_without_synonym(self):
        """Ana hattın olay denetimi bu modda da geçer; eş anlamlı eklenmedi."""
        for g, v, o, n in combos():
            self.assertEqual(pg.event_fidelity_issues(WF, hp.hit_kopya_orman_story(g, v, o, n)), [], (g, v, o, n))
            self.assertEqual(pg.event_fidelity_issues(WF, hp.hit_kopya_orman_prompt(g, v, o, n)), [], (g, v, o, n))

    def test_ates_hit_kopya_untouched(self):
        """Ateş hortumu Hit kopyası sabitleri ayrı ve aynen."""
        self.assertIsNot(hp.HIT_KOPYA_ATES, HKO)
        self.assertEqual(hp.HIT_KOPYA_MODE_LABEL, "⭐ Hit kopyası (ateş hortumu)")
        self.assertEqual(hp.HIT_KOPYA_MOD, "hit_kopya_ates")
        self.assertEqual(hp.HIT_KOPYA_GEO_SEED, ("G3",))
        self.assertEqual(hp.HIT_KOPYA_EVENTS, (FT,))


class TestScene(_Quiet):
    def _check(self, d):
        sc, st = d["scenes"][0], d["structure"]
        tb = st["hit_kopya_orman"]
        prompt = sc["prompt"]
        self.assertIn(tb["geo"], PLACES)
        self.assertIn(tb["vehicle"], VEHICLES)
        self.assertIn(tb["obstacle"], OBSTACLES)
        self.assertIn(tb["people"], (6, 7, 8))
        self.assertEqual(prompt, expected(tb["geo"], tb["vehicle"], tb["obstacle"], tb["people"]))
        self.assertEqual(sc["style_suffix"], hp.hit_kopya_orman_tail(tb["geo"]))
        for need in REQUIRED + (PLACES[tb["geo"]][1],):
            self.assertIn(need, prompt)
        for bad in FORBIDDEN:
            self.assertNotIn(bad.lower(), prompt.lower())
        self.assertEqual(d["combo_key"], f"{DOMAIN}|none|{WF.lower()}|balcony of a hillside house##HKO:{tb['geo']}"
                                         "|bystander_handheld")
        self.assertIsNone(es.beats_of_combo(d["combo_key"]))   # normal K*/L* ve Yaklaşma M*/N* LRU'su etkilenmez
        self.assertEqual(cp.submit_issues(st, {"prompt": prompt, "story": sc["story"],
                                               "style_suffix": sc["style_suffix"]}), [])
        self.assertEqual(pg.event_fidelity_issues(WF, sc["story"]), [])
        self.assertEqual((d["selection"]["domain_id"], d["selection"]["event"]), (DOMAIN, WF))
        ax = json.loads(d["axes_json"])["axes"]
        self.assertEqual((ax["mod"], ax["surum"], ax["cografya"], ax["arac"], ax["engel"], ax["kisi"], ax["people"]),
                         ("hit_kopya_orman", "v3", tb["geo"], tb["vehicle"], tb["obstacle"], tb["people"],
                          tb["people"]))
        for other in ("hit_kopya_ates", "orman_yaklasma", "kasirga", "donma_firtina", "approach", "hit", "spec"):
            self.assertNotIn(other, st)
        return tb

    def test_40_seeds_no_error_and_no_gpt(self):
        with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT çağrıldı"))) as gpt, \
             patch.object(pg, "_get_openai_client", side_effect=AssertionError("GPT istemcisi istendi")), \
             patch.object(cp, "build_creative_scene", AsyncMock(side_effect=AssertionError("normal hat"))) as normal:
            seen, people, obs = set(), set(), set()
            for seed in range(1, 41):
                tb = self._check(build(seed))
                seen.add((tb["geo"], tb["vehicle"]))
                people.add(tb["people"])
                obs.add(tb["obstacle"])
                self.assertNotEqual(tb["geo"], "G4")   # ilk üretim: G4 tohumu
        gpt.assert_not_called()
        normal.assert_not_called()
        self.assertGreater(len(seen), 8)
        self.assertEqual(people, {6, 7, 8})
        self.assertEqual(obs, {"O1", "O2"})

    def test_lru_and_g4_seed(self):
        geos, vehs = set(), set()
        for seed in range(1, 16):
            reset()
            random.seed(seed)
            runs = [self._check(gen()) for _ in range(12)]
            g = [r["geo"] for r in runs]
            self.assertNotIn("G4", g[:3], (seed, g))   # G4 tohumu: ilk 3 üretimde G4 gelmez
            hist = ["G4"] + g
            for i in range(1, len(hist)):
                self.assertNotIn(hist[i], hist[max(0, i - 3):i], (seed, g))
            v = [r["vehicle"] for r in runs]
            for i in range(len(v)):
                self.assertNotIn(v[i], v[max(0, i - 2):i], (seed, v))
            self.assertEqual(hp._HIT_KOPYA_ORMAN_GEO_MEMORY[-12:], g)
            self.assertEqual(hp._HIT_KOPYA_ORMAN_VEHICLE_MEMORY[-12:], v)
            geos |= set(g)
            vehs |= set(v)
        self.assertEqual(geos, set(PLACES))
        self.assertEqual(vehs, set(VEHICLES))
        self.assertEqual(hp._HIT_KOPYA_GEO_MEMORY, [])   # ateş Hit kopyası hafızası etkilenmez
        self.assertEqual(hp._HIT_KOPYA_VEHICLE_MEMORY, [])

    def test_obstacle_alternates_and_people_random(self):
        """Engel son 1 elenir: ardışık 4 seçim O1/O2 sırayla. Kişi 6-8 rastgele (LRU yok, tekrar gelebilir)."""
        repeats = 0
        for seed in range(1, 21):
            reset()
            random.seed(seed)
            runs = [self._check(gen()) for _ in range(4)]
            o = [r["obstacle"] for r in runs]
            self.assertIn(o, (["O1", "O2", "O1", "O2"], ["O2", "O1", "O2", "O1"]), (seed, o))
            self.assertEqual(hp._HIT_KOPYA_ORMAN_OBSTACLE_MEMORY[-4:], o)
            n = [r["people"] for r in runs]
            self.assertTrue(set(n) <= {6, 7, 8}, n)
            repeats += sum(1 for a, b in zip(n, n[1:]) if a == b)
        self.assertGreater(repeats, 0)   # LRU yok

    def test_history_sources(self):
        def rec(g, v, event=WF, mod="hit_kopya_orman", **extra):
            return {"eksenler": json.dumps({"event": event, "axes": {"mod": mod, "cografya": g, "arac": v, **extra}})}
        # v1 kayıtları (surum yok) coğrafya/araç LRU'suna sayılır; engel yalnız v2 + v3 kayıtlarından
        recs = [rec("G1", "SUV"), {"eksenler": "x"}, rec("G2", "pickup truck", engel="O2"),
                rec("G5", "SUV", mod="orman_yaklasma", engel="O1", surum="v2"),
                rec("G6", "white van", event=FT, mod="hit_kopya_ates")]
        self.assertEqual(hp.hit_kopya_orman_axes_history(recs, "cografya"), ["G1", "G2"])
        self.assertEqual(hp.hit_kopya_orman_axes_history(recs, "arac"), ["SUV", "pickup truck"])
        self.assertEqual(hp.hit_kopya_orman_axes_history(recs, "engel", "v2"), [])   # sürümsüz kayıt sayılmaz
        self.assertIsNone(hp.hit_kopya_orman_axes_history(None, "arac"))
        v2 = recs + [rec("G3", "SUV", engel="O1", surum="v2", kisi=7)]
        self.assertEqual(hp.hit_kopya_orman_axes_history(v2, "engel", "v2"), ["O1"])
        calls = []
        obs_first = set()
        for seed in range(1, 11):
            reset()
            random.seed(seed)
            d = gen(axes_loader=lambda dom: calls.append(dom) or recs)
            tb = d["structure"]["hit_kopya_orman"]
            self.assertIn(tb["geo"], ("G3", "G5", "G6"))   # son 3 (G4 tohum, G1, G2) elenir
            self.assertEqual(tb["vehicle"], "white van")   # son 2 (SUV, pickup truck) elenir
            obs_first.add(tb["obstacle"])
            axes = json.loads(d["axes_json"])
            self.assertEqual(axes["event"], WF)
            self.assertEqual((axes["axes"]["mod"], axes["axes"]["cografya"], axes["axes"]["arac"]),
                             ("hit_kopya_orman", tb["geo"], tb["vehicle"]))
            self.assertEqual(axes["axes"]["beats"], f"HKO:{tb['geo']}")
            self.assertEqual(axes["excluded"]["cografya"], ["G1", "G2", "G4"])
            self.assertEqual(axes["excluded"]["arac"], ["pickup truck", "SUV"])
            self.assertEqual(axes["excluded"]["engel"], [])
            self.assertEqual(d["trace"]["axes_source"], "notion")
            reset()
            random.seed(seed)
            d = gen(axes_loader=lambda dom: v2)
            tb = d["structure"]["hit_kopya_orman"]
            self.assertEqual(tb["obstacle"], "O2")   # son v2 engeli O1 → O2
            self.assertIn(tb["geo"], ("G4", "G5", "G6"))   # son 3 (G1, G2, G3) elenir
            self.assertEqual(json.loads(d["axes_json"])["excluded"]["engel"], ["O1"])
        self.assertEqual(obs_first, {"O1", "O2"})   # v2 geçmişi yokken engel serbest
        # v3: engel geçmişi v2 + v3 kayıtlarından (son kayıt hangisiyse); v1/sürümsüz sayılmaz
        v3 = v2 + [rec("G1", "pickup truck", engel="O2", surum="v3", kisi=6)]
        self.assertEqual(hp.hit_kopya_orman_axes_history(v3, "engel", ("v2", "v3")), ["O1", "O2"])
        self.assertEqual(hp.hit_kopya_orman_axes_history(v3, "engel", "v3"), ["O2"])
        for seed in range(1, 6):
            reset()
            random.seed(seed)
            d = gen(axes_loader=lambda dom: v3)
            tb = d["structure"]["hit_kopya_orman"]
            self.assertEqual(tb["obstacle"], "O1")   # son engel (v3) O2 → O1
            self.assertEqual(json.loads(d["axes_json"])["axes"]["surum"], "v3")
        reset()
        random.seed(1)
        d = gen(axes_loader=lambda dom: recs + [rec("G3", "SUV", engel="O2", surum="v2", kisi=7)])
        self.assertEqual(d["structure"]["hit_kopya_orman"]["obstacle"], "O1")   # v2 son engeli O2 → O1
        self.assertEqual(set(calls), {DOMAIN})

        def broken(dom):
            raise RuntimeError("Notion yok")
        reset()
        random.seed(3)
        d = gen(axes_loader=broken)
        self.assertEqual(d["trace"]["axes_source"], "bellek")
        self._check(d)

    def test_kie_final_check_required_and_forbidden(self):
        reset()
        random.seed(5)
        d = gen()
        st, sc = d["structure"], d["scenes"][0]
        tb = st["hit_kopya_orman"]
        geo = tb["geo"]
        good = {"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"]}
        self.assertEqual(cp.submit_issues(st, good), [])
        for need in REQUIRED:
            bad = sc["prompt"].replace(need, "x")
            self.assertTrue(hp.hit_kopya_orman_camera_issues(bad, geo), need)
            self.assertTrue(cp.submit_issues(st, {**good, "prompt": bad}), need)
        self.assertTrue(hp.hit_kopya_orman_camera_issues(sc["prompt"].replace(PLACES[geo][1], "a town"), geo))
        for bad_phrase in FORBIDDEN:
            bad = sc["prompt"].replace("eye level", f"eye level, {bad_phrase.lower()}")
            self.assertTrue(hp.hit_kopya_orman_camera_issues(bad), bad_phrase)
            self.assertTrue(cp.submit_issues(st, {**good, "prompt": bad}), bad_phrase)
        other = next(g for g in PLACES if g != geo)
        self.assertTrue(hp.hit_kopya_orman_camera_issues(hp.hit_kopya_orman_prompt(other, "SUV", "O1", 6), geo))
        self.assertTrue(cp.submit_issues(st, {**good, "style_suffix": "x"}))
        self.assertTrue(cp.submit_issues(st, {**good, "story": sc["story"] + " x"}))
        swapped = {**tb, "obstacle": "O2" if tb["obstacle"] == "O1" else "O1"}
        self.assertTrue(cp.submit_issues({**st, "hit_kopya_orman": swapped}, good))
        for key, val in (("obstacle", "O3"), ("people", 5), ("vehicle", "an SUV")):
            self.assertTrue(cp.submit_issues({**st, "hit_kopya_orman": {**tb, key: val}}, good), key)
        long = sc["prompt"] + " word" * 80
        self.assertTrue(any("kelime" in x for x in hp.hit_kopya_orman_issues(st, {**good, "prompt": long})))
        self.assertEqual(asyncio.run(cp.rewrite_structured(st, "ret", AsyncMock(side_effect=AssertionError("GPT")))),
                         sc["story"])

    def test_approval_lines(self):
        reset()
        random.seed(7)
        d = gen()
        tb = d["structure"]["hit_kopya_orman"]
        lines = tb["lines"].split("\n")
        g = tb["geo"]
        self.assertEqual(lines[0], "Mod: ⭐ Hit kopyası (orman yangını)")
        self.assertEqual(lines[1], VERSION_LINE)
        self.assertEqual(lines[2], SOURCE)
        self.assertEqual(lines[3], f"Coğrafya: {g} {PLACES[g][0]} «{PLACES[g][1]}»")
        self.assertEqual(lines[4], f"Araç: {tb['vehicle']}")
        self.assertIn(tb["vehicle"], VEHICLES)   # artikelsiz
        self.assertEqual(lines[5], f"Kişi: {tb['people']}")
        self.assertEqual(lines[6], f"Engel: {tb['obstacle']} {OBSTACLE_NAMES[tb['obstacle']]}")
        p = tb["prompt"]
        self.assertEqual(lines[7], CAMERA_LINE)
        self.assertEqual(lines[8], f"Kelime: {len(p.split())} (en fazla 230) · karakter: {len(p)} (en fazla 1400)")
        self.assertTrue(lines[9].startswith("Eksenler (⭐ Hit kopyası (orman yangını)): sürüm=v3 · coğrafya="))
        self.assertIn("kamera modu=sabit (sokağa sabit), korkuluk altta", lines[9])
        self.assertNotIn("alevleri takip", tb["lines"])
        self.assertEqual(lines[10], REPEAT)
        self.assertEqual(lines[11], WARNING)
        self.assertTrue(WARNING.endswith("çatı çöküyor mu, korkuluk baştan sona aynı yerde ve aynı şekilde mi?"))
        self.assertEqual(len(lines), 12)
        self.assertNotIn("—", tb["lines"])
        tr = d["trace"]
        self.assertEqual(tr["mode_camera"], "sabit kamera (sokağa sabit), korkuluk kadrajın altında")
        self.assertEqual(tr["spot"], "Balcony of a hillside house (hit kopyası v3)")
        from core.trace_format import format_generation
        text = "\n".join(b for _, b in format_generation(tr))
        self.assertIn(CAMERA_LINE + "\n", text)


class TestPipelineAndBot(_Quiet):
    def _run(self, poll=None, approve=True):
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
                return await orig(**{**kw, "domain": DOMAIN}, hit_kopya_orman=True)
            with patch.object(main, "run_pipeline", run_with):
                r = t.run_pipe(gen=AsyncMock(side_effect=fake_gen), reporter=rep, event=WF, poll=poll)
        finally:
            t.doCleanups()
        return r, rep, seen, t

    def test_pipeline_sends_verbatim_prompt_after_approval(self):
        r, rep, seen, t = self._run()
        self.assertTrue(r["success"], r)
        self.assertIs(seen["config"]["hit_kopya_orman"], True)
        for other in ("hit_kopya_ates", "orman_yaklasma", "kasirga", "donma_firtina", "approach_env", "hit_env"):
            self.assertNotIn(other, seen["config"])
        approve = [c[1] for c in rep.calls if c[0] == "approve"]
        self.assertEqual(len(approve), 1)
        info = approve[0]
        self.assertTrue(info["hit_lines"].startswith("Mod: ⭐ Hit kopyası (orman yangını)\n" + VERSION_LINE + "\n"))
        self.assertIn(SOURCE, info["hit_lines"])
        self.assertIn(WARNING, info["hit_lines"])
        self.assertEqual(t.create.await_count, 1)
        self.assertEqual(t.create.await_args.args[1], info["prompt"])
        axes = [c.args[0] for c in t.tracker.record_axes.call_args_list]
        ax = json.loads(axes[0])["axes"]
        self.assertEqual((ax["mod"], ax["surum"]), ("hit_kopya_orman", "v3"))
        self.assertIn(CAMERA_LINE, info["hit_lines"])
        self.assertTrue(info["prompt"].endswith(hp.hit_kopya_orman_tail(ax["cografya"])))
        self.assertEqual(info["prompt"], expected(ax["cografya"], ax["arac"], ax["engel"], ax["kisi"]))

    def test_event_gate_blocks_mismatch(self):
        import main
        with patch.object(main, "event_fidelity_issues", side_effect=lambda e, t, *a: ["uyuşmuyor"]
                          if e == WF else []):
            r, _, _, t = self._run()
        self.assertFalse(r["success"])
        self.assertEqual(t.create.await_count, 0)

    def test_rejected_approval_no_kie(self):
        r, _, _, t = self._run(approve=False)
        self.assertFalse(r["success"])
        self.assertEqual(t.create.await_count, 0)

    def _ids(self, bot, event=WF):
        return str(bot.DOMAIN_KEYS.index(DOMAIN)), str(bot.domain_events(DOMAIN).index(event))

    def test_button_and_flow(self):
        import bot
        from test_tur29_infra import _context, _update
        di, ei = self._ids(bot)
        ctx = _context()
        upd = _update(data=f"uret:e:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, ctx))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        rows = [[b.text for b in r] for r in kb.inline_keyboard]
        self.assertEqual(rows, [["✅ Üret", "❌ İptal"], ["⭐ Hit kalıbı · Yaklaşma", "⭐ Hit kopyası"]])
        cbs = [b.callback_data for r in kb.inline_keyboard for b in r]
        self.assertIn(f"uret:oy:{di}:{ei}", cbs)   # orman Yaklaşma v7 menüde aynen
        self.assertIn(f"uret:hko:{di}:{ei}", cbs)
        self.assertNotIn(f"uret:hk:{di}:{ei}", cbs)
        upd = _update(data=f"uret:hko:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, ctx))
        call = upd.callback_query.edit_message_text.await_args
        text = call.args[0]
        for part in ("Mod: ⭐ Hit kopyası (orman yangını)", SOURCE, "✋ Onay", CONFIRM_DESC):
            self.assertIn(part, text)
        self.assertNotIn("—", text)
        self.assertEqual([b.text for r in call.kwargs["reply_markup"].inline_keyboard for b in r], ["✅ Üret", "❌ İptal"])
        upd = _update(data=f"uret:hkook:{di}:{ei}")
        runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
        with patch.object(bot.pipeline, "run_pipeline", runner), patch.object(bot, "_production_lock", asyncio.Lock()):
            asyncio.run(bot.on_callback(upd, ctx))
        kw = runner.await_args.kwargs
        self.assertEqual((kw["domain"], kw["event"], kw["hit_kopya_orman"]), (DOMAIN, WF, True))
        for other in ("hit_kopya_ates", "kasirga", "donma_firtina", "cadde_yaklasma", "hortum_yaklasma",
                      "heli_yaklasma", "kul_yaklasma", "orman_yaklasma", "dalga24", "approach_env", "hit_env"):
            self.assertNotIn(other, kw)
        self.assertTrue(kw["reporter"].needs_approval)
        started = upd.callback_query.edit_message_text.await_args_list[0].args[0]
        self.assertIn("/ ⭐ Hit kopyası", started)
        _, ft = self._ids(bot, FT)
        for bad in (f"uret:hko:{di}", f"uret:hko:{di}:{ft}", f"uret:hkook:{di}:{ft}", f"uret:hkook:{di}:{ei}:x"):
            upd = _update(data=bad)
            asyncio.run(bot.on_callback(upd, ctx))
            self.assertIn("Geçersiz", upd.callback_query.edit_message_text.await_args.args[0])
        busy = asyncio.Lock()
        asyncio.run(busy.acquire())
        with patch.object(bot, "_production_lock", busy):
            upd = _update(data=f"uret:hkook:{di}:{ei}")
            asyncio.run(bot.on_callback(upd, ctx))
            self.assertEqual(upd.callback_query.edit_message_text.await_args.args[0], bot.BUSY_TEXT)
        for b in (b for m in (kb, bot.hit_kopya_orman_produce_keyboard(di, ei)) for r in m.inline_keyboard for b in r):
            self.assertLessEqual(len(b.callback_data.encode()), 64)

    def test_fire_tornado_buttons_unchanged(self):
        """Ateş hortumu onay ekranı ve Hit kopyası (hk) aynen; orman butonu orada yok."""
        import bot
        from test_tur29_infra import _context, _update
        di, ft = self._ids(bot, FT)
        ctx = _context()
        upd = _update(data=f"uret:e:{di}:{ft}")
        asyncio.run(bot.on_callback(upd, ctx))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        self.assertEqual([[b.text for b in r] for r in kb.inline_keyboard],
                         [["✅ Üret", "❌ İptal"], ["⭐ Hit kalıbı", "⭐ Hit kopyası"]])
        cbs = [b.callback_data for r in kb.inline_keyboard for b in r]
        self.assertIn(f"uret:hk:{di}:{ft}", cbs)
        self.assertFalse(any(c.startswith("uret:hko") for c in cbs))
        upd = _update(data=f"uret:hk:{di}:{ft}")
        asyncio.run(bot.on_callback(upd, ctx))
        text = upd.callback_query.edit_message_text.await_args.args[0]
        self.assertIn("Mod: ⭐ Hit kopyası (ateş hortumu)", text)
        self.assertIn(hp.HIT_KOPYA_CONFIRM_DESC, text)
        self.assertNotIn("orman", text.split("Mod:")[1])

    def test_other_fire_events_no_hko_button(self):
        import bot
        from test_tur29_infra import _context, _update
        di = str(bot.DOMAIN_KEYS.index(DOMAIN))
        ctx = _context()
        for i, e in enumerate(bot.domain_events(DOMAIN)):
            if e == WF:
                continue
            upd = _update(data=f"uret:e:{di}:{i}")
            asyncio.run(bot.on_callback(upd, ctx))
            kw = upd.callback_query.edit_message_text.await_args.kwargs
            if "reply_markup" in kw:
                cbs = [b.callback_data for r in kw["reply_markup"].inline_keyboard for b in r]
                self.assertFalse(any(c.startswith("uret:hko") for c in cbs), e)

    def test_only_wildfire(self):
        for e in es.EVENT_SKELETONS:
            self.assertEqual(hp.hit_kopya_orman_is_active(e), e == WF, e)
        with self.assertRaises(es.StructureError):
            hp.hit_kopya_orman_build_scene(DOMAIN, FT)
        with self.assertRaises(es.StructureError):
            hp.hit_kopya_orman_build_scene("city_disasters", WF)


class TestLocks(_Quiet):
    """Diğer 19 olay ve tüm modlar (önceki kod 14063ac) 40 tohum birebir; orman Yaklaşma v7 ORMAN_SHA256 aynen;
    bu modun kendi kilidi HIT_KOPYA_ORMAN_SHA256 (v3); v1 / v2 kayıtları fixture + HIT_KOPYA_ORMAN_V1/V2_SHA256."""

    def test_others_verbatim_40_seeds(self):
        snap = others_snapshot()
        self.assertEqual(len(snap["events"]), 19)
        for name, runs in snap["modes"].items():
            for s, r in runs.items():
                self.assertNotIn("error", r, (name, s))
        self.assertNotIn("hit_kopya_orman", snap["modes"])
        self.assertEqual(snapshot_hash(snap), OTHERS_SHA256)

    def test_orman_yaklasma_v7_untouched(self):
        import test_orman_yaklasma as to
        self.assertEqual(snapshot_hash(to.orman_snapshot()), ORMAN_SHA256)
        self.assertEqual(to.ORMAN_SHA256, ORMAN_SHA256)

    def test_hit_kopya_orman_lock(self):
        runs = hko_snapshot()
        self.assertEqual(len(runs), 40)
        for s, r in runs.items():
            self.assertTrue(r["combo"].endswith(f"##HKO:{r['axes']['axes']['cografya']}|bystander_handheld"), s)
            self.assertEqual((r["axes"]["axes"]["mod"], r["axes"]["axes"]["surum"]), ("hit_kopya_orman", "v3"))
            self.assertIn(CAMERA_NEW, r["prompt"])
        self.assertEqual(snapshot_hash(runs), HIT_KOPYA_ORMAN_SHA256)
        self.assertNotIn(HIT_KOPYA_ORMAN_SHA256, (HIT_KOPYA_ORMAN_V1_SHA256, HIT_KOPYA_ORMAN_V2_SHA256))

    def test_v3_differs_from_v2_only_in_camera(self):
        """40 tohum: v3 seçimleri (coğrafya/araç/engel/kişi, combo, dışlananlar) v2 fixture'ıyla aynı; prompt ve stil
        eki yalnız kamera parçasında, eksenler yalnız sürümde farklı."""
        with open(V2_FIXTURE, encoding="utf-8") as f:
            old = json.load(f)
        now = hko_snapshot()
        self.assertEqual(set(old), set(now))
        for s in now:
            o, n = old[s], now[s]
            self.assertEqual(n["prompt"], o["prompt"].replace(CAMERA_OLD, CAMERA_NEW), s)
            self.assertEqual(n["suffix"], o["suffix"].replace(CAMERA_OLD, CAMERA_NEW), s)
            self.assertEqual((n["story"], n["combo"]), (o["story"], o["combo"]), s)
            self.assertEqual(n["axes"]["axes"], {**o["axes"]["axes"], "surum": "v3"}, s)
            self.assertEqual({k: v for k, v in n["axes"].items() if k != "axes"},
                             {k: v for k, v in o["axes"].items() if k != "axes"}, s)

    def test_locked_events_hash_file(self):
        import locked_prompts as lp
        self.assertEqual(lp.hashes(), lp.load())


if __name__ == "__main__":
    unittest.main()
