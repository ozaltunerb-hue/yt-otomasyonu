# 14 Kas 2026, Bahadır: hortum "⭐ Hit kalıbı · Yaklaşma" modu (core/hit_prompts.py YAKLASMA_HORTUM).
# Kaynak: kanal rekoru "It came off the sea and straight into the harbor town" (1 Kas paylaşımı, 10M+), 31 Eki 09:52,
# coastal_tornado_landfall C1+E1, pencere kadrajı, pickup truck. GPT yok, zaman etiketleri var. Coğrafya G1-G6 (son 3,
# G3 tohum: ilk üretimde G3 yok), araç son 2, orta O1-O3 / final F1-F3 son 1. "Hortum karaya vurur" normal yolu (KİLİTLİ)
# ve bütün diğer olay/modlar değişmez. Ağ yok.
# 15 Kas 2026, Bahadır: her coğrafyanın kendi yer metni + SAHNE cümlesi (stil ekinde kamera cümlesinin arkasında), eski
# sabit "Setting: colorful houses ..." STIL_V1 pasif; O1 yeni (araç havaya), O3 ve eski O1 pasif; F1/F2'den "colorful"
# çıktı. Aktif orta O1, O2 (ikisinde de araç). Eskiler hp.HORTUM_PASIF (_V1).
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

LF = es.LANDFALL
HT = hp.YAKLASMA_HORTUM
DOMAIN = "coastal_tornado_landfall"
PLACES = {"G1": ("Norveç", "a Norwegian fishing harbor of red wooden boathouses and white wooden houses"),
          "G2": ("İtalya", "an Italian harbor town of pastel houses climbing the hillside"),
          "G3": ("İrlanda", "an Irish harbor town of painted terraced houses"),
          "G4": ("Danimarka", "a Danish harbor town of brick canal houses"),
          "G5": ("Brezilya", "a Brazilian harbor town of colonial houses"),
          "G6": ("Hindistan", "an Indian harbor town of Portuguese-style houses")}
SCENES = {
    "G1": "Setting: red wooden boathouses on stilts along a fjord quay, white wooden houses and steep green mountains "
          "behind.",
    "G2": "Setting: tall pastel houses with green shutters stacked up a steep hillside above a small stone harbor.",
    "G3": "Setting: painted two-storey terraced houses with slate roofs along a stone harbor wall, a grey Atlantic sea.",
    "G4": "Setting: narrow brick houses with steep tiled roofs along a canal quay with old wooden boats.",
    "G5": "Setting: low whitewashed colonial houses with blue and yellow trim, a cobblestone seafront street, palm trees "
          "and fishing boats.",
    "G6": "Setting: weathered Portuguese-style houses with balconies and flat roofs, a seafront road, wooden fishing "
          "boats pulled up on the shore.",
}
OLD_SETTING = "Setting: colorful houses along a stone quay with small sailboats."
PASIF = {
    "G1_V1": "a Norwegian harbor town of colorful wooden fishing houses",
    "G2_V1": "an Italian harbor town of pastel houses climbing the hillside",
    "G3_V1": "an Irish harbor town of colorful terraced houses",
    "G4_V1": "a Danish harbor town of colorful canal houses",
    "G5_V1": "a Brazilian harbor town of colorful colonial houses",
    "G6_V1": "an Indian harbor town of colorful Portuguese-style houses",
    "STIL_V1": OLD_SETTING,
    "O1_V1": "The tornado shoves the {vehicle} sideways across the street and slams it into the far curb.",
    "O3_V1": "The tornado rips the moored sailboats out of the water and flings them onto the quay.",
    "F1_V1": "Right across from the window, the tornado tears the roof off a colorful house, the pieces flying past the "
             "camera.",
    "F2_V1": "Right across from the window, the tornado rips the whole front wall off a colorful house, furniture "
             "swirling up into the funnel.",
}
OPENING = ("The tornado makes landfall from the sea at {place}, crosses the seafront road and flips a parked car onto "
           "its side, then heads up the street toward the camera.")
