# 15 Kas 2026, Bahadır: "🌪️ Hortum sahil caddesini süpürür" olayına "⭐ Hit kalıbı · Yaklaşma (cadde)" modu
# (core/hit_prompts.py YAKLASMA_CADDE). Temel: 17 Eki hit'i (1,2M; Onay P6+Q3, beyaz minibüs, yüksek cam korkuluklu
# balkon). YAKLASMA_HORTUM ile aynı düzen: GPT yok, hikâye koddan birebir, zaman etiketleri var. Coğrafya G1-G6 (son 3,
# G1 tohum: ilk 3 üretimde G1 yok), araç son 2, orta O1-O2 / final F1-F3 son 1. Normal "sahil caddesi" yolu ve bütün
# diğer olay/modlar değişmez. Ağ yok.
# 15 Kas (2): ilk üretim (İspanya, O1+F2) 6/10 aldı; kamera 10. kata çıktı, savrulan minibüs yoluna devam etti. Alçak
# ölçek (G3/G5/G6), park halindeki araç hurda kalır (O1/O2), karşıdaki bina (F1/F2), 3. kat balkon + iki şeritli cadde
# (stil eki). Eski metinler CADDE_PASIF (_V1); aktif prompt'ta hiç çıkmaz.
# 15 Kas (3): mod hit'ten uzaklaştı (Meksika üretimi 2/10). Hit'in kendi Kie prompt'una dönüş: metin birebir, sadece
# coğrafya, park halindeki araç + hurda, kameraya yakın final ve hafif takip. "eye level, normal lens" bu modda serbest.
# Kişi 5/6. 15 Kas (2) metinlerinin hepsi CADDE_PASIF (_V2).
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

AV = es.AVENUE
CT = hp.YAKLASMA_CADDE
DOMAIN = "coastal_tornado_landfall"
PLACES = {"G1": ("ABD", "a Californian beach town"),
          "G2": ("Brezilya", "a Brazilian beach city with wavy mosaic sidewalks"),
          "G3": ("Avustralya", "an Australian beach town of low-rise surf shops and cafes"),
          "G4": ("Meksika", "a Mexican beach town of colorful low buildings"),
          "G5": ("İspanya", "a Spanish seaside town of low whitewashed houses"),
          "G6": ("Hindistan", "an Indian seaside town of low pastel buildings")}
OPENING = ("A violent tornado sweeps down a palm-lined coastal avenue of {place}, hurling signs, branches and debris "
           "along the road.")
PEOPLE = {5: "Five people scramble in a panic, sprinting down the sidewalk to escape its furious path.",
          6: "Six people scramble in a panic, sprinting down the sidewalk to escape its furious path."}
VEHICLES = ("white van", "pickup truck", "SUV")
MIDS = {
    "O1": "The tornado lifts a parked {vehicle} skyward, spinning it wildly before it crashes, wrecked, onto the avenue.",
    "O2": "The tornado flips a parked {vehicle} and sends it rolling over and over down the avenue until it stops, "
          "crushed, on its roof.",
}
FINALS = {
    "F1": "Right across the street, the tornado tears the roof off a building, the pieces flying past the camera.",
    "F2": "Right across the street, the tornado rips the balconies and front wall off a building, debris flying past "
          "the camera.",
    "F3": "Right below the balcony, the tornado rips the palm trees out by the roots and hurls them past the camera.",
}
TAIL = ("Handheld footage shot by a person standing on a high balcony across the street, overlooking the avenue, eye "
        "level, normal lens; slight hand shake, the camera follows the tornado only slightly, keeping the avenue in "
        "frame; no zoom, no cuts. Bystanders wear civilian clothes, never hi-vis PPE on civilians; emergency responders "
        "wear service uniforms. Raw natural light matching the weather, never glossy or CGI; no white hazmat suits.")
WARNING = "⚠️ Araç ortası: videoda aracın tek parça kalıp kalmadığını kontrol et."
CAMERA_LINE = "Kamera: hit kamerası (yüksek balkon, normal lens, hafif takip)"
REQUIRED = ("high balcony across the street", "normal lens", "a parked")
FORBIDDEN = ("pans to follow", "third-floor", "glass railing", "the sea at its end", "Full action",
             "Until the last frame")
