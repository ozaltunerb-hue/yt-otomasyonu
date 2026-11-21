# 15 Kas 2026 (4), Bahadır: yeni kategori "🌀 Kasırga", tek olay "🌀 Kasırga kıyı kasabasını döver"
# (core/hit_prompts.py KASIRGA). Odak rüzgâr: hortum (huni) yok, dev dalga/sel dalgası yok. Altın kural: video asla
# yapay görünmez (kısa, sade, gerçek görüntülere benzer prompt). DONMA_FIRTINA ile aynı düzen: GPT yok, hikâye koddan
# birebir, zaman etiketleri var, normal hattın sahnesi yok (olay yapılandırılmış havuzda değil). Coğrafya G1-G6 (son 3),
# araç son 2, orta O1-O2 / final F1-F3 son 1, kişi 4/5. Diğer 20 olay/kategori ve bütün modlar birebir aynı (40 tohum).
# Ağ yok.
# 15 Kas (5): ilk üretim (Florida, O2 + F2) 7/10, kasırga hissi yoktu (yağmur yok, aydınlık gök, hafif eğilen palmiye,
# "heavy hand shake" kamerayı döndürdü, palmiye finali okunmadı). Kategori 5 şiddet + sağanak + kaos, O3 (kökünden
# sökülen ağaç), yeni F2 (dükkân cephesi), kamera sabit; G5 "street" tekrarı düzeldi. Eski metinler hp.KASIRGA_PASIF.
# 21 Kas (2), kasırga v2: açılışa "one palm torn out by its roots and hurled across the road", F2 dükkânın ön duvarı
# yerine elektrik direği (eskiler OPENING_V2 / F2_V2 pasif). Seçim sırası (G, araç, O, F, kişi) aynı tohumlarda aynı;
# 40 tohum kaydı v1 fixture (kasirga_v1_runs_40.json, KASIRGA_V1_SHA256) ve v2 fixture (KASIRGA_V2_SHA256).
# 21 Kas (3), kasırga v3: stil ekine "never pans" + sabit balkon korkuluğu, O2 yalnız tente (metal sac çıktı) ve
# ön camı kırar (eskiler TAIL_V3 / CAMERA_V3 / CAMERA_LINE_V3 / O2_V3 / VERSION_LINE_V3 pasif). Seçim sırası aynı
# tohumlarda aynı; canlı 40 tohum kaydı v3 fixture (kasirga_v3_runs_40.json, KASIRGA_SHA256).
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
import core.caption as cap   # noqa: E402
import core.creative_pipeline as cp   # noqa: E402
import core.hit_prompts as hp   # noqa: E402
import core.prompt_generator as pg   # noqa: E402
import core.skeleton_pipeline as sk   # noqa: E402
import prompt_snapshot as ps   # noqa: E402
from core.trace_format import format_final_prompt, format_generation, sections_to_text   # noqa: E402

KS = hp.KASIRGA
EVENT = "Hurricane winds batter a coastal town"
DOMAIN = "hurricane_disasters"
PLACES = {"G1": ("ABD", "a Florida beach town of low pastel houses"),
          "G2": ("Filipinler", "a Philippine coastal town of tin-roofed houses"),
          "G3": ("Meksika", "a Mexican Caribbean town of colorful concrete houses"),
          "G4": ("Hindistan", "an Indian coastal town of old concrete buildings"),
          "G5": ("Küba", "a Cuban seaside town of faded colonial houses"),
          "G6": ("Japonya", "a Japanese coastal town of low tiled houses")}
# Talimattaki metinler kelimesi kelimesine (zaman etiketleri dahil)
OPENING = ("0-4s: Category 5 hurricane winds and torrential sideways rain hammer a street in {place}, palm trees bent "
           "almost flat, one palm torn out by its roots and hurled across the road, branches, roof sheets and debris "
           "flying everywhere in total chaos.")
PEOPLE = {4: "Four people struggle along the sidewalk toward the camera, bent double against the wind, clinging to "
             "railings, one knocked off his feet by a gust.",
          5: "Five people struggle along the sidewalk toward the camera, bent double against the wind, clinging to "
             "railings, one knocked off his feet by a gust."}
VEHICLES = ("pickup truck", "SUV", "small car")
MIDS = {
    "O1": "4-9s: A violent gust flips a parked {vehicle} onto its roof and sends it skidding across the wet road.",
    "O2": "4-9s: A shop awning rips loose and slams down onto a parked {vehicle}, smashing its windshield.",
    "O3": ("4-9s: A big tree is ripped out by its roots and crashes across the road onto a parked {vehicle}, crushing "
           "its roof."),
}
FINALS = {
    "F1": ("9-15s: Right across the street, the wind peels the whole roof off a house, metal sheets and tiles flying "
           "past the camera."),
    "F2": ("9-15s: Right across the street, a wooden power pole snaps at its base and crashes down across the road, "
           "live wires whipping and sparking."),
    "F3": "9-15s: Across the street, a large blank billboard rips loose and cartwheels down the road toward the camera.",
}
TAIL = ("Handheld footage shot by a person standing on a high balcony across the street, eye level, normal lens; the "
        "camera stays fixed on the street and never pans, shaking in the wind, rain streaking across the lens; a "
        "balcony railing stays fixed at the bottom of the frame the whole time; no zoom, no cuts. No tornado funnel, no "
        "flood waves. Bystanders wear everyday clothes. Raw natural light under a dark grey sky in pouring rain, never "
        "glossy or CGI. No readable signs or text. Everything moves in real time, never in slow motion.")
REQUIRED = ("Category 5", "torrential sideways rain", "normal lens", "stays fixed on the street", "pouring rain",
            "No tornado funnel")
FORBIDDEN = ("tornado", "funnel", "twister", "waterspout", "surge", "tsunami", "tidal", "flood wave", "pans to follow",
             "Full action", "Until the last frame", "heavy hand shake")
NEGATION = "No tornado funnel, no flood waves."
EVENT_LABEL = "🌀 Kasırga kıyı kasabasını döver"
CAMERA_LINE = ("Kamera: hit kamerası (yüksek balkon, normal lens, sabit, dönmez, korkuluk altta sabit, rüzgârla sarsılır, "
               "lenste yağmur)")
WARNING = ("⚠️ Gerçekçilik: gökte huni yok mu, sel dalgası yok mu, insanlar rüzgârla gerçekten boğuşuyor mu, video "
           "yapay görünüyor mu? Sağanak yağmur, karanlık gökyüzü ve kaos var mı?")