PEOPLE = {3: "Three people run away from the tornado.", 5: "Five people run away from the tornado."}
VEHICLES = ("pickup truck", "delivery van", "SUV")
MIDS = {
    "O1": "The tornado lifts the {vehicle} off the street, spins it through the air and smashes it down onto the quay.",
    "O2": "The tornado lifts the {vehicle} off the quay and hurls it, in one piece, into the harbor water.",
}
FINALS = {
    "F1": "Right across from the window, the tornado tears the roof off a house, the pieces flying past the camera.",
    "F2": "Right across from the window, the tornado rips the whole front wall off a house, furniture swirling up into "
          "the funnel.",
    "F3": "Right below the window, the tornado hits the row of houses, roofs and balconies peeling off one after "
          "another.",
}
TAIL = ("Handheld footage filmed through an open upper-floor window across from the harbor street, high vantage; slight "
        "hand shake, the camera stays fixed, tilting only slightly, never descending, the tornado always in frame, the "
        "open window frame at one side; one continuous shot, no zoom, no cuts, no person or face close to the camera. "
        "{scene} All people are ordinary civilians in everyday clothes, no hazmat suits, natural light, never CGI. "
        "Everything moves in real time, never in slow motion, people run at full speed.")


def tail(g: str) -> str:
    return TAIL.format(scene=SCENES[g])
O2_WARNING = "⚠️ Araç savurma ortası (O2): videoda aracın tek parça kalıp kalmadığını kontrol et."
VEHICLE_WORDS = ("pickup", "truck", "van", "SUV", "car", "vehicle", "{")
TURKEY = ("Turkish", "Turkey", "Türk", "Istanbul", "İstanbul", "Izmir", "Bodrum")


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
    return asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": LF, "hortum_yaklasma": True,
                                                     "used_combos": [], "recent_topics": [], **extra}))


def build(seed: int) -> dict:
    reset()
    random.seed(seed)
    return gen()


def all_combos():
    for g in HT["geos"]:
        for ppl in (3, 5):
            for v in HT["vehicles"]:
                for m in HT["mids"]:
                    for f in HT["finals"]:
                        yield (g, ppl, v, m, f), hp.hortum_prompt(g, ppl, m, v, f)