PASIF = {
    "G3_V1": "an Australian beach city lined with high-rise hotels",
    "G5_V1": "a Spanish seaside town of white apartment blocks",
    "G6_V1": "an Indian seaside city of pastel apartment blocks",
    "O1_V1": "The tornado sweeps the {vehicle} up into the air, spins it, and crashes it down across the avenue.",
    "O2_V1": "The tornado flips the {vehicle} and sends it rolling over and over down the avenue toward the camera.",
    "F1_V1": "Right across from the balcony, the tornado tears the roof off an apartment building, the pieces flying "
             "past the camera.",
    "F2_V1": "Right across from the balcony, the tornado rips the balconies and front wall off an apartment building, "
             "debris flying past the camera.",
    "STIL_V1": ("Handheld footage shot from a high balcony with a glass railing across the avenue, high vantage; slight "
                "hand shake, the camera stays fixed, tilting only slightly, never descending, the tornado always in "
                "frame, the glass railing in the foreground; one continuous shot, no zoom, no cuts, no person or face "
                "close to the camera. Setting: a wide palm-lined avenue with parked cars and the sea at its end. All "
                "people are ordinary civilians in everyday clothes, no hazmat suits, natural light under grey storm "
                "clouds, never CGI. Everything moves in real time, never in slow motion, people run at full speed."),
    "KAMERA_SATIRI_V1": "Kamera: sabit (hafifçe eğilir, cam korkuluklu yüksek balkon)",
    "ACILIS_V2": ("A violent tornado sweeps down a palm-lined coastal avenue of {place}, hurling signs, branches and "
                  "debris along the road, and heads straight toward the camera."),
    "INSAN_3_V2": "Three people sprint along the sidewalk toward the camera, fleeing the tornado.",
    "INSAN_5_V2": "Five people sprint along the sidewalk toward the camera, fleeing the tornado.",
    "O1_V2": "The tornado sweeps a parked {vehicle} up into the air, spins it, and slams it down on its roof across the "
             "avenue, where it stays wrecked.",
    "O2_V2": "The tornado flips a parked {vehicle} and sends it rolling over and over down the avenue toward the camera "
             "until it stops, crushed, on its side.",
    "F1_V2": "Right across from the balcony, the tornado tears the roof off the building across the street, the pieces "
             "flying past the camera.",
    "F2_V2": "Right across from the balcony, the tornado rips the balconies and front wall off the building across the "
             "street, debris flying past the camera.",
    "F3_V2": "Right below the balcony, the tornado rips the palm trees out by the roots and hurls them past the camera.",
    "KAMERA_V2": "the camera stays fixed, tilting only slightly",
    "STIL_V2": ("Handheld footage shot from a third-floor balcony with a glass railing across the avenue, high vantage; "
                "slight hand shake, the camera stays fixed, tilting only slightly, never descending, the tornado always "
                "in frame, the glass railing in the foreground; one continuous shot, no zoom, no cuts, no person or "
                "face close to the camera. Setting: a two-lane palm-lined avenue with cars parked on both sides, "
                "low-rise buildings, the sea at its end. All people are ordinary civilians in everyday clothes, no "
                "hazmat suits, natural light under grey storm clouds, never CGI. Everything moves in real time, never "
                "in slow motion, people run at full speed."),
    "KAMERA_SATIRI_V2": "Kamera: sabit (hafifçe eğilir, cam korkuluklu 3. kat balkon)",
    "ZORUNLU_V2": ("high vantage", "glass railing", "third-floor balcony", "a parked"),
    "YASAK_V2": ("pans to follow", "eye level", "Full action", "Until the last frame", "high-rise", "apartment block",
                 "wide palm-lined avenue"),
}
# 15 Kas (3): F3 hit'in kendi cümlesiyle aynı kaldı (F3_V2 = aktif F3); diğer _V2 metinler aktif kalıpta yok
SAME_AS_ACTIVE = ("F3_V2",)
# aktif prompt'ta hiç çıkmaması gereken eski parçalar (sabit cümleler + eski ortaların araçtan sonraki kısmı)
OLD_MARKS = (PASIF["G3_V1"], PASIF["G5_V1"], PASIF["G6_V1"], PASIF["F1_V1"], PASIF["F2_V1"], PASIF["STIL_V1"],
             " up into the air, spins it, and crashes it down across the avenue.",
             " down the avenue toward the camera. ", "an apartment building", "from a high balcony with a glass railing",
             "Setting: a wide palm-lined avenue with parked cars and the sea at its end.", "white apartment blocks",
             "high-rise hotels", "wide avenue", "The tornado sweeps the ", "The tornado flips the ",
             # 15 Kas (3): _V2 parçaları
             PASIF["STIL_V2"], PASIF["F1_V2"], PASIF["F2_V2"], PASIF["INSAN_3_V2"], PASIF["INSAN_5_V2"],
             PASIF["KAMERA_V2"], "and heads straight toward the camera.", " up into the air, spins it, and slams it down",
             "where it stays wrecked.", "toward the camera until it stops, crushed, on its side.",
             "Right across from the balcony", "third-floor", "glass railing", "high vantage", "the sea at its end",
             "Setting:", "stays fixed", "grey storm clouds", "people run at full speed")


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
    return asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": AV, "cadde_yaklasma": True,
                                                     "used_combos": [], "recent_topics": [], **extra}))


def build(seed: int) -> dict:
    reset()
    random.seed(seed)
    return gen()