# 15 Kas (5): değişen eski metinler pasif kayıtta (hp.KASIRGA_PASIF) birebir
PASIF = {
    "G5_V1": "a Cuban seaside street of faded colonial houses",
    "OPENING_V1": ("Hurricane winds and sideways rain hammer a street in {place}, palm trees bending almost flat as "
                   "metal roof sheets tear loose and fly across the road."),
    "PEOPLE_V1": {4: "Four people struggle along the sidewalk toward the camera, bent double against the wind, "
                     "clinging to railings.",
                  5: "Five people struggle along the sidewalk toward the camera, bent double against the wind, "
                     "clinging to railings."},
    "F2_V1": ("Right below the balcony, a tall palm tree snaps in half and crashes onto the parked cars, debris "
              "slamming into the balcony railing."),
    "VEHICLE_MIDS_V1": ("O1", "O2"),
    "CAMERA_V1": "heavy hand shake from the wind, rain streaking across the lens; no zoom, no cuts",
    "TAIL_V1": ("Handheld footage shot by a person standing on a high balcony across the street, eye level, normal "
                "lens; heavy hand shake from the wind, rain streaking across the lens; no zoom, no cuts. No tornado "
                "funnel, no flood waves. Bystanders wear everyday clothes. Raw natural light under a dark storm sky, "
                "never glossy or CGI. No readable signs or text. Everything moves in real time, never in slow motion."),
    "CAMERA_LINE_V1": "Kamera: hit kamerası (yüksek balkon, normal lens, rüzgârla sarsılan el, lenste yağmur)",
    "WARNING_V1": ("⚠️ Gerçekçilik: gökte huni yok mu, sel dalgası yok mu, insanlar rüzgârla gerçekten boğuşuyor mu, "
                   "video yapay görünüyor mu?"),
    "WEATHER_V1": "kasırga rüzgârı ve yatay yağmur (stil ekinde raw natural light under a dark storm sky)",
    "CONFIRM_DESC_V1": ("Kasırga rüzgârı ve yatay yağmur kıyı kasabasının caddesini döver: palmiyeler yatar, çatı "
                        "sacları uçar. İnsanlar rüzgâra karşı boğuşarak kameraya doğru ilerler; park halindeki araç "
                        "devrilir ya da üstüne tente ve sac düşer; final caddenin karşısında ya da balkonun altında. "
                        "Huni yok, sel dalgası yok."),
    "REQUIRED_V1": ("Hurricane", "sideways rain", "normal lens", "No tornado funnel"),
    "SPOT_DISPLAY_V1": "High balcony across the street (hit kamerası, yüksek balkon, normal lens, rüzgârla sarsılan el)",
    "CAMERA_MODE_V1": "elde, rüzgârla sarsılan",
    # 21 Kas (2), kasırga v2
    "OPENING_V2": ("Category 5 hurricane winds and torrential sideways rain hammer a street in {place}, palm trees "
                   "bent almost flat, branches, roof sheets and debris flying everywhere in total chaos."),
    "F2_V2": ("Right across the street, the wind rips the entire front wall off a shop, glass and debris blasting past "
              "the camera."),
    # 21 Kas (3), kasırga v3
    "TAIL_V3": ("Handheld footage shot by a person standing on a high balcony across the street, eye level, normal "
                "lens; the camera stays fixed on the street, shaking in the wind, rain streaking across the lens; no "
                "zoom, no cuts. No tornado funnel, no flood waves. Bystanders wear everyday clothes. Raw natural light "
                "under a dark grey sky in pouring rain, never glossy or CGI. No readable signs or text. Everything "
                "moves in real time, never in slow motion."),
    "CAMERA_V3": "the camera stays fixed on the street, shaking in the wind, rain streaking across the lens; no zoom, no cuts",
    "CAMERA_LINE_V3": "Kamera: hit kamerası (yüksek balkon, normal lens, sabit, rüzgârla sarsılır, lenste yağmur)",
    "O2_V3": ("A shop awning and a sheet of metal roofing rip loose and slam down onto a parked {vehicle}, smashing its "
              "windows."),
    "VERSION_LINE_V3": "Sürüm: kasırga v2 (palmiye kökünden, F2 direk)",
}
VERSION_LINE = "Sürüm: kasırga v3 (sabit korkuluk, O2 tente)"
# Aktif prompt'ta asla çıkmaması gereken eski parçalar
OLD_PROMPT_BITS_V2 = [PASIF["G5_V1"], *PASIF["OPENING_V1"].split("{place}"), *PASIF["PEOPLE_V1"].values(),
                   PASIF["F2_V1"], PASIF["CAMERA_V1"], PASIF["TAIL_V1"], "Raw natural light under a dark storm sky",
                   "a tall palm tree snaps in half", "a Cuban seaside street",
                   *[PASIF["OPENING_V2"].format(place=p) for _, p in PLACES.values()], PASIF["F2_V2"],
                   "palm trees bent almost flat, branches", "rips the entire front wall off a shop"]
# 21 Kas (3) v3: + eski stil eki / kamera / O2
OLD_PROMPT_BITS = OLD_PROMPT_BITS_V2 + [PASIF["TAIL_V3"], PASIF["CAMERA_V3"],
                                        *[PASIF["O2_V3"].format(vehicle=v) for v in VEHICLES],
                                        "a sheet of metal roofing", "smashing its windows", "lens; no zoom, no cuts"]
# v2'de kasırga çıktılarında hiç geçmeyecek kelimeler (büyük/küçük harf fark etmez); v3: + "metal roofing"
NO_WALL_WORDS_V2 = ("front wall", "facade")
NO_WALL_WORDS = NO_WALL_WORDS_V2 + ("metal roofing",)
FIXTURE_V1 = os.path.join(ROOT, "tests", "fixtures", "kasirga_v1_runs_40.json")
FIXTURE_V2 = os.path.join(ROOT, "tests", "fixtures", "kasirga_v2_runs_40.json")
FIXTURE_V3 = os.path.join(ROOT, "tests", "fixtures", "kasirga_v3_runs_40.json")
# 🌀 Kasırga 40 tohum kaydı (🎲 Rastgele; prompt / hikâye / stil eki / combo / eksenler, caption hariç)
KASIRGA_V1_SHA256 = "c96655d503dbad8716b754039b55ca1cf9f760c4dde22663edbc3c9fd16b21e6"   # 35411fc (v1, fixture)
KASIRGA_V2_SHA256 = "c3ebc747253c64e6ad1e505016a154fc961796ffdaa2e7104f5135377a8a7840"   # 21 Kas (2) v2 (fixture)
KASIRGA_SHA256 = "9e9b0103832b81e2b8afa1d0bc3c855c89981acd03800d156bad49c9665439db"      # 21 Kas (3) v3
# Diğer 19 olay (normal yol) + 12 mod + ❄️ Donduran fırtına, 40 tohum: değişiklikten ÖNCEKİ kodla (ed5a9ab) üretilen
# kaydın SHA-256'sı
OTHERS_SHA256 = "0f17e5f5bec700860e7bdff73111d8518d651936a1dd62e276dcbaa75f96f860"


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
    return asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": EVENT, "kasirga": True,
                                                     "used_combos": [], "recent_topics": [], **extra}))


def build(seed: int) -> dict:
    reset()
    random.seed(seed)
    return gen()


def expected(g, ppl, v, m, f) -> str:
    return f"{OPENING.format(place=PLACES[g][1])} {PEOPLE[ppl]} {MIDS[m].format(vehicle=v)} {FINALS[f]} {TAIL}"


def all_combos():
    for g in KS["geos"]:
        for ppl in (4, 5):
            for v in KS["vehicles"]:
                for m in KS["mids"]:
                    for f in KS["finals"]:
                        yield (g, ppl, v, m, f), hp.kasirga_prompt(g, ppl, m, v, f)


def others_snapshot() -> dict:
    """Diğer 19 olay (normal yol, prompt_snapshot) + 12 mod + ❄️ Donduran fırtına; 40 tohum. Caption (tohumsuz
    rastgele) çıkarılır."""
    def strip(js):
        try:
            d = json.loads(js)
        except (TypeError, ValueError):
            return js
        d.pop("caption", None)
        return d

    def mode_run(flags, ev, seed, domain=None):
        reset()
        random.seed(seed)
        try:
            with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT"))):
                d = asyncio.run(pg.generate_creative_prompts({"domain": domain, "event": ev, **flags,
                                                             "used_combos": [], "recent_topics": []}))
        except Exception as e:   # noqa: BLE001 - davranış kaydı
            return {"error": f"{type(e).__name__}: {e}"}
        sc = d["scenes"][0]
        return {"prompt": sc["prompt"], "story": sc["story"], "suffix": sc["style_suffix"], "combo": d["combo_key"],
                "axes": strip(d.get("axes_json", ""))}
    out = {"events": {ev: {str(s): ps.snapshot_event(ev, s) for s in range(1, 41)} for ev in ps.active_events()},
           "modes": {}}
    modes = [(f"hit:{e}", {"hit_env": e}, es.FIRE_TORNADO, None) for e in hp.HIT_ENVS[es.FIRE_TORNADO]]
    modes += [(f"yaklasma:{e}", {"approach_env": e}, es.FIRE_TORNADO, None) for e in hp.yaklasma_envs(es.FIRE_TORNADO)]
    modes += [("dalga24", {"dalga24": True}, es.TIDAL, None), ("kul", {"kul_yaklasma": True}, es.PYROCLASTIC, None),
              ("orman", {"orman_yaklasma": True}, es.WILDFIRE, None),
              ("heli", {"heli_yaklasma": True}, es.HELICOPTER, None),
              ("hortum", {"hortum_yaklasma": True}, es.LANDFALL, None),
              ("cadde", {"cadde_yaklasma": True}, es.AVENUE, None),
              ("donma", {"donma_firtina": True}, hp.DONMA_EVENT, hp.DONMA_DOMAIN)]
    for name, flags, ev, dom in modes:
        if name == "orman":
            # 20 Kas 2026: orman Yaklaşma v4 bilerek değişti. Bu kilit diğer olay/modlar içindir; orman kaydı v3
            # (3c0369c) fixture'ından gelir (ORMAN_V3_SHA256), canlı v4 test_orman_yaklasma ORMAN_SHA256 ile kilitli.
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "orman_v3_runs_40.json"),
                      encoding="utf-8") as fh:
                out["modes"][name] = json.load(fh)
            continue
        out["modes"][name] = {str(s): mode_run(flags, ev, s, dom) for s in range(1, 41)}
    return out