class TestTexts(_Quiet):
    def test_verbatim_texts(self):
        self.assertEqual(hp.HORTUM_MODE_LABEL, "⭐ Hit kalıbı · Yaklaşma (hortum)")
        self.assertEqual(hp.HORTUM_EVENTS, (LF,))
        self.assertEqual({g: (HT["geos"][g]["name"], HT["geos"][g]["place"]) for g in HT["geos"]}, PLACES)
        for g, (_, place) in PLACES.items():
            self.assertEqual(hp.hortum_opening(g), OPENING.format(place=place))
        for n, text in PEOPLE.items():
            self.assertEqual(hp.hortum_people(n), text)
        for n in (2, 4, 6):
            with self.assertRaises(es.StructureError):
                hp.hortum_people(n)
        self.assertEqual(HT["vehicles"], VEHICLES)
        self.assertEqual(HT["mids"], MIDS)
        self.assertEqual(HT["finals"], FINALS)
        self.assertEqual(HT["vehicle_mids"], ("O1", "O2"))
        for g in PLACES:
            self.assertEqual(hp.hortum_tail(g), tail(g))
            self.assertEqual(HT["geos"][g]["scene"], SCENES[g])
            self.assertIn("high vantage; slight hand shake, the camera stays fixed, tilting only slightly, never "
                          "descending, the tornado always in frame, the open window frame at one side; one continuous "
                          f"shot, no zoom, no cuts, no person or face close to the camera. {SCENES[g]} All people",
                          tail(g))   # sahne cümlesi kamera cümlesinin hemen arkasında
            self.assertNotIn("colorful", PLACES[g][1] + SCENES[g])
        self.assertEqual(hp.HORTUM_PASIF, PASIF)
        self.assertEqual(hp.HORTUM_O2_WARNING, O2_WARNING)
        self.assertEqual(hp.HORTUM_GEO_SEED, ("G3",))
        self.assertEqual((hp.HORTUM_GEO_BLOCK, hp.HORTUM_VEHICLE_BLOCK, hp.HORTUM_MID_BLOCK, hp.HORTUM_FINAL_BLOCK),
                         (3, 2, 1, 1))
        self.assertEqual((hp.HORTUM_MAX_WORDS, hp.HORTUM_MAX_CHARS), (230, 1400))
        for _, place in PLACES.values():
            for bad in TURKEY:
                self.assertNotIn(bad, place)

    def test_passive_not_active(self):
        """15 Kas: eski sabit sahne STIL_V1, eski O1 ve O3 sadece pasif kayıtta; aktif havuzda / stil ekinde yok."""
        self.assertEqual(list(HT["mids"]), ["O1", "O2"])
        self.assertNotIn("O3", HT["mids"])
        self.assertNotIn(PASIF["O1_V1"], HT["mids"].values())
        self.assertNotIn(PASIF["O3_V1"], HT["mids"].values())
        self.assertNotIn(OLD_SETTING, HT["tail"])
        self.assertEqual(hp.HORTUM_PASIF["STIL_V1"], OLD_SETTING)
        self.assertIn("colorful houses along a stone quay", hp.HORTUM_FORBIDDEN)
        # G2 İtalya yer metni 15 Kas talimatında eskisiyle aynı kaldı (G2_V1 = G2): bilinçli istisna
        self.assertEqual(PASIF["G2_V1"], PLACES["G2"][1])
        for key in ("F1_V1", "F2_V1", *[f"G{i}_V1" for i in (1, 3, 4, 5, 6)]):
            self.assertNotIn(PASIF[key], json.dumps(HT, ensure_ascii=False))
        with self.assertRaises(es.StructureError):
            hp.hortum_mid("O3", "SUV")

    def test_vehicle_fill(self):
        """{vehicle} O1/O2'de doğru dolu; iki ortada da araç var."""
        self.assertEqual(HT["vehicle_mids"], tuple(HT["mids"]))
        for v in VEHICLES:
            for m in ("O1", "O2"):
                self.assertEqual(hp.hortum_mid(m, v), MIDS[m].format(vehicle=v))
                self.assertIn(f"the {v} ", hp.hortum_mid(m, v))
                self.assertNotIn("{", hp.hortum_mid(m, v))
        for m in ("O1", "O2"):
            with self.assertRaises(es.StructureError):
                hp.hortum_mid(m, None)
            with self.assertRaises(es.StructureError):
                hp.hortum_mid(m, "white van")   # bu modun havuzunda değil
        for bad in ("O3", "O4", "C1", "H1"):
            with self.assertRaises(es.StructureError):
                hp.hortum_mid(bad, "SUV")
        for bad in ("F4", "E1", "J1"):
            with self.assertRaises(es.StructureError):
                hp.hortum_final(bad)

    def test_all_combos_within_limits(self):
        """Coğrafya × kişi × araç × orta × final: hepsi ≤ 230 kelime, ≤ 1400 karakter + metin kuralları."""
        n, over, longest = 0, [], (0, 0, None)
        for key, p in all_combos():
            n += 1
            g, ppl, v, m, f = key
            w, c = len(p.split()), len(p)
            longest = max(longest, (w, c, key))
            if w > hp.HORTUM_MAX_WORDS or c > hp.HORTUM_MAX_CHARS:
                over.append((key, w, c))
            self.assertEqual(sum(pl in p for _, pl in PLACES.values()), 1, key)
            self.assertIn(PLACES[g][1], p)
            self.assertEqual(sum(sc in p for sc in SCENES.values()), 1, key)
            self.assertIn(SCENES[g], p)
            for bad in TURKEY + ("Full action", "Until the last frame", sk.FULL_MOTION, OLD_SETTING,
                                 "colorful houses along a stone quay"):
                self.assertNotIn(bad, p)
            for need in ("high vantage", "open upper-floor window"):
                self.assertIn(need, p)
            self.assertEqual(hp.hortum_camera_issues(p, g), [], key)
            expected = (f"0-4s: {OPENING.format(place=PLACES[g][1])} {PEOPLE[ppl]} 4-9s: "
                        f"{MIDS[m].format(vehicle=v)} 9-15s: {FINALS[f]} {tail(g)}")
            self.assertEqual(p, expected, key)   # sıra: açılış + insan + orta + final + stil eki
            opening = p.split(" 4-9s: ")[0]
            self.assertIn("makes landfall from the sea", opening)
            self.assertIn("toward the camera", opening)
            mid_part = p.split(" 4-9s: ")[1].split(" 9-15s: ")[0]
            self.assertIn(f"the {v} ", mid_part)
            self.assertEqual(sum(f"the {x} " in mid_part for x in VEHICLES), 1, key)
        self.assertEqual(n, 6 * 2 * 3 * 2 * 3)   # 216 (coğrafya × kişi × araç × orta × final)
        self.assertEqual(longest[:2], (193, 1139))   # G1 + pickup truck + O1 + F2
        self.assertEqual(over, [], f"en uzun: {longest}")
        self.assertLessEqual(longest[:2], (230, 1400))

    def test_sentences_only_in_this_mode(self):
        marks = ["makes landfall from the sea at", "crosses the seafront road and flips a parked car onto its side",
                 "then heads up the street toward the camera.", *PEOPLE.values(),
                 *[t.split("{vehicle}")[1] for t in MIDS.values()], *FINALS.values(),
                 "Handheld footage filmed through an open upper-floor window across from the harbor street",
                 *SCENES.values(), *[p for _, p in PLACES.values()]]
        # bilinçli ortak: "the open window frame at one side" normal pencere kadrajının (frame_axis) ifadesi. 15 Kas:
        # O1 artık normal karaya vurur C1 ile aynı değil (eski O1 = C1, pasif O1_V1)
        pools = json.dumps({e: {s: {k: v["text"] for k, v in b[s].items()} for s in ("slice_2", "slice_3")}
                            for e, b in es.EVENT_BEATS.items()}, ensure_ascii=False)
        others = (pools + json.dumps(hp.HIT_PROMPTS, ensure_ascii=False)
                  + json.dumps(hp.YAKLASMA_ATES_HORTUMU, default=str, ensure_ascii=False)
                  + json.dumps(hp.DALGA_24EYLUL, default=str, ensure_ascii=False)
                  + json.dumps(hp.YAKLASMA_KUL_BULUTU, default=str, ensure_ascii=False)
                  + json.dumps(hp.KUL_PASIF, default=str, ensure_ascii=False)
                  + json.dumps(hp.YAKLASMA_ORMAN, default=str, ensure_ascii=False)
                  + json.dumps(hp.ORMAN_PASIF, default=str, ensure_ascii=False)
                  + json.dumps(hp.YAKLASMA_HELIKOPTER, default=str, ensure_ascii=False)
                  + json.dumps(hp.YAKLASMA_CADDE, default=str, ensure_ascii=False)
                  + json.dumps(es.EVENT_KEY_VISUAL, ensure_ascii=False))
        for ev in ps.active_events():
            for seed in range(1, 6):
                others += json.dumps(ps.snapshot_event(ev, seed), ensure_ascii=False)
        for m in marks:
            self.assertNotIn(m, others, m)