def all_combos():
    for g in CT["geos"]:
        for ppl in (5, 6):
            for v in CT["vehicles"]:
                for m in CT["mids"]:
                    for f in CT["finals"]:
                        yield (g, ppl, v, m, f), hp.cadde_prompt(g, ppl, m, v, f)


class TestTexts(_Quiet):
    def test_verbatim_texts(self):
        self.assertEqual(hp.CADDE_MODE_LABEL, "⭐ Hit kalıbı · Yaklaşma (cadde)")
        self.assertEqual(hp.CADDE_EVENTS, (AV,))
        self.assertEqual({g: (CT["geos"][g]["name"], CT["geos"][g]["place"]) for g in CT["geos"]}, PLACES)
        for g, (_, place) in PLACES.items():
            self.assertEqual(hp.cadde_opening(g), OPENING.format(place=place))
        for n, text in PEOPLE.items():
            self.assertEqual(hp.cadde_people(n), text)
        for n in (2, 3, 4, 7):
            with self.assertRaises(es.StructureError):
                hp.cadde_people(n)
        self.assertEqual(CT["vehicles"], VEHICLES)
        self.assertEqual(CT["mids"], MIDS)
        self.assertEqual(CT["finals"], FINALS)
        self.assertEqual(CT["vehicle_mids"], ("O1", "O2"))
        self.assertEqual(hp.cadde_tail(), TAIL)
        self.assertEqual(hp.CADDE_VEHICLE_WARNING, WARNING)
        self.assertEqual(hp.CADDE_GEO_SEED, ("G1",))
        self.assertEqual((hp.CADDE_GEO_BLOCK, hp.CADDE_VEHICLE_BLOCK, hp.CADDE_MID_BLOCK, hp.CADDE_FINAL_BLOCK),
                         (3, 2, 1, 1))
        self.assertEqual((hp.CADDE_MAX_WORDS, hp.CADDE_MAX_CHARS), (230, 1400))
        self.assertEqual(hp.CADDE_REQUIRED, REQUIRED)
        self.assertEqual(hp.CADDE_FORBIDDEN, FORBIDDEN)
        self.assertEqual(hp.CADDE_CAMERA_LINE, CAMERA_LINE)
        self.assertEqual(CT["opening"], OPENING)
        self.assertEqual(CT["camera"], "the camera follows the tornado only slightly, keeping the avenue in frame")
        self.assertIn(hp.cadde_camera_text(), TAIL)
        # sıra: açılış + insan + orta + final + stil eki; zaman etiketleri talimattaki gibi
        p = hp.cadde_prompt("G4", 5, "O1", "white van", "F1")
        self.assertEqual(p, "0-4s: A violent tornado sweeps down a palm-lined coastal avenue of a Mexican beach town of "
                            "colorful low buildings, hurling signs, branches and debris along the road. Five people "
                            "scramble in a panic, sprinting down the sidewalk to escape its furious path. 4-9s: The "
                            "tornado lifts a parked white van skyward, spinning it wildly before it crashes, wrecked, "
                            "onto the avenue. 9-15s: Right across the street, the tornado tears the roof off a building, "
                            "the pieces flying past the camera. " + TAIL)

    def test_passive_not_active(self):
        """15 Kas (2): değişen her eski metin CADDE_PASIF'te _V1; 15 Kas (3): bütün önceki metinler _V2. Aktif kalıpta
        ve 216 prompt'un hiçbirinde yok (F3_V2 hit'in cümlesiyle aynı kaldı)."""
        self.assertEqual(hp.CADDE_PASIF, PASIF)
        active = json.dumps(CT, ensure_ascii=False)
        for key, old in PASIF.items():
            if key.startswith(("KAMERA_SATIRI", "ZORUNLU", "YASAK")) or key in SAME_AS_ACTIVE:
                continue
            self.assertNotIn(old, active, key)
        self.assertEqual(PASIF["F3_V2"], FINALS["F3"])
        self.assertNotEqual(hp.CADDE_REQUIRED, PASIF["ZORUNLU_V2"])
        self.assertNotEqual(hp.CADDE_FORBIDDEN, PASIF["YASAK_V2"])
        for _, p in all_combos():
            for m in OLD_MARKS:
                self.assertNotIn(m, p, m)
        for seed in range(1, 41):
            d = build(seed)
            for m in OLD_MARKS:
                self.assertNotIn(m, d["scenes"][0]["prompt"], (seed, m))
            for key in ("KAMERA_SATIRI_V1", "KAMERA_SATIRI_V2"):
                self.assertNotIn(PASIF[key], d["structure"]["cadde_yaklasma"]["lines"])

    def test_vehicle_fill(self):
        for v in VEHICLES:
            for m in MIDS:
                self.assertEqual(hp.cadde_mid(m, v), MIDS[m].format(vehicle=v))
                self.assertIn(f"a parked {v} ", hp.cadde_mid(m, v))
        for m in MIDS:
            with self.assertRaises(es.StructureError):
                hp.cadde_mid(m, None)
            with self.assertRaises(es.StructureError):
                hp.cadde_mid(m, "delivery van")   # bu modun havuzunda değil
        for bad in ("O3", "P6", "C1"):
            with self.assertRaises(es.StructureError):
                hp.cadde_mid(bad, "SUV")
        for bad in ("F4", "Q3", "E1"):
            with self.assertRaises(es.StructureError):
                hp.cadde_final(bad)

    def test_all_combos_within_limits(self):
        """216 kombinasyon: hepsi ≤ 230 kelime, ≤ 1400 karakter; sıra açılış + insan + orta + final + stil eki."""
        n, over, words, chars = 0, [], (0, None), (0, None)
        for key, p in all_combos():
            n += 1
            g, ppl, v, m, f = key
            w, c = len(p.split()), len(p)
            words, chars = max(words, (w, key)), max(chars, (c, key))
            if w > hp.CADDE_MAX_WORDS or c > hp.CADDE_MAX_CHARS:
                over.append((key, w, c))
            expected = (f"0-4s: {OPENING.format(place=PLACES[g][1])} {PEOPLE[ppl]} 4-9s: "
                        f"{MIDS[m].format(vehicle=v)} 9-15s: {FINALS[f]} {TAIL}")
            self.assertEqual(p, expected, key)
            self.assertEqual(sum(pl in p for _, pl in PLACES.values()), 1, key)
            self.assertEqual(hp.cadde_camera_issues(p, g), [], key)
            for bad in FORBIDDEN + (sk.FULL_MOTION,):
                self.assertNotIn(bad, p)
        self.assertEqual(n, 6 * 2 * 3 * 2 * 3)
        self.assertEqual(over, [])
        # 15 Kas (3), talimattaki hesap: en kısa 143, en uzun 158 kelime (G3 + white van + O2 + F2), en uzun karakter
        # 958 (G3 + pickup truck + O2 + F2)
        self.assertEqual(words[0], 158)
        self.assertEqual(min(len(p.split()) for _, p in all_combos()), 143)
        self.assertEqual(len(hp.cadde_prompt("G3", 5, "O2", "white van", "F2").split()), 158)
        self.assertEqual(chars[0], 958)
        self.assertEqual(len(hp.cadde_prompt("G3", 5, "O2", "pickup truck", "F2")), 958)
        self.assertEqual(chars[1][0::2], ("G3", "pickup truck", "F2"))

    def test_sentences_only_in_this_mode(self):
        """Bu modun cümleleri başka hiçbir olayda / modda çıkmaz."""
        marks = ["sweeps down a palm-lined coastal avenue of", *PEOPLE.values(),
                 *[t.split("{vehicle}")[1] for t in MIDS.values()], *FINALS.values(),
                 "the camera follows the tornado only slightly, keeping the avenue in frame", TAIL,
                 *[p for _, p in PLACES.values()]]
        pools = json.dumps({e: {s: {k: v["text"] for k, v in b[s].items()} for s in ("slice_2", "slice_3")}
                            for e, b in es.EVENT_BEATS.items()}, ensure_ascii=False)
        others = pools + json.dumps(es.EVENT_KEY_VISUAL, ensure_ascii=False)
        for name in ("HIT_PROMPTS", "YAKLASMA_ATES_HORTUMU", "DALGA_24EYLUL", "YAKLASMA_KUL_BULUTU", "KUL_PASIF",
                     "YAKLASMA_ORMAN", "ORMAN_PASIF", "YAKLASMA_HELIKOPTER", "YAKLASMA_HORTUM", "HORTUM_PASIF"):
            others += json.dumps(getattr(hp, name), default=str, ensure_ascii=False)
        for ev in ps.active_events():
            for seed in range(1, 6):
                others += json.dumps(ps.snapshot_event(ev, seed), ensure_ascii=False)
        for flag, ev in (("hortum_yaklasma", es.LANDFALL), ("heli_yaklasma", es.HELICOPTER),
                         ("kul_yaklasma", es.PYROCLASTIC), ("orman_yaklasma", es.WILDFIRE), ("dalga24", es.TIDAL)):
            for seed in range(1, 4):
                reset()
                random.seed(seed)
                d = asyncio.run(pg.generate_creative_prompts({"domain": None, "event": ev, flag: True,
                                                             "used_combos": [], "recent_topics": []}))
                others += d["scenes"][0]["prompt"]
        for m in marks:
            self.assertNotIn(m, others, m)