def snapshot_hash(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


class TestTexts(_Quiet):
    def test_verbatim_texts(self):
        self.assertEqual(hp.KASIRGA_MODE_LABEL, "🌀 Kasırga")
        self.assertEqual(hp.KASIRGA_CATEGORY_LABEL, "🌀 Kasırga")
        self.assertEqual(hp.KASIRGA_EVENT_LABEL, EVENT_LABEL)
        self.assertEqual((hp.KASIRGA_EVENT, hp.KASIRGA_DOMAIN), (EVENT, DOMAIN))
        self.assertEqual({g: (KS["geos"][g]["name"], KS["geos"][g]["place"]) for g in KS["geos"]}, PLACES)
        a, b, c = es.SLICE_LABELS
        for g, (_, place) in PLACES.items():
            self.assertEqual(f"{a}: {hp.kasirga_opening(g)}", OPENING.format(place=place))
        for n, text in PEOPLE.items():
            self.assertEqual(hp.kasirga_people(n), text)
        for n in (2, 3, 6, 7):
            with self.assertRaises(es.StructureError):
                hp.kasirga_people(n)
        self.assertEqual(KS["vehicles"], VEHICLES)
        self.assertEqual({k: f"{b}: {v}" for k, v in KS["mids"].items()}, MIDS)
        self.assertEqual({k: f"{c}: {v}" for k, v in KS["finals"].items()}, FINALS)
        self.assertEqual(KS["vehicle_mids"], ("O1", "O2", "O3"))
        self.assertEqual(hp.kasirga_tail(), TAIL)
        self.assertEqual(KS["tail"], TAIL)
        self.assertIn(hp.kasirga_camera_text(), TAIL)
        self.assertIn(NEGATION, TAIL)
        self.assertEqual(hp.KASIRGA_NEGATION, NEGATION)
        self.assertEqual((hp.KASIRGA_GEO_BLOCK, hp.KASIRGA_VEHICLE_BLOCK, hp.KASIRGA_MID_BLOCK,
                          hp.KASIRGA_FINAL_BLOCK), (3, 2, 1, 1))
        self.assertEqual((hp.KASIRGA_MAX_WORDS, hp.KASIRGA_MAX_CHARS), (230, 1400))
        self.assertEqual(hp.KASIRGA_REQUIRED, REQUIRED)
        self.assertEqual(hp.KASIRGA_FORBIDDEN, FORBIDDEN)
        self.assertEqual(hp.KASIRGA_CAMERA_LINE, CAMERA_LINE)
        self.assertEqual(hp.KASIRGA_WARNING, WARNING)
        self.assertEqual(hp.KASIRGA_NOTION_CATEGORY, "Kasırga")
        # sıra: açılış + insan + orta + final + stil eki
        self.assertEqual(hp.kasirga_prompt("G3", 5, "O2", "SUV", "F3"), expected("G3", 5, "SUV", "O2", "F3"))
        self.assertEqual(hp.kasirga_prompt("G1", 4, "O1", "pickup truck", "F1"),
                         "0-4s: Category 5 hurricane winds and torrential sideways rain hammer a street in a Florida "
                         "beach town of low pastel houses, palm trees bent almost flat, one palm torn out by its roots "
                         "and hurled across the road, branches, roof sheets and debris flying everywhere in total "
                         "chaos. Four people struggle along the sidewalk toward the camera, "
                         "bent double against the wind, clinging to railings, one knocked off his feet by a gust. 4-9s: "
                         "A violent gust flips a parked pickup truck onto its roof and sends it skidding across the wet "
                         "road. 9-15s: Right across the street, the wind peels the whole roof off a house, metal sheets "
                         "and tiles flying past the camera. " + TAIL)
        self.assertEqual(hp.kasirga_prompt("G5", 5, "O3", "small car", "F2"),
                         "0-4s: Category 5 hurricane winds and torrential sideways rain hammer a street in a Cuban "
                         "seaside town of faded colonial houses, palm trees bent almost flat, one palm torn out by its "
                         "roots and hurled across the road, branches, roof sheets and debris flying everywhere in "
                         "total chaos. Five people struggle along the sidewalk toward the camera, bent double against "
                         "the wind, clinging to railings, one knocked off his feet by a gust. 4-9s: A big tree is "
                         "ripped out by its roots and crashes across the road onto a parked small car, crushing its "
                         "roof. 9-15s: Right across the street, a wooden power pole snaps at its base and crashes "
                         "down across the road, live wires whipping and sparking. " + TAIL)
        self.assertEqual(hp.KASIRGA_VERSION_LINE, VERSION_LINE)
        self.assertEqual(hp.KASIRGA_WEATHER, "kategori 5 kasırga rüzgârı ve sağanak yatay yağmur (stil ekinde dark grey "
                                             "sky in pouring rain)")

    def test_passive_v1_texts(self):
        """15 Kas (5): değişen her eski metin KASIRGA_PASIF'te _V1 olarak birebir; hiçbir aktif prompt'ta (324
        kombinasyon + 40 tohum) ve aktif Onay/kamera metninde çıkmaz."""
        self.assertEqual(hp.KASIRGA_PASIF, PASIF)
        for (g, ppl, v, m, f), p in all_combos():
            for bit in OLD_PROMPT_BITS:
                self.assertNotIn(bit, p, (g, ppl, v, m, f, bit))
            self.assertNotIn("heavy hand shake", p.lower())
        for seed in range(1, 41):
            d = build(seed)
            sc, tb = d["scenes"][0], d["structure"]["kasirga"]
            for bit in OLD_PROMPT_BITS:
                for text in (sc["prompt"], sc["story"], sc["style_suffix"]):
                    self.assertNotIn(bit, text, (seed, bit))
            for old in ("CAMERA_LINE_V1", "WARNING_V1", "SPOT_DISPLAY_V1", "CAMERA_MODE_V1", "CAMERA_LINE_V3",
                        "VERSION_LINE_V3"):
                self.assertNotIn(PASIF[old] + "\n", tb["lines"] + "\n", (seed, old))
            self.assertNotIn("rüzgârla sarsılan el", json.dumps(d["trace"], ensure_ascii=False), seed)
        for old, new in (("OPENING_V2", KS["opening"]), ("F2_V2", KS["finals"]["F2"]), ("TAIL_V3", KS["tail"]),
                         ("CAMERA_V3", KS["camera"]), ("CAMERA_LINE_V3", hp.KASIRGA_CAMERA_LINE),
                         ("O2_V3", KS["mids"]["O2"]), ("VERSION_LINE_V3", hp.KASIRGA_VERSION_LINE)):
            self.assertNotEqual(PASIF[old], new, old)
        for old, new in (("CAMERA_LINE_V1", hp.KASIRGA_CAMERA_LINE), ("WARNING_V1", hp.KASIRGA_WARNING),
                         ("WEATHER_V1", hp.KASIRGA_WEATHER), ("CONFIRM_DESC_V1", hp.KASIRGA_CONFIRM_DESC),
                         ("REQUIRED_V1", hp.KASIRGA_REQUIRED), ("TAIL_V1", hp.kasirga_tail()),
                         ("CAMERA_V1", hp.kasirga_camera_text()), ("VEHICLE_MIDS_V1", KS["vehicle_mids"])):
            self.assertNotEqual(PASIF[old], new, old)
        # eski stil eki yeni Kie öncesi denetimden geçmez (heavy hand shake yasak, yeni zorunlular eksik)
        p = hp.kasirga_prompt("G1", 4, "O1", "SUV", "F1").replace(TAIL, PASIF["TAIL_V1"])
        issues = hp.kasirga_camera_issues(p, "G1")
        self.assertIn("bu kategoride olmayan ifade var: heavy hand shake", issues)
        self.assertIn('"stays fixed on the street" eksik', issues)
        self.assertIn('"pouring rain" eksik', issues)

    def test_vehicle_fill_and_bad_ids(self):
        for v in VEHICLES:
            for m in MIDS:
                self.assertEqual("4-9s: " + hp.kasirga_mid(m, v), MIDS[m].format(vehicle=v))
        for m in MIDS:
            with self.assertRaises(es.StructureError):
                hp.kasirga_mid(m, None)
            with self.assertRaises(es.StructureError):
                hp.kasirga_mid(m, "taxi")   # bu kategorinin havuzunda değil
        for bad in ("O4", "P6", "C1"):
            with self.assertRaises(es.StructureError):
                hp.kasirga_mid(bad, "SUV")
        for bad in ("F4", "Q3"):
            with self.assertRaises(es.StructureError):
                hp.kasirga_final(bad)
        with self.assertRaises(es.StructureError):
            hp.kasirga_opening("G7")

    def test_all_combos_within_limits(self):
        """324 kombinasyon (6 × 2 × 3 × 3 × 3): hepsi ≤ 230 kelime, ≤ 1400 karakter. 21 Kas (3) v3: en kısa 200
        kelime (G2 + SUV + O2 + F3), en uzun 214 kelime (G1 + pickup truck + O3 + F2 dahil 20 kombinasyon); en kısa
        karakter 1152 (G1 + SUV + O2 + F3), en uzun 1221 (G3 + pickup truck + O3 + F2). (v2: 186-197 kelime,
        1071-1137 karakter; v1: 174-183 kelime, en uzun 1063.) Zorunlu/yasak ifade kontrolü ve ana hattın zorunlu olay denetimi her kombinasyonda geçer; "front wall"
        ve "facade" hiçbirinde yok."""
        n, over, words, chars = 0, [], [], []
        for key, p in all_combos():
            n += 1
            g, ppl, v, m, f = key
            w, c = len(p.split()), len(p)
            words.append((w, key))
            chars.append((c, key))
            if w > hp.KASIRGA_MAX_WORDS or c > hp.KASIRGA_MAX_CHARS:
                over.append((key, w, c))
            self.assertEqual(p, expected(g, ppl, v, m, f), key)
            self.assertEqual(sum(pl in p for _, pl in PLACES.values()), 1, key)
            self.assertEqual(hp.kasirga_camera_issues(p, g), [], key)
            self.assertTrue(p.endswith(" " + TAIL))
            for w in NO_WALL_WORDS:
                self.assertNotIn(w, p.lower(), (key, w))
            rest = p.replace(NEGATION, " ").lower()
            for bad in FORBIDDEN + (sk.FULL_MOTION,):
                self.assertNotIn(bad.lower(), rest, (key, bad))
            for need in REQUIRED:
                self.assertIn(need, p, (key, need))
            # main.py zorunlu olay denetimi (iç anahtar "Hurricane winds batter a coastal town"): "Hurricane winds"
            # her açılışta, eş anlamlı gerekmedi
            self.assertEqual(pg.event_fidelity_issues(EVENT, hp.kasirga_story(g, ppl, m, v, f)), [], key)
            self.assertEqual(pg.event_fidelity_issues(EVENT, p), [], key)
        self.assertEqual(n, 6 * 2 * 3 * 3 * 3)
        self.assertEqual(n, 324)
        self.assertEqual(over, [])
        self.assertEqual(min(words)[0], 200)
        self.assertEqual(max(words)[0], 214)
        self.assertEqual(sum(w == 214 for w, _ in words), 20)
        self.assertEqual(len(hp.kasirga_prompt("G1", 4, "O3", "pickup truck", "F2").split()), 214)
        self.assertEqual(len(hp.kasirga_prompt("G2", 4, "O2", "SUV", "F3").split()), 200)
        self.assertEqual(max(chars)[0], 1221)
        self.assertEqual(max(chars)[1][0::2], ("G3", "pickup truck", "F2"))
        self.assertEqual(max(chars)[1][3], "O3")
        self.assertEqual(min(chars)[0], 1152)
        self.assertEqual(len(hp.kasirga_prompt("G3", 5, "O3", "pickup truck", "F2")), 1221)
        self.assertEqual(len(hp.kasirga_prompt("G1", 4, "O2", "SUV", "F3")), 1152)

    def test_event_gate_without_synonym(self):
        """Olay kapısı bu olayda da açık ve geçiyor: iç anahtarın kökleri (hurr, wind, batt, coas, town) içinden
        "hurr" + "wind" her açılışta. Eş anlamlı eklenmedi; normal hattın eş anlamlı tablosu aynı. Rüzgârsız metin ya da
        sadece "hurricane" geçen metin hâlâ reddedilir."""
        self.assertEqual(pg._event_stems(EVENT), {"hurr", "wind", "batt", "coas", "town"})
        self.assertNotIn("hurr", pg._EVENT_SYNONYMS)
        self.assertNotIn("batt", pg._EVENT_SYNONYMS)
        self.assertTrue(pg.event_fidelity_issues(EVENT, "Rain falls on the beach."))
        self.assertTrue(pg.event_fidelity_issues(EVENT, "A hurricane."))
        self.assertEqual(pg.event_fidelity_issues(EVENT, "Hurricane winds hammer the street."), [])
        # 15 Kas (5): açılış artık "Category 5 hurricane winds" (küçük harf); kapı harf büyüklüğüne bakmaz
        self.assertEqual(pg.event_fidelity_issues(EVENT, "Category 5 hurricane winds hammer the street."), [])
        for g, (_, place) in PLACES.items():
            self.assertEqual(pg.event_fidelity_issues(EVENT, hp.kasirga_opening(g)), [], g)
        self.assertEqual([e for e in es.structured_events() if "hurr" in pg._event_stems(e)], [])


class TestKasirgaScene(_Quiet):
    def _check(self, d):
        sc, st = d["scenes"][0], d["structure"]
        tb = st["kasirga"]
        prompt = sc["prompt"]
        self.assertIn(tb["geo"], PLACES)
        self.assertIn(tb["vehicle"], VEHICLES)
        self.assertIn(tb["mid"], MIDS)
        self.assertIn(tb["final"], FINALS)
        self.assertIn(tb["people"], (4, 5))
        self.assertEqual(prompt, expected(tb["geo"], tb["people"], tb["vehicle"], tb["mid"], tb["final"]))
        self.assertEqual(sc["style_suffix"], TAIL)
        self.assertIn(PLACES[tb["geo"]][1], prompt)
        for need in REQUIRED:
            self.assertIn(need, prompt)
        rest = prompt.replace(NEGATION, " ").lower()
        for bad in FORBIDDEN:
            self.assertNotIn(bad.lower(), rest)
        self.assertLessEqual(len(prompt.split()), 230)
        self.assertLessEqual(len(prompt), 1400)
        self.assertEqual(d["combo_key"], f"{DOMAIN}|none|{EVENT.lower()}|high balcony across the street##"
                                         f"{tb['mid']}+{tb['final']}|bystander_handheld")
        self.assertEqual(cp.submit_issues(st, {"prompt": prompt, "story": sc["story"],
                                               "style_suffix": sc["style_suffix"]}), [])
        self.assertEqual(pg.event_fidelity_issues(EVENT, sc["story"]), [])
        self.assertEqual((d["selection"]["domain_id"], d["selection"]["event"]), (DOMAIN, EVENT))
        self.assertNotIn("donma_firtina", st)
        return tb

    def test_40_seeds_no_error_and_no_gpt(self):
        """EK KONTROL: 40 tohumda hatasız; GPT (hikâye) hiç çağrılmaz, OpenAI istemcisi istenmez, normal hat çalışmaz."""
        with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT çağrıldı"))) as gpt, \
             patch.object(pg, "_get_openai_client", side_effect=AssertionError("GPT istemcisi istendi")), \
             patch.object(cp, "build_creative_scene", AsyncMock(side_effect=AssertionError("normal hat"))) as normal:
            seen = set()
            for seed in range(1, 41):
                tb = self._check(build(seed))
                seen.add((tb["geo"], tb["mid"], tb["final"], tb["vehicle"], tb["people"]))
        gpt.assert_not_called()
        normal.assert_not_called()
        self.assertGreater(len(seen), 20)
        self.assertEqual(es.CODE_STORY_FORCE.get(), frozenset())
        self.assertFalse(es.is_structured(EVENT))   # normal havuzda yok

    def test_lru(self):
        geos, mids, finals = set(), set(), set()
        for seed in range(1, 16):
            reset()
            random.seed(seed)
            runs = [self._check(gen()) for _ in range(10)]
            for key in ("mid", "final"):
                vals = [r[key] for r in runs]
                for i in range(1, len(vals)):
                    self.assertNotEqual(vals[i], vals[i - 1], (seed, key, vals))
            g = [r["geo"] for r in runs]
            for i in range(len(g)):
                self.assertNotIn(g[i], g[max(0, i - 3):i], (seed, g))
            v = [r["vehicle"] for r in runs]
            for i in range(len(v)):
                self.assertNotIn(v[i], v[max(0, i - 2):i], (seed, v))
            self.assertEqual(hp._KASIRGA_VEHICLE_MEMORY[-10:], v)
            self.assertEqual(hp._KASIRGA_GEO_MEMORY[-10:], g)
            geos |= set(g)
            mids |= {r["mid"] for r in runs}
            finals |= {r["final"] for r in runs}
        self.assertEqual(geos, set(PLACES))
        self.assertEqual(mids, set(MIDS))
        self.assertEqual(finals, set(FINALS))
        self.assertEqual(hp._DONMA_GEO_MEMORY, [])   # donma hafızası etkilenmez

    def test_history_sources(self):
        """Notion "Eksenler" kayıtları (iptaller dahil) varsa LRU oradan; okunamazsa süreç hafızası, üretim durmaz."""
        def rec(g, v, tag, event=EVENT, mod="kasirga"):
            return {"eksenler": json.dumps({"event": event, "axes": {"mod": mod, "cografya": g, "arac": v,
                                                                     "beats": tag}})}
        recs = [rec("G1", "SUV", "O1+F1"), rec("G2", "pickup truck", "O2+F2"), {"eksenler": "x"},
                rec("G3", "SUV", "O1+F3"), rec("G5", "small car", "O2+F1", event=hp.DONMA_EVENT, mod="donma_firtina")]
        self.assertEqual(hp.kasirga_axes_history(recs, "cografya"), ["G1", "G2", "G3"])
        self.assertEqual(hp.kasirga_axes_history(recs, "arac"), ["SUV", "pickup truck", "SUV"])
        self.assertEqual(hp.kasirga_axes_history(recs, "beats"), ["O1+F1", "O2+F2", "O1+F3"])
        self.assertIsNone(hp.kasirga_axes_history(None, "arac"))
        calls = []
        for seed in range(1, 11):
            reset()
            random.seed(seed)
            d = gen(axes_loader=lambda dom: calls.append(dom) or recs)
            tb = d["structure"]["kasirga"]
            self.assertIn(tb["geo"], ("G4", "G5", "G6"))      # son 3 (G1, G2, G3) elenir
            self.assertEqual(tb["vehicle"], "small car")      # son 2 (pickup truck, SUV) elenir
            self.assertIn(tb["mid"], ("O2", "O3"))            # son 1 (O1) elenir
            self.assertIn(tb["final"], ("F1", "F2"))          # son 1 (F3) elenir
            axes = json.loads(d["axes_json"])
            self.assertEqual(axes["event"], EVENT)
            self.assertEqual((axes["axes"]["mod"], axes["axes"]["cografya"], axes["axes"]["arac"],
                              axes["axes"]["beats"], axes["axes"]["kategori"]),
                             ("kasirga", tb["geo"], tb["vehicle"], f"{tb['mid']}+{tb['final']}", "Kasırga"))
            self.assertEqual(d["trace"]["axes_source"], "notion")
        self.assertEqual(set(calls), {DOMAIN})

        def broken(dom):
            raise RuntimeError("Notion yok")
        reset()
        random.seed(3)
        d = gen(axes_loader=broken)
        self.assertEqual(d["trace"]["axes_source"], "bellek")
        self._check(d)
        hist = [f"{DOMAIN}|none|{EVENT.lower()}|high balcony across the street##O2+F2|bystander_handheld"]
        for s in range(20):
            reset()
            tags = hp.kasirga_tags(hist)
            self.assertEqual(tags, ["O2+F2"])
            self.assertIn(hp.kasirga_choose_mid(tags, random.Random(s)), ("O1", "O3"))
            self.assertIn(hp.kasirga_choose_final(tags, random.Random(s)), ("F1", "F3"))
        donma = [f"{hp.DONMA_DOMAIN}|none|{hp.DONMA_EVENT.lower()}|x##O1+F2|bystander_handheld"]
        self.assertEqual(hp.kasirga_tags(donma), [])   # donma kaydı bu kategoriyi etkilemez

    def test_kie_final_check_required_and_forbidden(self):
        d = build(9)
        sc, st = d["scenes"][0], d["structure"]
        tb = st["kasirga"]
        info = {"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"]}
        self.assertEqual(cp.submit_issues(st, info), [])
        p0 = sc["prompt"]
        place = PLACES[tb["geo"]][1]
        other = PLACES["G2" if tb["geo"] != "G2" else "G3"][1]
        end = "never in slow motion."
        for need in REQUIRED:
            bad = p0.replace(need, "x")
            self.assertIn(f'"{need}" eksik', hp.kasirga_camera_issues(bad, tb["geo"]), need)
            self.assertTrue(cp.submit_issues(st, {**info, "prompt": bad}), need)
        self.assertIn("G1-G6 yer metni yok", hp.kasirga_camera_issues(p0.replace(place, "a town"), tb["geo"]))
        self.assertTrue(hp.kasirga_camera_issues(p0.replace(place, other), tb["geo"]))
        for bad in FORBIDDEN:
            for form in (bad, bad.upper(), bad.capitalize()):   # büyük/küçük harf fark etmez
                text = p0.replace(end, end + f" {form} x.")
                self.assertIn(f"bu kategoride olmayan ifade var: {bad}", hp.kasirga_camera_issues(text, tb["geo"]),
                              form)
                self.assertTrue(hp.kasirga_issues(st, {**info, "prompt": text}), form)
                self.assertTrue(cp.submit_issues(st, {**info, "prompt": text}), form)
        # izinli olumsuzlama cümlesi dışında geçen "tornado"/"funnel"/"flood waves" yakalanır
        self.assertTrue(hp.kasirga_camera_issues(p0 + " A tornado funnel appears.", tb["geo"]))
        self.assertTrue(hp.kasirga_camera_issues(p0 + " Big flood waves roll in.", tb["geo"]))
        self.assertTrue(hp.kasirga_camera_issues(p0 + " A storm surge floods the road.", tb["geo"]))
        # cümle değişirse (ör. "no flood waves" çıkarsa) "No tornado funnel" zorunlu ifadesi yine aranır
        self.assertIn('"No tornado funnel" eksik', hp.kasirga_camera_issues(p0.replace(NEGATION, ""), tb["geo"]))
        for bad in ({"geo": "G7"}, {"mid": "P6"}, {"mid": "O4"}, {"final": "Q3"}, {"people": 6},
                    {"mid": "O1", "vehicle": None}, {"vehicle": "taxi"}):
            self.assertTrue(cp.submit_issues({**st, "kasirga": {**tb, **bad}}, info), bad)
        self.assertTrue(cp.submit_issues(st, {**info, "style_suffix": "x"}))
        self.assertTrue(cp.submit_issues(st, {**info, "prompt": p0.replace("4-9s: ", "")}))
        # Kie reddi sonrası yeni yazım yok: aynı hikâye döner, GPT çağrılmaz
        story = asyncio.run(cp.rewrite_structured(st, "test", AsyncMock(side_effect=AssertionError("GPT"))))
        self.assertEqual(story, sc["story"])
        self.assertIn("yeniden yazım yok", st["rewrite_log"][-1]["result"])
        with patch.object(hp, "KASIRGA_REQUIRED", REQUIRED + ("olmayan ifade",)):
            reset()
            random.seed(9)
            with self.assertRaises(es.StructureError):
                gen()

    def test_approval_lines_and_display(self):
        seen = set()
        for seed in range(1, 41):
            d = build(seed)
            sc, st = d["scenes"][0], d["structure"]
            tb = st["kasirga"]
            lines = tb["lines"].split("\n")
            self.assertEqual(lines[:9], [
                "Mod: 🌀 Kasırga",
                VERSION_LINE,   # 21 Kas (2)
                f"Coğrafya: {tb['geo']} {PLACES[tb['geo']][0]} (rastgele)",   # 21 Kas: + seçim kaynağı
                f"Araç: {tb['vehicle']}",
                f"Orta (4-9s): {tb['mid']} «{MIDS[tb['mid']].format(vehicle=tb['vehicle'])[6:]}»",
                f"Final (9-15s): {tb['final']} «{FINALS[tb['final']][7:]}»",
                f"Kişi: {tb['people']}",
                CAMERA_LINE,
                f"Kelime: {len(sc['prompt'].split())} (en fazla 230) · karakter: {len(sc['prompt'])} (en fazla 1400)"])
            self.assertTrue(lines[9].startswith("Eksenler (🌀 Kasırga): "), lines[9])
            for part in (f"coğrafya={tb['geo']} {PLACES[tb['geo']][0]}", f"araç={tb['vehicle']}", f"orta={tb['mid']}",
                         f"final={tb['final']}", f"kişi={tb['people']}"):
                self.assertIn(part, lines[9])
            self.assertTrue(lines[10].startswith("Tekrar önleme: coğrafya son 3 elendi · araç son 2 · orta son 1 · "
                                                 "final son 1"), lines[10])
            self.assertEqual(lines[11], WARNING)
            self.assertEqual(len(lines), 12)
            for w in NO_WALL_WORDS:
                for text in (sc["prompt"], sc["story"], sc["style_suffix"], tb["lines"]):
                    self.assertNotIn(w, text.lower(), (seed, w))
            seen.add(tb["mid"])
            # O1-O3 hepsinde araç: araç geçmişi her üretimde ilerler, Notion Eksenler'e araç yazılır
            self.assertEqual(hp._KASIRGA_VEHICLE_MEMORY[-1], tb["vehicle"])
            self.assertEqual(json.loads(d["axes_json"])["axes"]["arac"], tb["vehicle"])
            shown = sections_to_text(format_generation(d["trace"], {"domain": "🌀 Kasırga",
                                                                    "event": hp.KASIRGA_EVENT_LABEL}))
            self.assertIn(hp.KASIRGA_WEATHER, shown)
            self.assertIn("Mod: 🌀 Kasırga", shown)
            self.assertIn("Hikâye: kod (birebir) · 🌀 Kasırga", shown)
            self.assertNotIn("GPT'ye verildi", shown)
            _, body = format_final_prompt({"prompt": sc["prompt"], "story": sc["story"],
                                           "style_suffix": sc["style_suffix"], "hit_lines": tb["lines"],
                                           "story_source": st["story_source"], "axes_line": st["axes_line"]})
            self.assertIn("\nMod: 🌀 Kasırga\n", body)
            self.assertEqual(body.count("Eksenler (🌀 Kasırga)"), 1)
            self.assertIn(WARNING, body)
            self.assertIn("\n\n" + sc["prompt"], body)
        self.assertEqual(seen, {"O1", "O2", "O3"})   # 15 Kas (5): O3 40 tohumda seçilebiliyor

    def test_notion_category_and_caption(self):
        """Notion üretim kaydında kategori "Eksenler" JSON'unda metin ("Kasırga"), donmadaki gibi; Paylaşımlar
        "Kategori" caption'dan (seçenek ilk yazımda oluşur). Otomatik caption diğer olaylardaki gibi çalışır."""
        self.assertEqual(cap.KASIRGA, EVENT)
        self.assertEqual(cap.SHARE_CATEGORY[EVENT], "Kasırga")
        self.assertEqual(cap.TAG_POOL[EVENT], "kasirga")
        broad, special = cap.event_tags(EVENT)
        for t in broad + special:
            for bad in ("tornado", "twister", "waterspout", "surge", "tsunami", "tidal", "flood"):
                self.assertNotIn(bad, t)
        for seed in range(1, 11):
            d = build(seed)
            self.assertEqual(json.loads(d["axes_json"])["axes"]["kategori"], "Kasırga")
            c = d["caption"]
            self.assertIsNotNone(c)
            self.assertEqual(c["category"], "Kasırga")
            self.assertEqual(len(c["hashtags"]), 5)
            self.assertTrue(set(c["hashtags"]) <= set(broad) | set(special))
            self.assertTrue(d["caption_block"])
            self.assertEqual(json.loads(d["axes_json"])["caption"]["category"], "Kasırga")
            self.assertTrue(d["youtube_title"].endswith(" #Shorts"))
            for bad in ("tornado", "funnel", "twister", "tsunami", "tidal"):
                self.assertNotIn(bad, json.dumps(c, ensure_ascii=False).lower(), (seed, bad))
        st = d["caption_state"]
        c2 = cap.choose(st["event"], st["info"], st["candidates"], st["ctx"] or {}, random.Random(1),
                        exclude_titles=st["shown"])
        self.assertEqual(c2["category"], "Kasırga")