class TestHortumMode(_Quiet):
    def _check(self, d):
        sc, st = d["scenes"][0], d["structure"]
        tb = st["hortum_yaklasma"]
        prompt = sc["prompt"]
        self.assertIn(tb["geo"], PLACES)
        self.assertEqual(sum(pl in prompt for _, pl in PLACES.values()), 1)
        self.assertTrue(prompt.startswith(f"0-4s: {hp.hortum_opening(tb['geo'])} {PEOPLE[tb['people']]} 4-9s: "))
        self.assertIn(tb["vehicle"], VEHICLES)
        self.assertIn(tb["mid"], MIDS)
        self.assertIn(tb["final"], FINALS)
        mid_text = hp.hortum_mid(tb["mid"], tb["vehicle"])
        self.assertIn(f" 4-9s: {mid_text} 9-15s: {FINALS[tb['final']]} Handheld footage", prompt)
        for lab in ("0-4s: ", " 4-9s: ", " 9-15s: "):
            self.assertIn(lab, prompt)
        for bad in ("Full action", "Until the last frame", sk.FULL_MOTION) + TURKEY:
            self.assertNotIn(bad, prompt)
        self.assertTrue(prompt.endswith(" " + tail(tb["geo"])))
        self.assertEqual(sc["style_suffix"], tail(tb["geo"]))
        self.assertIn(SCENES[tb["geo"]], prompt)
        self.assertEqual(sum(x in prompt for x in SCENES.values()), 1)
        self.assertNotIn(OLD_SETTING, prompt)
        self.assertNotIn("colorful", prompt)
        self.assertIn(tb["mid"], ("O1", "O2"))   # O3 hiç seçilmez
        self.assertIn(f"the {tb['vehicle']} ", prompt)   # her üretimde araç var
        self.assertLessEqual(len(prompt.split()), 230)
        self.assertLessEqual(len(prompt), 1400)
        self.assertIn(f"#{tb['mid']}+{tb['final']}|", d["combo_key"])
        for slot in ("slice_2", "slice_3"):   # normal karaya vurur havuzu (C*/E*) metni yok
            for bid in es.EVENT_BEATS[LF][slot]:
                self.assertNotIn(es.beat_text(LF, slot, bid)[4:], prompt)
        self.assertNotIn(es.EVENT_KEY_VISUAL[LF], prompt)
        self.assertEqual(cp.submit_issues(st, {"prompt": prompt, "story": sc["story"],
                                               "style_suffix": sc["style_suffix"]}), [])
        return tb

    def test_first_production_never_g3(self):
        for seed in range(1, 51):
            tb = self._check(build(seed))
            self.assertNotEqual(tb["geo"], "G3", seed)
        for s in range(40):   # Notion'da bu modun kaydı yoksa da G3 elenir
            self.assertNotEqual(hp.hortum_choose_geo([], random.Random(s)), "G3")

    def test_50_seeds_every_mid_and_final(self):
        mids, finals, geos = set(), set(), set()
        for seed in range(1, 51):
            reset()
            random.seed(seed)
            runs = []
            for i in range(3):
                with self.subTest(seed=seed, i=i):
                    runs.append(self._check(gen()))
            for r in runs:
                mids.add(r["mid"])
                finals.add(r["final"])
                geos.add(r["geo"])
            for key in ("mid", "final"):
                vals = [r[key] for r in runs]
                self.assertTrue(all(a != b for a, b in zip(vals, vals[1:])), (seed, key, vals))
        self.assertEqual(mids, {"O1", "O2"})
        self.assertEqual(finals, {"F1", "F2", "F3"})
        self.assertEqual(geos, set(PLACES) - {"G3"})   # G3 tohum: ilk 3 üretimde gelmez
        self.assertIsNone(es.HIT_OVERRIDE.get())

    def test_consecutive_lru(self):
        """Coğrafya ardışık 3 üretimde tekrar etmez; araç son 2 (araçlı ortalarda); orta ve final arka arkaya yok."""
        g3 = []
        for seed in range(1, 16):
            reset()
            random.seed(seed)
            runs = [self._check(gen()) for _ in range(9)]
            geos = ["G3"] + [r["geo"] for r in runs]   # G3 tohum
            for i in range(1, len(geos)):
                self.assertNotIn(geos[i], geos[max(0, i - 3):i], (seed, geos))
            for key in ("mid", "final"):
                vals = [r[key] for r in runs]
                for i in range(1, len(vals)):
                    self.assertNotEqual(vals[i], vals[i - 1], (seed, key, vals))
            used = [r["vehicle"] for r in runs]   # 15 Kas: araç her üretimde var, geçmiş her üretimde ilerler
            for i in range(len(used)):
                self.assertNotIn(used[i], used[max(0, i - 2):i], (seed, used))
            self.assertTrue({r["people"] for r in runs} <= {3, 5})
            g3.append("G3" in geos[1:])
        self.assertTrue(any(g3))   # G3 sadece ilk üretimlerde elenir, sonra serbest

    def test_history_sources(self):
        def combo(tag):
            return f"{DOMAIN}|none|{LF.lower()}|beachfront promenade##{tag}|bystander_handheld"
        reset()
        hist = [combo("O1+F1"), combo("C1+E1"), combo("O3+F2")]
        for s in range(30):   # 15 Kas: geçmişteki eski O3 kaydı hata vermez (aktif havuzda yok, iki orta da serbest)
            self.assertIn(hp.hortum_choose_mid(hist, random.Random(s)), ("O1", "O2"))
            self.assertIn(hp.hortum_choose_final(hist, random.Random(s)), ("F1", "F3"))   # son 1: F2 elenir
        self.assertEqual({hp.hortum_choose_mid(hist, random.Random(s)) for s in range(30)}, {"O1", "O2"})
        hist2 = [combo("O2+F1"), combo("O1+F3")]   # eski O1 kaydı: O1 son 1 olarak elenir
        for s in range(30):
            self.assertEqual(hp.hortum_choose_mid(hist2, random.Random(s)), "O2")
        recs = [{"eksenler": json.dumps({"event": LF, "axes": {"mod": "hortum_yaklasma", "cografya": g, "arac": v}})}
                for g, v in (("G1", "SUV"), ("G2", "delivery van"), ("G4", "SUV"))] + [{"eksenler": "x"}]
        recs.append({"eksenler": json.dumps({"event": es.HELICOPTER, "axes": {"mod": "heli_yaklasma",
                                                                              "cografya": "G5", "arac": "pickup truck"}})})
        recs.append({"eksenler": json.dumps({"event": LF, "axes": {"cografya": "G6", "arac": "pickup truck"}})})
        self.assertEqual(hp.hortum_axes_history(recs, "cografya"), ["G1", "G2", "G4"])
        self.assertEqual(hp.hortum_axes_history(recs, "arac"), ["SUV", "delivery van", "SUV"])
        self.assertIsNone(hp.hortum_axes_history(None, "arac"))
        for seed in range(1, 11):
            reset()
            random.seed(seed)
            d = gen(axes_loader=lambda dom: recs)
            tb = d["structure"]["hortum_yaklasma"]
            self.assertIn(tb["geo"], ("G3", "G5", "G6"))   # son 3 (G1, G2, G4) elenir; kayıt varken G3 serbest
            self.assertEqual(tb["vehicle"], "pickup truck")
            axes = json.loads(d["axes_json"])["axes"]
            self.assertEqual((axes["mod"], axes["cografya"]), ("hortum_yaklasma", tb["geo"]))
            self.assertEqual(axes["arac"], tb["vehicle"])   # 15 Kas: Notion'a araç her üretimde yazılır

    def test_kie_final_check(self):
        with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT çağrıldı"))) as gpt, \
             patch.object(pg, "_get_openai_client", side_effect=AssertionError("GPT istemcisi istendi")):
            d = build(7)
        gpt.assert_not_called()
        sc, st = d["scenes"][0], d["structure"]
        tb = st["hortum_yaklasma"]
        info = {"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"]}
        self.assertEqual(cp.submit_issues(st, info), [])
        p0 = sc["prompt"]
        place = PLACES[tb["geo"]][1]
        other = PLACES["G3" if tb["geo"] != "G3" else "G1"][1]
        scene = SCENES[tb["geo"]]
        other_scene = SCENES["G3" if tb["geo"] != "G3" else "G1"]
        for old_s, new_s in ((scene, ""), (scene, other_scene), (scene, OLD_SETTING),
                             ("never CGI.", "never CGI. A row of colorful houses along a stone quay."),
                             ("high vantage", "low vantage"),
                             ("open upper-floor window", "ground-floor doorway"),
                             (place, "a Turkish harbor town of colorful houses"),
                             (place, other),
                             ("never CGI.", f"never CGI. {sk.FULL_MOTION}"),
                             ("people run at full speed.", "people run at full speed. Full action from the very first "
                                                           "frame to the last."),
                             ("people run at full speed.", "people run at full speed. Until the last frame, the "
                                                           "tornado keeps tearing through the street."),
                             ("4-9s: ", "")):
            bad_prompt = p0.replace(old_s, new_s, 1)
            self.assertNotEqual(bad_prompt, p0, old_s)
            self.assertTrue(hp.hortum_issues(st, {**info, "prompt": bad_prompt}), new_s)
            self.assertTrue(cp.submit_issues(st, {**info, "prompt": bad_prompt}), new_s)
        # metin kuralları ayrıca (yeniden kurulum eşitliğinden bağımsız) kontrol edilir
        self.assertIn('"high vantage" eksik', hp.hortum_camera_issues(p0.replace("high vantage", "vantage"), tb["geo"]))
        self.assertIn('"open upper-floor window" eksik',
                      hp.hortum_camera_issues(p0.replace("open upper-floor window", "window"), tb["geo"]))
        self.assertIn("G1-G6 yer metni yok", hp.hortum_camera_issues(p0.replace(place, "a harbor town"), tb["geo"]))
        self.assertIn("G1-G6 sahne cümlesi yok", hp.hortum_camera_issues(p0.replace(scene, ""), tb["geo"]))
        self.assertTrue(hp.hortum_camera_issues(p0.replace(scene, other_scene), tb["geo"]))
        self.assertIn("bu modda olmayan ifade var: colorful houses along a stone quay",
                      hp.hortum_camera_issues(p0.replace(scene, OLD_SETTING), tb["geo"]))
        self.assertTrue(hp.hortum_camera_issues(p0 + " Full action from the very first frame to the last.", tb["geo"]))
        self.assertTrue(hp.hortum_camera_issues(p0 + " Until the last frame, it rages.", tb["geo"]))
        for bad in ({"geo": "G7"}, {"geo": "L1"}, {"mid": "C1"}, {"final": "E1"}, {"people": 4}, {"mid": "O4"},
                    {"mid": "O3"},
                    {"final": "F4"}, {"mid": "O1", "vehicle": None}):
            self.assertTrue(cp.submit_issues({**st, "hortum_yaklasma": {**tb, **bad}}, info), bad)
        self.assertTrue(cp.submit_issues(st, {**info, "style_suffix": "x"}))
        story = asyncio.run(cp.rewrite_structured(st, "test", AsyncMock(side_effect=AssertionError("GPT"))))
        self.assertEqual(story, sc["story"])
        # Kie'ye gitmeden ihlal yakalanır: apply içindeki son denetim de aynı fonksiyon
        with patch.object(hp, "HORTUM_REQUIRED", ("high vantage", "open upper-floor window", "olmayan ifade")):
            reset()
            random.seed(7)
            with self.assertRaises(es.StructureError):
                gen()

    def _approval(self, d):
        sc, st = d["scenes"][0], d["structure"]
        tb = st["hortum_yaklasma"]
        lines = tb["lines"].split("\n")
        self.assertEqual(lines[0], "Mod: ⭐ Hit kalıbı · Yaklaşma (hortum)")
        self.assertEqual(lines[1], f"Coğrafya: {tb['geo']} {PLACES[tb['geo']][0]}")
        self.assertEqual(lines[2], f"Sahne: «{SCENES[tb['geo']]}»")   # 15 Kas: Coğrafya satırının altında
        self.assertEqual(lines[3], f"Araç: {tb['vehicle']}")
        self.assertEqual(lines[4], f"Orta (4-9s): {tb['mid']} «{hp.hortum_mid(tb['mid'], tb['vehicle'])}»")
        self.assertEqual(lines[5], f"Final (9-15s): {tb['final']} «{FINALS[tb['final']]}»")
        self.assertEqual(lines[6], "Kamera: sabit (hafifçe eğilir, açık üst kat penceresi)")
        self.assertEqual(lines[7], f"Kelime: {len(sc['prompt'].split())} (en fazla 230) · karakter: "
                                   f"{len(sc['prompt'])} (en fazla 1400)")
        if tb["mid"] == "O2":
            self.assertEqual(lines[8], O2_WARNING)
            self.assertEqual(len(lines), 9)
        else:
            self.assertNotIn(O2_WARNING, tb["lines"])
            self.assertEqual(len(lines), 8)
        shown = sections_to_text(format_generation(d["trace"])) + "\n" + st["axes_line"]
        sel, _, rest = shown.partition("🔍 2.")
        story = rest.split("🔍 3. Hikâye\n", 1)[1]
        for part in (hp.hortum_opening(tb["geo"]), hp.hortum_mid(tb["mid"], tb["vehicle"]), FINALS[tb["final"]]):
            self.assertIn(part, sc["prompt"])
            self.assertIn(part, sel)
            self.assertIn(part, story)
        self.assertIn("Mod: ⭐ Hit kalıbı · Yaklaşma (hortum)", sel)
        self.assertIn(f"orta={tb['mid']}", st["axes_line"])
        self.assertIn(f"final={tb['final']}", st["axes_line"])
        self.assertIn(f"coğrafya={tb['geo']} {PLACES[tb['geo']][0]}", st["axes_line"])
        self.assertIn(f"araç={tb['vehicle']}", st["axes_line"])
        for absent in (st["spec"]["key_visual"], "kamera modu=A", "kamera modu=B"):
            self.assertNotIn(absent, shown)
        _, body = format_final_prompt({"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"],
                                       "hit_lines": tb["lines"], "environment": st["environment"]})
        self.assertIn("\nMod: ⭐ Hit kalıbı · Yaklaşma (hortum)\n", body)
        self.assertIn("\n\n" + sc["prompt"], body)
        return tb["mid"]

    def test_approval_lines_and_display(self):
        seen = set()
        for seed in range(1, 40):
            seen.add(self._approval(build(seed)))
            if seen == {"O1", "O2"}:
                break
        self.assertEqual(seen, {"O1", "O2"})

    def test_40_seeds_never_o3_and_vehicle_always(self):
        for seed in range(1, 41):
            d = build(seed)
            tb = self._check(d)
            self.assertNotEqual(tb["mid"], "O3", seed)
            self.assertIn(tb["vehicle"], VEHICLES)
            self.assertEqual(json.loads(d["axes_json"])["axes"]["arac"], tb["vehicle"]) if d.get("axes_json") else None
        reset()
        random.seed(3)
        runs = [self._check(gen()) for _ in range(6)]
        self.assertEqual(hp._HORTUM_VEHICLE_MEMORY, [r["vehicle"] for r in runs])   # her üretimde ilerler

    def test_normal_landfall_untouched(self):
        for seed in range(1, 6):
            reset()
            random.seed(seed)
            d = asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": LF, "used_combos": [],
                                                         "recent_topics": []}))
            self.assertNotIn("hortum_yaklasma", d["structure"])
            self.assertNotIn("mode_label", d["trace"])
            p = d["scenes"][0]["prompt"]
            for x in ("makes landfall from the sea at", "open upper-floor window", "people run away from the tornado.",
                      "Setting: colorful houses along a stone quay", *[pl for _, pl in PLACES.values()],
                      *SCENES.values()):
                self.assertNotIn(x, p)
            self.assertNotRegex(d["combo_key"], r"#O\d\+F\d\|")