class TestCaddeMode(_Quiet):
    def _check(self, d):
        sc, st = d["scenes"][0], d["structure"]
        tb = st["cadde_yaklasma"]
        prompt = sc["prompt"]
        self.assertIn(tb["geo"], PLACES)
        self.assertIn(tb["vehicle"], VEHICLES)
        self.assertIn(tb["mid"], MIDS)
        self.assertIn(tb["final"], FINALS)
        self.assertIn(tb["people"], (5, 6))
        self.assertEqual(prompt, hp.cadde_prompt(tb["geo"], tb["people"], tb["mid"], tb["vehicle"], tb["final"]))
        self.assertTrue(prompt.endswith(" " + TAIL))
        self.assertEqual(sc["style_suffix"], TAIL)
        self.assertIn(f"a parked {tb['vehicle']} ", prompt)
        self.assertIn(PLACES[tb["geo"]][1], prompt)
        for need in REQUIRED:
            self.assertIn(need, prompt)
        for bad in FORBIDDEN:
            self.assertNotIn(bad, prompt)
        self.assertIn("eye level, normal lens", prompt)   # 15 Kas (3): hit'in ifadesi, bu modda serbest
        self.assertLessEqual(len(prompt.split()), 230)
        self.assertLessEqual(len(prompt), 1400)
        self.assertIn(f"#{tb['mid']}+{tb['final']}|", d["combo_key"])
        for slot in ("slice_2", "slice_3"):   # normal cadde havuzu (P*/Q*) metni yok
            for bid in es.EVENT_BEATS[AV][slot]:
                self.assertNotIn(es.beat_text(AV, slot, bid, tb["vehicle"])[4:], prompt)
        self.assertNotIn(es.EVENT_KEY_VISUAL[AV], prompt)
        self.assertEqual(cp.submit_issues(st, {"prompt": prompt, "story": sc["story"],
                                               "style_suffix": sc["style_suffix"]}), [])
        return tb

    def test_40_seeds_no_error_and_no_gpt(self):
        with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT çağrıldı"))) as gpt, \
             patch.object(pg, "_get_openai_client", side_effect=AssertionError("GPT istemcisi istendi")):
            for seed in range(1, 41):
                self._check(build(seed))
        gpt.assert_not_called()
        self.assertEqual(es.CODE_STORY_FORCE.get(), frozenset())   # geçici anahtar geri alındı
        self.assertFalse(es.code_story(AV))

    def test_g1_seed_first_three(self):
        """G1 başlangıçta kullanıldı sayılır: ilk 3 üretimde G1 gelmez, sonra serbest."""
        later = []
        for seed in range(1, 21):
            reset()
            random.seed(seed)
            runs = [self._check(gen()) for _ in range(8)]
            geos = [r["geo"] for r in runs]
            self.assertNotIn("G1", geos[:3], (seed, geos))
            seq = ["G1"] + geos
            for i in range(1, len(seq)):
                self.assertNotIn(seq[i], seq[max(0, i - 3):i], (seed, seq))
            later.append("G1" in geos[3:])
        self.assertTrue(any(later))
        for s in range(40):
            self.assertNotEqual(hp.cadde_choose_geo([], random.Random(s)), "G1")

    def test_lru(self):
        mids, finals = set(), set()
        for seed in range(1, 16):
            reset()
            random.seed(seed)
            runs = [self._check(gen()) for _ in range(9)]
            for key in ("mid", "final"):
                vals = [r[key] for r in runs]
                for i in range(1, len(vals)):
                    self.assertNotEqual(vals[i], vals[i - 1], (seed, key, vals))
            used = [r["vehicle"] for r in runs]
            for i in range(len(used)):
                self.assertNotIn(used[i], used[max(0, i - 2):i], (seed, used))
            self.assertEqual(hp._CADDE_VEHICLE_MEMORY[-9:], used)   # araç geçmişi her üretimde ilerler
            mids |= {r["mid"] for r in runs}
            finals |= {r["final"] for r in runs}
        self.assertEqual(mids, set(MIDS))
        self.assertEqual(finals, set(FINALS))

    def test_history_sources(self):
        def combo(tag):
            return f"{DOMAIN}|none|{AV.lower()}|high balcony over a downtown avenue##{tag}|bystander_handheld"
        reset()
        hist = [combo("O1+F1"), combo("P6+Q3"), combo("O2+F3")]
        for s in range(30):
            self.assertEqual(hp.cadde_choose_mid(hist, random.Random(s)), "O1")   # son 1: O2 elenir
            self.assertIn(hp.cadde_choose_final(hist, random.Random(s)), ("F1", "F2"))   # son 1: F3 elenir
        lf = [f"{DOMAIN}|none|{es.LANDFALL.lower()}|x##O1+F2|bystander_handheld"]   # hortum kaydı cadde'yi etkilemez
        self.assertEqual(hp.cadde_tags(lf), [])
        recs = [{"eksenler": json.dumps({"event": AV, "axes": {"mod": "cadde_yaklasma", "cografya": g, "arac": v}})}
                for g, v in (("G2", "SUV"), ("G3", "white van"), ("G4", "SUV"))] + [{"eksenler": "x"}]
        recs.append({"eksenler": json.dumps({"event": es.LANDFALL, "axes": {"mod": "hortum_yaklasma",
                                                                            "cografya": "G5", "arac": "pickup truck"}})})
        self.assertEqual(hp.cadde_axes_history(recs, "cografya"), ["G2", "G3", "G4"])
        self.assertEqual(hp.cadde_axes_history(recs, "arac"), ["SUV", "white van", "SUV"])
        self.assertIsNone(hp.cadde_axes_history(None, "arac"))
        for seed in range(1, 11):
            reset()
            random.seed(seed)
            d = gen(axes_loader=lambda dom: recs)
            tb = d["structure"]["cadde_yaklasma"]
            self.assertIn(tb["geo"], ("G1", "G5", "G6"))   # son 3 (G2, G3, G4) elenir; 4. üretimde G1 tohumu serbest
            self.assertEqual(tb["vehicle"], "pickup truck")
            axes = json.loads(d["axes_json"])["axes"]
            self.assertEqual((axes["mod"], axes["cografya"], axes["arac"]), ("cadde_yaklasma", tb["geo"],
                                                                             tb["vehicle"]))

    def test_kie_final_check(self):
        d = build(7)
        sc, st = d["scenes"][0], d["structure"]
        tb = st["cadde_yaklasma"]
        info = {"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"]}
        self.assertEqual(cp.submit_issues(st, info), [])
        p0 = sc["prompt"]
        place = PLACES[tb["geo"]][1]
        other = PLACES["G2" if tb["geo"] != "G2" else "G3"][1]
        end = "no white hazmat suits."
        for old_s, new_s in (("high balcony across the street", "low balcony across the street"),
                             ("normal lens", "wide lens"), (place, "a beach town"), (place, other),
                             ("follows the tornado only slightly", "pans to follow the tornado"),
                             (end, end + " Shot from a third-floor balcony."),
                             (end, end + " A glass railing in the foreground."),
                             (end, end + " The sea at its end."), (end, end + " Setting: the sea at its end."),
                             (end, end + " Full action from the very first frame to the last."),
                             (end, end + " Until the last frame, it rages."),
                             ("a parked", "a moving"), ("4-9s: ", "")):
            bad = p0.replace(old_s, new_s)
            self.assertNotEqual(bad, p0, old_s)
            self.assertTrue(hp.cadde_issues(st, {**info, "prompt": bad}), new_s)
            self.assertTrue(cp.submit_issues(st, {**info, "prompt": bad}), new_s)
        self.assertIn('"high balcony across the street" eksik',
                      hp.cadde_camera_issues(p0.replace("high balcony across the street", "balcony"), tb["geo"]))
        self.assertIn('"normal lens" eksik', hp.cadde_camera_issues(p0.replace("normal lens", "lens"), tb["geo"]))
        self.assertIn('"a parked" eksik', hp.cadde_camera_issues(p0.replace("a parked", "the"), tb["geo"]))
        for old in (PASIF["G3_V1"], PASIF["G5_V1"], PASIF["G6_V1"]):   # eski yer metinleri G1-G6'da yok
            self.assertTrue(hp.cadde_camera_issues(p0.replace(place, old), tb["geo"]), old)
        # 15 Kas (3): "eye level" bu modda serbest (hit'in ifadesi), eski stil eki ise yasak ifadelere takılır
        self.assertIn("eye level", p0)
        self.assertEqual(hp.cadde_camera_issues(p0 + " Shot at eye level.", tb["geo"]), [])
        self.assertTrue(hp.cadde_camera_issues(p0.replace(TAIL, PASIF["STIL_V2"]), tb["geo"]))
        self.assertIn("G1-G6 yer metni yok", hp.cadde_camera_issues(p0.replace(place, "a town"), tb["geo"]))
        for bad in FORBIDDEN:
            self.assertIn(f"bu modda olmayan ifade var: {bad}", hp.cadde_camera_issues(p0 + f" {bad}.", tb["geo"]))
        for bad in ({"geo": "G7"}, {"mid": "P6"}, {"mid": "O3"}, {"final": "Q3"}, {"people": 4},
                    {"mid": "O1", "vehicle": None}, {"vehicle": "delivery van"}):
            self.assertTrue(cp.submit_issues({**st, "cadde_yaklasma": {**tb, **bad}}, info), bad)
        self.assertTrue(cp.submit_issues(st, {**info, "style_suffix": "x"}))
        story = asyncio.run(cp.rewrite_structured(st, "test", AsyncMock(side_effect=AssertionError("GPT"))))
        self.assertEqual(story, sc["story"])
        with patch.object(hp, "CADDE_REQUIRED", ("normal lens", "a parked", "olmayan ifade")):
            reset()
            random.seed(7)
            with self.assertRaises(es.StructureError):
                gen()

    def _approval(self, d):
        sc, st = d["scenes"][0], d["structure"]
        tb = st["cadde_yaklasma"]
        lines = tb["lines"].split("\n")
        self.assertEqual(lines, [
            "Mod: ⭐ Hit kalıbı · Yaklaşma (cadde)",
            f"Coğrafya: {tb['geo']} {PLACES[tb['geo']][0]}",
            f"Araç: {tb['vehicle']}",
            f"Orta (4-9s): {tb['mid']} «{MIDS[tb['mid']].format(vehicle=tb['vehicle'])}»",
            f"Final (9-15s): {tb['final']} «{FINALS[tb['final']]}»",
            f"Kişi: {tb['people']}",
            CAMERA_LINE,
            f"Kelime: {len(sc['prompt'].split())} (en fazla 230) · karakter: {len(sc['prompt'])} (en fazla 1400)",
            WARNING])   # O1 ve O2'de uyarı
        shown = sections_to_text(format_generation(d["trace"])) + "\n" + st["axes_line"]
        sel, _, rest = shown.partition("🔍 2.")
        story = rest.split("🔍 3. Hikâye\n", 1)[1]
        for part in (hp.cadde_opening(tb["geo"]), hp.cadde_mid(tb["mid"], tb["vehicle"]), FINALS[tb["final"]]):
            self.assertIn(part, sc["prompt"])
            self.assertIn(part, sel)
            self.assertIn(part, story)
        self.assertIn("Mod: ⭐ Hit kalıbı · Yaklaşma (cadde)", sel)
        self.assertIn("Eksenler (⭐ Hit kalıbı · Yaklaşma (cadde)): ", st["axes_line"])
        self.assertIn("\nTekrar önleme: coğrafya son 3 elendi (G1 tohum)", st["axes_line"])
        for part in (f"coğrafya={tb['geo']} {PLACES[tb['geo']][0]}", f"araç={tb['vehicle']}", f"orta={tb['mid']}",
                     f"final={tb['final']}", f"kişi={tb['people']}"):
            self.assertIn(part, st["axes_line"])
        _, body = format_final_prompt({"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"],
                                       "hit_lines": tb["lines"], "environment": st["environment"]})
        self.assertIn("\nMod: ⭐ Hit kalıbı · Yaklaşma (cadde)\n", body)
        self.assertIn("\n\n" + sc["prompt"], body)
        return tb["mid"]

    def test_approval_lines_and_display(self):
        seen = set()
        for seed in range(1, 40):
            seen.add(self._approval(build(seed)))
        self.assertEqual(seen, {"O1", "O2"})

    def test_normal_avenue_untouched(self):
        """Normal "sahil caddesi" yolu: GPT yolu aynen (kod hikâyesi zorlanmaz), bu modun metni yok."""
        self.assertFalse(es.code_story(AV))
        for seed in range(1, 6):
            reset()
            random.seed(seed)
            fake = AsyncMock(return_value=dict(ps.FAKE_SLICES))
            with patch.object(pg, "_call_gpt", fake):
                d = asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": AV, "used_combos": [],
                                                             "recent_topics": []}))
            self.assertTrue(fake.await_count >= 1)   # normal yolda GPT denenir (kilitli değil)
            self.assertNotIn("cadde_yaklasma", d["structure"])
            self.assertNotIn("mode_label", d["trace"])
            p = d["scenes"][0]["prompt"]
            for x in ("coastal avenue of", *PEOPLE.values(), *[pl for _, pl in PLACES.values()], TAIL,
                      "the camera follows the tornado only slightly"):
                self.assertNotIn(x, p)
            self.assertNotRegex(d["combo_key"], r"#O\d\+F\d\|")
        for seed in range(1, 6):   # baseline ile birebir (20 tohumluk prompt_snapshot)
            self.assertEqual(ps.snapshot_event(AV, seed), ps.load_baseline()[AV][str(seed)])