class TestKasirgaPipelineAndBot(_Quiet):
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
                return await orig(**{**kw, "domain": DOMAIN}, kasirga=True)
            with patch.object(main, "run_pipeline", run_with):
                r = t.run_pipe(gen=AsyncMock(side_effect=fake_gen), reporter=rep, event=EVENT, poll=poll)
        finally:
            t.doCleanups()
        return r, rep, seen, t

    def test_pipeline_passes_flag_and_sends_prompt(self):
        """Ana hat: zorunlu olay denetimi (senaryo + hikâye + Kie öncesi) geçer, ✋ Onay Kie'den önce, Kie'ye giden
        metin onaydaki, Notion Eksenler'de kategori metni."""
        r, rep, seen, t = self._run()
        self.assertTrue(r["success"], r)
        self.assertIs(seen["config"]["kasirga"], True)
        self.assertNotIn("donma_firtina", seen["config"])
        self.assertEqual((seen["config"]["domain"], seen["config"]["event"]), (DOMAIN, EVENT))
        approve = [c[1] for c in rep.calls if c[0] == "approve"]
        self.assertEqual(len(approve), 1)
        info = approve[0]
        self.assertTrue(info["hit_lines"].startswith(f"Mod: 🌀 Kasırga\n{VERSION_LINE}\nCoğrafya: G"))
        self.assertIn(WARNING, info["hit_lines"])
        self.assertIn(CAMERA_LINE, info["hit_lines"])
        self.assertEqual(t.create.await_count, 1)
        self.assertEqual(t.create.await_args.args[1], info["prompt"])
        self.assertTrue(info["prompt"].endswith(TAIL))
        axes = [c.args[0] for c in t.tracker.record_axes.call_args_list]
        self.assertEqual(json.loads(axes[0])["axes"]["kategori"], "Kasırga")

    def test_event_gate_blocks_mismatch(self):
        """Olay kapısı bu olay için kapalı değil: hikâye olayı taşımıyorsa Kie çağrılmaz."""
        import main
        with patch.object(main, "event_fidelity_issues", side_effect=lambda e, t, *a: ["uyuşmuyor"]
                          if e == EVENT else []):
            r, _, _, t = self._run()
        self.assertFalse(r["success"])
        self.assertEqual(t.create.await_count, 0)

    def test_kie_rejection_existing_behavior(self):
        from infrastructure.kie_client import ContentFilterError
        poll = AsyncMock(side_effect=ContentFilterError("İçerik filtresi: prohibited content"))
        r, rep, _, t = self._run(poll=poll)
        self.assertFalse(r["success"])
        self.assertEqual(r["reason"], "structure_check")
        self.assertIn("Kie içerik filtresi", r["error"])
        self.assertEqual(t.create.await_count, 2)   # mevcut davranış: aynı prompt bir kez daha
        self.assertEqual(t.create.await_args_list[0].args[1], t.create.await_args_list[1].args[1])

    def test_bot_labels(self):
        import bot
        from test_tur29_infra import _context
        ctx = _context()
        runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
        with patch.object(bot.pipeline, "run_pipeline", runner):
            asyncio.run(bot.produce(ctx.bot, 1, DOMAIN, EVENT, cfg=bot.default_cfg(), bot_data={}, kasirga=True))
        kw = runner.await_args.kwargs
        self.assertIs(kw["kasirga"], True)
        self.assertNotIn("donma_firtina", kw)
        self.assertEqual(kw["reporter"].labels, {"domain": "🌀 Kasırga", "event": EVENT_LABEL})
        self.assertEqual(bot.selection_label(EVENT), EVENT_LABEL)
        self.assertEqual(bot.CODE_EVENT_LABELS[EVENT], EVENT_LABEL)
        self.assertEqual(bot.CODE_DOMAIN_LABELS[DOMAIN], "🌀 Kasırga")

    def test_bot_button_and_flow(self):
        import bot
        from test_tur29_infra import _context, _update
        kb = bot.domain_keyboard(bot.default_cfg())
        texts = [b.text for r in kb.inline_keyboard for b in r]
        self.assertEqual(texts.count("🌀 Kasırga"), 1)
        row = next(r for r in kb.inline_keyboard if r[0].text == "🌀 Kasırga")
        self.assertEqual((len(row), row[0].callback_data), (1, "uret:ks"))
        self.assertEqual(texts.index("🌀 Kasırga"), texts.index("❄️ Donduran fırtına") + 1)
        self.assertNotIn(DOMAIN, bot.DOMAIN_KEYS)   # normal kategori sıra numaraları değişmez
        self.assertNotIn(EVENT, bot.EVENT_LABELS)
        ctx = _context()
        upd = _update(data="uret:ks")
        asyncio.run(bot.on_callback(upd, ctx))
        call = upd.callback_query.edit_message_text.await_args
        self.assertIn("🌀 Kasırga", call.args[0])
        labels = [b.text for r in call.kwargs["reply_markup"].inline_keyboard for b in r]
        self.assertEqual(labels, [EVENT_LABEL, "🔙 Geri"])
        cbs = [b.callback_data for r in call.kwargs["reply_markup"].inline_keyboard for b in r]
        self.assertEqual(cbs, ["uret:kse", "uret:back"])
        # 21 Kas: olay → coğrafya ekranı (G1-G6 + 🎲 Rastgele + 🔙 Geri)
        upd = _update(data="uret:kse")
        asyncio.run(bot.on_callback(upd, ctx))
        call = upd.callback_query.edit_message_text.await_args
        self.assertEqual(call.args[0], f"{EVENT_LABEL}\nHangi coğrafya?")
        rows = call.kwargs["reply_markup"].inline_keyboard
        self.assertEqual([[b.text for b in r] for r in rows], [
            ["🇺🇸 ABD Florida", "🇵🇭 Filipinler"], ["🌴 Meksika Karayipleri", "🇮🇳 Hindistan"],
            ["🇨🇺 Küba", "🇯🇵 Japonya"], ["🎲 Rastgele"], ["🔙 Geri"]])
        self.assertEqual([b.callback_data for r in rows for b in r],
                         [f"uret:ksg:G{i}" for i in range(1, 7)] + ["uret:ksg:r", "uret:ks"])
        upd = _update(data="uret:ksg:r")
        asyncio.run(bot.on_callback(upd, ctx))
        call = upd.callback_query.edit_message_text.await_args
        text = call.args[0]
        self.assertIn("Coğrafya: 🎲 Rastgele (son 3 coğrafya elenir)", text)
        for part in ("Kategori: 🌀 Kasırga", f"Olay: {EVENT_LABEL}", "Mod: 🌀 Kasırga", CAMERA_LINE, "✋ Onay",
                     hp.KASIRGA_CONFIRM_DESC, "\n" + VERSION_LINE + "\n", "orta (O1-O3)"):
            self.assertIn(part, text)
        self.assertNotIn("O1-O2", text)   # 21 Kas (2): O3 15 Kas (5)'ten beri aktif
        self.assertNotIn("—", text)   # Türkçe içerik kuralı: em-dash yok
        self.assertEqual([b.text for r in call.kwargs["reply_markup"].inline_keyboard for b in r], ["✅ Üret", "❌ İptal"])
        self.assertEqual(call.kwargs["reply_markup"].inline_keyboard[0][0].callback_data, "uret:ksok:r")
        upd = _update(data="uret:ksok:r")
        runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
        with patch.object(bot.pipeline, "run_pipeline", runner), patch.object(bot, "_production_lock", asyncio.Lock()):
            asyncio.run(bot.on_callback(upd, ctx))
        kw = runner.await_args.kwargs
        self.assertEqual((kw["domain"], kw["event"], kw["kasirga"]), (DOMAIN, EVENT, True))
        self.assertNotIn("kasirga_geo", kw)   # 🎲 Rastgele: bugünkü LRU yolu
        for other in ("donma_firtina", "cadde_yaklasma", "hortum_yaklasma", "heli_yaklasma", "kul_yaklasma",
                      "orman_yaklasma", "dalga24", "approach_env", "hit_env"):
            self.assertNotIn(other, kw)
        self.assertTrue(kw["reporter"].needs_approval)
        started = upd.callback_query.edit_message_text.await_args_list[0].args[0]
        self.assertIn(f"🚀 Üretim başladı: 🌀 Kasırga / {EVENT_LABEL}", started)
        for bad in ("uret:ks:1", "uret:kse:0", "uret:ksok:x", "uret:ksg", "uret:ksg:G7", "uret:ksg:g1",
                    "uret:ksok:G1:r"):
            upd = _update(data=bad)
            asyncio.run(bot.on_callback(upd, ctx))
            self.assertIn("Geçersiz", upd.callback_query.edit_message_text.await_args.args[0])
        busy = asyncio.Lock()
        asyncio.run(busy.acquire())
        with patch.object(bot, "_production_lock", busy):
            upd = _update(data="uret:ksok")
            asyncio.run(bot.on_callback(upd, ctx))
            self.assertEqual(upd.callback_query.edit_message_text.await_args.args[0], bot.BUSY_TEXT)
        for b in (b for m in (kb, bot.kasirga_event_keyboard(), bot.kasirga_produce_keyboard(),
                              bot.kasirga_geo_keyboard(), bot.kasirga_produce_keyboard("G6"))
                  for r in m.inline_keyboard for b in r):
            self.assertLessEqual(len(b.callback_data.encode()), 64)