class TestHortumPipelineAndBot(_Quiet):
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
                return await orig(**kw, hortum_yaklasma=True)
            with patch.object(main, "run_pipeline", run_with):
                r = t.run_pipe(gen=AsyncMock(side_effect=fake_gen), reporter=rep, event=LF)
        finally:
            t.doCleanups()
        self.assertTrue(r["success"], r)
        self.assertIs(seen["config"]["hortum_yaklasma"], True)
        approve = [c[1] for c in rep.calls if c[0] == "approve"]
        self.assertEqual(len(approve), 1)
        info = approve[0]
        self.assertTrue(info["hit_lines"].startswith("Mod: ⭐ Hit kalıbı · Yaklaşma (hortum)\nCoğrafya: G"))
        self.assertEqual(t.create.await_args.args[1], info["prompt"])   # Kie'ye giden = onaydaki

    def test_bot_button_and_flow(self):
        import bot
        from test_tur29_infra import _context, _update
        di = str(bot.DOMAIN_KEYS.index(DOMAIN))
        ei = str(bot.domain_events(DOMAIN).index(LF))
        ctx = _context()
        upd = _update(data=f"uret:e:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, ctx))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        labels = [b.text for r in kb.inline_keyboard for b in r]
        self.assertEqual(labels, ["✅ Üret", "❌ İptal", "⭐ Hit kalıbı · Yaklaşma"])
        self.assertEqual([len(r) for r in kb.inline_keyboard], [2, 1])   # buton Üret/İptal'in altında
        upd = _update(data=f"uret:ty:{di}:{ei}")
        asyncio.run(bot.on_callback(upd, ctx))
        text = upd.callback_query.edit_message_text.await_args.args[0]
        self.assertIn("Mod: ⭐ Hit kalıbı · Yaklaşma (hortum)", text)
        upd = _update(data=f"uret:tyok:{di}:{ei}")
        runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
        with patch.object(bot.pipeline, "run_pipeline", runner), patch.object(bot, "_production_lock", asyncio.Lock()):
            asyncio.run(bot.on_callback(upd, ctx))
        kw = runner.await_args.kwargs
        self.assertEqual((kw["event"], kw["hortum_yaklasma"]), (LF, True))
        for other in ("heli_yaklasma", "kul_yaklasma", "orman_yaklasma", "dalga24", "approach_env", "hit_env"):
            self.assertNotIn(other, kw)
        self.assertTrue(kw["reporter"].needs_approval)
        # aynı kategorinin diğer olaylarında bu buton yok
        for i, e in enumerate(bot.domain_events(DOMAIN)):
            if e == LF:
                continue
            upd = _update(data=f"uret:e:{di}:{i}")
            asyncio.run(bot.on_callback(upd, ctx))
            kw = upd.callback_query.edit_message_text.await_args.kwargs
            if "reply_markup" in kw:
                cbs = [b.callback_data for r in kw["reply_markup"].inline_keyboard for b in r]
                self.assertFalse(any(c.startswith("uret:ty") for c in cbs), e)
        self.assertIsNone(bot.parse_hortum(di, str(next(i for i, e in enumerate(bot.domain_events(DOMAIN))
                                                        if e != LF))))


if __name__ == "__main__":
    unittest.main()