class TestCaddePipelineAndBot(_Quiet):
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
                return await orig(**kw, cadde_yaklasma=True)
            with patch.object(main, "run_pipeline", run_with):
                r = t.run_pipe(gen=AsyncMock(side_effect=fake_gen), reporter=rep, event=AV)
        finally:
            t.doCleanups()
        self.assertTrue(r["success"], r)
        self.assertIs(seen["config"]["cadde_yaklasma"], True)
        approve = [c[1] for c in rep.calls if c[0] == "approve"]
        self.assertEqual(len(approve), 1)   # Kie'ye göndermeden önce ✋ Onay
        info = approve[0]
        self.assertTrue(info["hit_lines"].startswith("Mod: ⭐ Hit kalıbı · Yaklaşma (cadde)\nCoğrafya: G"))
        self.assertEqual(t.create.await_args.args[1], info["prompt"])   # Kie'ye giden = onaydaki

    def test_bot_button_and_flow(self):
        import bot
        from test_tur29_infra import _context, _update
        di = str(bot.DOMAIN_KEYS.index(DOMAIN))
        ei = str(bot.domain_events(DOMAIN).index(AV))
        self.assertEqual(bot.EVENT_LABELS[AV], "🌪️ Hortum sahil caddesini süpürür")
        ctx = _context()
        upd = _update(data=f"uret:e:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, ctx))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        labels = [b.text for r in kb.inline_keyboard for b in r]
        self.assertEqual(labels, ["✅ Üret", "❌ İptal", "⭐ Hit kalıbı · Yaklaşma"])
        self.assertEqual([len(r) for r in kb.inline_keyboard], [2, 1])   # buton Üret/İptal'in altında
        self.assertEqual(kb.inline_keyboard[1][0].callback_data, f"uret:cy:{di}:{ei}")
        upd = _update(data=f"uret:cy:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, ctx))
        text = upd.callback_query.edit_message_text.await_args.args[0]
        self.assertIn("Mod: ⭐ Hit kalıbı · Yaklaşma (cadde)", text)
        self.assertIn(CAMERA_LINE, text)
        self.assertIn("normal lens", text)
        self.assertIn("hafifçe takip", text)
        for old in ("3. kat", "cam korkuluk", "iki şeritli", PASIF["KAMERA_SATIRI_V2"]):
            self.assertNotIn(old, text)
        kb2 = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        self.assertEqual([b.text for r in kb2.inline_keyboard for b in r], ["✅ Üret", "❌ İptal"])
        upd = _update(data=f"uret:cyok:{di}:{ei}")
        runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
        with patch.object(bot.pipeline, "run_pipeline", runner), patch.object(bot, "_production_lock", asyncio.Lock()):
            asyncio.run(bot.on_callback(upd, ctx))
        kw = runner.await_args.kwargs
        self.assertEqual((kw["event"], kw["cadde_yaklasma"]), (AV, True))
        for other in ("hortum_yaklasma", "heli_yaklasma", "kul_yaklasma", "orman_yaklasma", "dalga24", "approach_env",
                      "hit_env"):
            self.assertNotIn(other, kw)
        self.assertTrue(kw["reporter"].needs_approval)
        # aynı kategorinin diğer olaylarında bu buton yok
        for i, e in enumerate(bot.domain_events(DOMAIN)):
            if e == AV:
                continue
            upd = _update(data=f"uret:e:{di}:{i}")
            asyncio.run(bot.on_callback(upd, ctx))
            kw = upd.callback_query.edit_message_text.await_args.kwargs
            if "reply_markup" in kw:
                cbs = [b.callback_data for r in kw["reply_markup"].inline_keyboard for b in r]
                self.assertFalse(any(c.startswith("uret:cy") for c in cbs), e)
            self.assertIsNone(bot.parse_cadde(di, str(i)))


class TestOtherModesUntouched(_Quiet):
    """15 Kas (3): "eye level" serbestliği sadece bu modda; hortum Yaklaşma ve diğer modlar birebir aynı."""

    def test_other_modes_rules_same(self):
        self.assertEqual(hp.HORTUM_FORBIDDEN, ("colorful houses along a stone quay", "Full action",
                                               "Until the last frame"))
        import prompt_rules as pr
        self.assertIn("eye level", pr.CAMERA_BANNED)   # normal hattın kamera kuralı (K1) aynı
        for flag, ev in (("hortum_yaklasma", es.LANDFALL), ("heli_yaklasma", es.HELICOPTER),
                         ("kul_yaklasma", es.PYROCLASTIC), ("orman_yaklasma", es.WILDFIRE), ("dalga24", es.TIDAL)):
            for seed in range(1, 6):
                reset()
                random.seed(seed)
                d = asyncio.run(pg.generate_creative_prompts({"domain": None, "event": ev, flag: True,
                                                             "used_combos": [], "recent_topics": []}))
                p = d["scenes"][0]["prompt"]
                self.assertNotIn("eye level", p, (flag, seed))
                self.assertEqual(cp.submit_issues(d["structure"], {"prompt": p, "story": d["scenes"][0]["story"],
                                                                   "style_suffix": d["scenes"][0]["style_suffix"]}),
                                 [], (flag, seed))

    def test_hortum_prompts_verbatim(self):
        """Hortum Yaklaşma 40 tohum prompt'u 15 Kas (2) kilidiyle birebir (test_hortum_yaklasma ile aynı hash)."""
        import hashlib
        prompts = []
        for seed in range(1, 41):
            reset()
            random.seed(seed)
            d = asyncio.run(pg.generate_creative_prompts({"domain": None, "event": es.LANDFALL, "hortum_yaklasma": True,
                                                         "used_combos": [], "recent_topics": []}))
            prompts.append(d["scenes"][0]["prompt"])
            for m in ("follows the tornado only slightly", *PEOPLE.values()):
                self.assertNotIn(m, prompts[-1])
        self.assertEqual(hashlib.sha256("\n".join(prompts).encode()).hexdigest(),
                         "dd4c4d78a0614c5b668d6a7214bcb6fd3ad3d76b38d3c2c55efdfec04c5e95ec")


if __name__ == "__main__":
    unittest.main()