class TestOthersUntouched(_Quiet):
    """Diğer 19 olay, bütün modlar ve ❄️ Donduran fırtına: 40 tohum prompt / hikâye / stil eki / combo / eksenler
    birebir (önceki kod)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.snap = others_snapshot()

    def test_other_prompts_verbatim_40_seeds(self):
        self.assertEqual(len(self.snap["events"]), 19)
        self.assertEqual(len(self.snap["modes"]), 13)
        self.assertNotIn(EVENT, self.snap["events"])
        for name, runs in self.snap["modes"].items():
            for s, r in runs.items():
                self.assertNotIn("error", r, (name, s))
        self.assertEqual(snapshot_hash(self.snap), OTHERS_SHA256)

    def test_sentences_only_in_this_category(self):
        marks = ["Category 5 hurricane winds and torrential sideways rain hammer", *PEOPLE.values(),
                 *[t.split("{vehicle}")[0] for t in KS["mids"].values()], *KS["finals"].values(), TAIL,
                 KS["camera"], *[p for _, p in PLACES.values()], "sideways rain", "bent double against the wind",
                 "cartwheels down the road", "peels the whole roof off", "Hurricane", "Category 5",
                 "ripped out by its roots", "one palm torn out by its roots", "wooden power pole snaps at its base",
                 "live wires whipping and sparking", "dark grey sky in pouring rain",
                 "one knocked off his feet by a gust"]
        pools = json.dumps({e: {s: {k: v["text"] for k, v in b[s].items()} for s in ("slice_2", "slice_3")}
                            for e, b in es.EVENT_BEATS.items()}, ensure_ascii=False)
        others = pools + json.dumps(es.EVENT_KEY_VISUAL, ensure_ascii=False)
        for name in ("HIT_PROMPTS", "YAKLASMA_ATES_HORTUMU", "DALGA_24EYLUL", "YAKLASMA_KUL_BULUTU", "KUL_PASIF",
                     "YAKLASMA_ORMAN", "ORMAN_PASIF", "YAKLASMA_HELIKOPTER", "YAKLASMA_HORTUM", "HORTUM_PASIF",
                     "YAKLASMA_CADDE", "CADDE_PASIF", "DONMA_FIRTINA", "DONMA_PASIF"):
            others += json.dumps(getattr(hp, name), default=str, ensure_ascii=False)
        others += json.dumps(self.snap, ensure_ascii=False)
        for m in marks:
            self.assertNotIn(m, others, m)

    def test_locked_events_hash_file(self):
        import locked_prompts as lp
        self.assertEqual(lp.hashes(), lp.load())


if __name__ == "__main__":
    unittest.main()


class TestKasirgaV2Lock(_Quiet):
    """21 Kas (2), kasırga v2: 40 tohum kaydı yeni fixture ile birebir; v1 fixture'ından farkı yalnız açılış ve F2
    cümlesi; seçim sırası (G, araç, O, F, kişi), combo ve eksenler aynı tohumlarda aynı."""

    @staticmethod
    def live_runs() -> dict:
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

    @staticmethod
    def to_v1(text: str) -> str:
        for _, place in PLACES.values():
            text = text.replace(KS["opening"].format(place=place), PASIF["OPENING_V2"].format(place=place))
        return text.replace(KS["finals"]["F2"], PASIF["F2_V2"])

    def test_v2_fixture_hash(self):
        # 21 Kas (3): canlı kayıt artık v3 (TestKasirgaV3Lock); v2 kaydı fixture'da kilitli
        with open(FIXTURE_V2, encoding="utf-8") as fh:
            v2 = json.load(fh)
        self.assertEqual(snapshot_hash(v2), KASIRGA_V2_SHA256)

    def test_v1_fixture_hash(self):
        with open(FIXTURE_V1, encoding="utf-8") as fh:
            self.assertEqual(snapshot_hash(json.load(fh)), KASIRGA_V1_SHA256)

    def test_diff_only_opening_and_f2_same_selection(self):
        with open(FIXTURE_V1, encoding="utf-8") as fh:
            v1 = json.load(fh)
        with open(FIXTURE_V2, encoding="utf-8") as fh:
            v2 = json.load(fh)
        self.assertEqual(set(v1), set(v2))
        self.assertEqual(len(v2), 40)
        f2 = 0
        for s in v1:
            a, b = v1[s], v2[s]
            self.assertEqual(a["combo"], b["combo"], s)     # O + F aynı
            self.assertEqual(a["axes"], b["axes"], s)       # G, araç, kişi, O+F, dışlananlar aynı
            for k in ("prompt", "story", "suffix"):
                self.assertEqual(self.to_v1(b[k]), a[k], (s, k))
            self.assertEqual(a["suffix"], b["suffix"], s)
            self.assertNotEqual(a["prompt"], b["prompt"], s)   # açılış her tohumda değişti
            f2 += b["axes"]["axes"]["beats"].endswith("+F2")
            for w in NO_WALL_WORDS_V2:   # v2 dönemi kuralı (v2 fixture'ında O2 hâlâ metal sac içerir)
                self.assertNotIn(w, b["prompt"].lower(), (s, w))
            for bit in OLD_PROMPT_BITS_V2:
                self.assertNotIn(bit, b["prompt"], (s, bit))
        self.assertGreater(f2, 0)   # F2 40 tohumda en az bir kez seçiliyor


class TestKasirgaV3Lock(_Quiet):
    """21 Kas (3), kasırga v3: canlı 40 tohum kaydı v3 fixture ile birebir; v2 fixture'ından farkı yalnız stil eki ve
    O2 cümlesi; seçim sırası (G, araç, O, F, kişi), combo ve eksenler aynı tohumlarda aynı. Onay'da fark yalnız Sürüm,
    Kamera, O2'li Orta ve Kelime satırları."""

    @staticmethod
    def to_v2(text: str) -> str:
        text = text.replace(KS["tail"], PASIF["TAIL_V3"])
        for v in VEHICLES:
            text = text.replace(KS["mids"]["O2"].format(vehicle=v), PASIF["O2_V3"].format(vehicle=v))
        return text

    def test_live_equals_v3_fixture(self):
        with open(FIXTURE_V3, encoding="utf-8") as fh:
            v3 = json.load(fh)
        self.assertEqual(snapshot_hash(v3), KASIRGA_SHA256)
        self.assertEqual(snapshot_hash(TestKasirgaV2Lock.live_runs()), KASIRGA_SHA256)

    def test_diff_only_tail_and_o2_same_selection(self):
        with open(FIXTURE_V2, encoding="utf-8") as fh:
            v2 = json.load(fh)
        with open(FIXTURE_V3, encoding="utf-8") as fh:
            v3 = json.load(fh)
        self.assertEqual(set(v2), set(v3))
        self.assertEqual(len(v3), 40)
        o2 = 0
        for s in v2:
            a, b = v2[s], v3[s]
            self.assertEqual(a["combo"], b["combo"], s)     # O + F aynı
            self.assertEqual(a["axes"], b["axes"], s)       # G, araç, kişi, O+F, dışlananlar aynı
            for k in ("prompt", "story", "suffix"):
                self.assertEqual(self.to_v2(b[k]), a[k], (s, k))
            self.assertEqual(b["suffix"], TAIL, s)
            self.assertNotEqual(a["prompt"], b["prompt"], s)   # stil eki her tohumda değişti
            is_o2 = b["axes"]["axes"]["beats"].startswith("O2+")
            o2 += is_o2
            self.assertEqual(a["story"] != b["story"], is_o2, s)   # hikâye yalnız O2'de değişir
            for w in NO_WALL_WORDS:
                for k in ("prompt", "story", "suffix"):
                    self.assertNotIn(w, b[k].lower(), (s, k, w))
            for bit in OLD_PROMPT_BITS:
                self.assertNotIn(bit, b["prompt"], (s, bit))
        self.assertGreater(o2, 0)   # O2 40 tohumda en az bir kez seçiliyor

    def test_approval_diff_only_version_camera_o2_words(self):
        for s in range(1, 41):
            d = build(s)
            tb = d["structure"]["kasirga"]
            lines = tb["lines"].split("\n")
            self.assertEqual(lines[1], VERSION_LINE)
            self.assertIn(CAMERA_LINE, lines)
            self.assertNotIn(PASIF["CAMERA_LINE_V3"], lines)
            self.assertNotIn(PASIF["VERSION_LINE_V3"], lines)
            for w in NO_WALL_WORDS:
                self.assertNotIn(w, tb["lines"].lower(), (s, w))
