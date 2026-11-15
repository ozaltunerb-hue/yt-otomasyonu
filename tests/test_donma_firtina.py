# 15 Kas 2026, Bahadır: yeni kategori "❄️ Donduran fırtına", tek olay "❄️ Fırtınanın gözü şehri dondurur"
# (core/hit_prompts.py DONMA_FIRTINA). İlham: The Day After Tomorrow. YAKLASMA_CADDE ile aynı düzen: GPT yok, hikâye
# koddan birebir, zaman etiketleri var. Normal hattın sahnesi yok (olay yapılandırılmış havuzda değil). Coğrafya G1-G6
# (son 3), araç son 2, orta O1-O2 / final F1-F3 son 1, kişi 5/6. Karar: insanlar kaçarken donar, köpek de donar, kan
# yok; Kie reddederse öğrenmiş oluruz. Diğer 19 olay ve bütün modlar birebir aynı (40 tohum). Ağ yok.
# 15 Kas (3): 2. sürüm (göz halka) çok yapay çıktı; gözden vazgeçildi, tehdit caddeden gelen kar ve buz fırtınası
# cephesi. Metinler 1. sürüme döndü (açılış fırtına cephesi, F3 "blizzard", stil eki "high vantage" + "the blizzard
# always in frame"). Görünen ad "❄️ Buz fırtınası şehri dondurur" (iç anahtar aynı). 2. sürüm DONMA_PASIF *_V2.
import asyncio
import hashlib
import json
import logging
import os
import random
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

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

DF = hp.DONMA_FIRTINA
EVENT = "Storm's eye freezes the city"
DOMAIN = "frozen_storm_disasters"
PLACES = {"G1": ("ABD", "a New York avenue of brownstone buildings"),
          "G2": ("Fransa", "a Paris boulevard of cream stone buildings"),
          "G3": ("İngiltere", "a London street of red-brick terraces"),
          "G4": ("Almanya", "a Berlin boulevard lined with linden trees"),
          "G5": ("Brezilya", "a Rio avenue of palm trees and pastel buildings"),
          "G6": ("Hindistan", "a Mumbai street of old colonial buildings")}
# Talimattaki metinler kelimesi kelimesine (zaman etiketleri dahil). 15 Kas (3): fırtına cephesi, 1. sürüme dönüş.
OPENING = ("0-4s: A freezing blizzard front of dense, swirling snow and ice rolls down {place} toward the camera, and "
           "everything it swallows turns white with frost in an instant, trees and parked cars freezing solid.")
PEOPLE = {5: "Five people and a dog sprint toward the camera ahead of it.",
          6: "Six people and a dog sprint toward the camera ahead of it."}
VEHICLES = ("city bus", "taxi", "delivery van")
MIDS = {
    "O1": ("4-9s: The frost catches the people and the dog mid-stride, freezing them solid into white ice statues, and "
           "a moving {vehicle} freezes white and slides sideways into a lamppost."),
    "O2": ("4-9s: The frost catches the people and the dog mid-stride, freezing them solid into white ice statues, and "
           "a {vehicle} freezes mid-turn and tips over onto its side."),
}
FINALS = {
    "F1": ("9-15s: Right across the street, the frost climbs the building, its windows bursting white with ice, then "
           "ice races over the balcony railing in front of the camera."),
    "F2": ("9-15s: Right below the balcony, a tree and a row of parked cars freeze solid, the tree splitting with a "
           "crack, and white frost creeps up the railing in front of the camera."),
    "F3": ("9-15s: The blizzard hits the camera's building, ice racing up the facade and over the balcony railing as "
           "frost spreads across the edges of the frame."),
}
TAIL = ("Handheld footage shot by a person standing on a high balcony across the street, high vantage, normal lens; "
        "slight hand shake, the camera stays fixed, tilting only slightly, the blizzard always in frame; one continuous "
        "shot, no zoom, no cuts. Everything the frost touches freezes instantly and stays frozen white; frozen people "
        "stand still like statues, no blood, no injuries, no faces close to the camera. Raw natural light under a dark "
        "storm sky, never glossy or CGI. No readable signs or text. Everything moves in real time, never in slow "
        "motion, people run at full speed.")
CAMERA = "the camera stays fixed, tilting only slightly, the blizzard always in frame"
REQUIRED = ("blizzard", "freez", "high vantage", "normal lens", "no blood", "never glossy or CGI")
FORBIDDEN = ("storm's eye", "circular hole", "fountain", "far below the camera", "pans to follow", "Full action",
             "Until the last frame", "blood-", "corpse", "dead")
# Eski (15 Kas ilk) metinler: pasif kayıtta birebir, aktif prompt'ta hiç yok
V1 = {
    "G5_V1": "a Rio de Janeiro avenue of palm trees and pastel buildings",
    "OPENING_V1": ("The storm's eye opens in the black sky above {place}, and a wall of white frost races down the "
                   "street toward the camera, freezing a fountain's spray in mid-air."),
    "PEOPLE_V1": {5: "Five people and a dog sprint toward the camera ahead of it.",
                  6: "Six people and a dog sprint toward the camera ahead of it."},
    "O1_V1": ("The frost catches the people and the dog mid-stride, freezing them solid into white ice statues, and a "
              "moving {vehicle} freezes white and slides sideways into a lamppost."),
    "O2_V1": ("The frost catches the people and the dog mid-stride, freezing them solid into white ice statues, and a "
              "{vehicle} freezes mid-turn and tips over onto its side."),
    "F2_V1": ("Right below the balcony, a tree and a row of parked cars freeze solid, the tree splitting with a crack, "
              "and white frost creeps up the railing in front of the camera."),
    "TAIL_V1": ("Handheld footage shot by a person standing on a high balcony across the street, normal lens; slight "
                "hand shake, the camera stays fixed, tilting only slightly, the storm's eye always visible in the sky; "
                "one continuous shot, no zoom, no cuts. Everything the frost touches freezes instantly and stays frozen "
                "white; frozen people stand still like statues, no blood, no injuries, no faces close to the camera. "
                "Raw natural light under a dark storm sky, never glossy or CGI. No readable signs or text. Everything "
                "moves in real time, never in slow motion, people run at full speed."),
    "TAIL_SHORTEN_V1": "No readable signs or text.",
    "WARNING_V1": "⚠️ Donma: insanlar ve köpek kanlı/yaralı değil, buz heykel gibi donmuş mu kontrol et.",
    "REQUIRED_V1": ("storm's eye", "freez", "normal lens", "no blood"),
    "FORBIDDEN_V1": ("pans to follow", "Full action", "Until the last frame", "blood-", "corpse", "dead"),
}
# 2. sürüm (15 Kas (2), göz halka) metinleri: pasif kayıtta birebir, aktif prompt'ta hiç yok
V2 = {
    "OPENING_V2": ("Above {place}, the storm's eye opens, a vast circular hole in the black clouds with a calm pale sky "
                   "inside the ring, and a wall of white frost races down the street toward the camera, freezing "
                   "everything it passes."),
    "PEOPLE_V2": {5: "Five people and a dog sprint down the middle of the street ahead of it.",
                  6: "Six people and a dog sprint down the middle of the street ahead of it."},
    "O1_V2": ("The frost catches the people and the dog mid-stride, far below the camera, freezing them solid into ice "
              "statues, and a moving {vehicle} freezes white and slides sideways into a lamppost."),
    "O2_V2": ("The frost catches the people and the dog mid-stride, far below the camera, freezing them solid into ice "
              "statues, and a {vehicle} freezes mid-turn and tips over onto its side."),
    "F2_V2": ("Right below the balcony, a tree and parked cars freeze solid, the tree splitting with a crack, and frost "
              "creeps up the railing in front of the camera."),
    "F3_V2": ("The frost wall hits the camera's building, ice racing up the facade and over the balcony railing as "
              "frost spreads across the edges of the frame."),
    "CAMERA_V2": "the camera stays fixed, tilting only slightly, the storm's eye always visible in the sky",
    "TAIL_V2": ("Handheld footage shot by a person standing on a high balcony across the street, high vantage looking "
                "down over the street, normal lens; slight hand shake, the camera stays fixed, tilting only slightly, "
                "the storm's eye always visible in the sky; one continuous shot, no zoom, no cuts. No funnel, no "
                "tornado. Everything the frost touches freezes instantly and stays frozen white; frozen people stand "
                "still like statues, no blood, no injuries, no faces close to the camera. Natural light under a dark "
                "sky, never CGI. Everything moves in real time, never in slow motion, people run at full speed."),
    "EVENT_LABEL_V2": "❄️ Fırtınanın gözü şehri dondurur",
    "WARNING_V2": ("⚠️ Donma: insanlar ve köpek kanlı/yaralı değil, buz heykel gibi donmuş mu kontrol et. "
                   "Kamera yüksekte mi, gökte huni değil halka şeklinde göz mü?"),
    "REQUIRED_V2": ("storm's eye", "circular hole", "freez", "high vantage", "normal lens", "No funnel", "no blood",
                    "far below the camera"),
    "FORBIDDEN_V2": ("fountain", "pans to follow", "Full action", "Until the last frame", "blood-", "corpse", "dead"),
    "WEATHER_V2": "yok (stil ekinde natural light under a dark sky)",
    "CONFIRM_DESC_V2": ("Fırtınanın gözü şehrin üstünde açılır, beyaz don caddeden kameraya doğru gelir; kaçan insanlar "
                        "ve köpek buz heykel gibi donar (kan yok), araç donup kayar ya da devrilir; final kameranın "
                        "balkonunda."),
}
EVENT_LABEL = "❄️ Buz fırtınası şehri dondurur"
CAMERA_LINE = "Kamera: hit kamerası (yüksek balkon, normal lens, sabit)"
WARNING = ("⚠️ Gerçekçilik: insanlar ve köpek donmadan önce gerçekten koşuyor mu (kaymıyor mu), kan/yara yok mu, "
           "kamera yüksekte mi, video yapay görünüyor mu?")
CONFIRM_DESC = ("Kar ve buz fırtınası cephesi caddeden kameraya doğru gelir; dokunduğu her şey anında beyaz donar. Kaçan "
                "insanlar ve köpek buz heykel gibi donar (kan yok), araç donup kayar ya da devrilir; final kameranın "
                "balkonunda.")
# Diğer 19 olay (normal yol) + 12 mod, 40 tohum: değişiklikten ÖNCEKİ kodla (4cbdd4f) üretilen kaydın SHA-256'sı
OTHERS_SHA256 = "d651fa4985c878bec19e64f0e248a540aaa40f9ce55f26241f1b88afc1898436"


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
    return asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": EVENT, "donma_firtina": True,
                                                     "used_combos": [], "recent_topics": [], **extra}))


def build(seed: int) -> dict:
    reset()
    random.seed(seed)
    return gen()


def expected(g, ppl, v, m, f) -> str:
    return (f"{OPENING.format(place=PLACES[g][1])} {PEOPLE[ppl]} {MIDS[m].format(vehicle=v)} {FINALS[f]} {TAIL}")


def all_combos():
    for g in DF["geos"]:
        for ppl in (5, 6):
            for v in DF["vehicles"]:
                for m in DF["mids"]:
                    for f in DF["finals"]:
                        yield (g, ppl, v, m, f), hp.donma_prompt(g, ppl, m, v, f)


def others_snapshot() -> dict:
    """Diğer 19 olay (normal yol, prompt_snapshot) + 12 mod; 40 tohum. Caption (tohumsuz rastgele) çıkarılır."""
    def strip(js):
        try:
            d = json.loads(js)
        except (TypeError, ValueError):
            return js
        d.pop("caption", None)
        return d

    def mode_run(flags, ev, seed):
        reset()
        random.seed(seed)
        try:
            with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT"))):
                d = asyncio.run(pg.generate_creative_prompts({"domain": None, "event": ev, **flags,
                                                             "used_combos": [], "recent_topics": []}))
        except Exception as e:   # noqa: BLE001 - davranış kaydı
            return {"error": f"{type(e).__name__}: {e}"}
        sc = d["scenes"][0]
        return {"prompt": sc["prompt"], "story": sc["story"], "suffix": sc["style_suffix"], "combo": d["combo_key"],
                "axes": strip(d.get("axes_json", ""))}
    out = {"events": {ev: {str(s): ps.snapshot_event(ev, s) for s in range(1, 41)} for ev in ps.active_events()},
           "modes": {}}
    modes = [(f"hit:{e}", {"hit_env": e}, es.FIRE_TORNADO) for e in hp.HIT_ENVS[es.FIRE_TORNADO]]
    modes += [(f"yaklasma:{e}", {"approach_env": e}, es.FIRE_TORNADO) for e in hp.yaklasma_envs(es.FIRE_TORNADO)]
    modes += [("dalga24", {"dalga24": True}, es.TIDAL), ("kul", {"kul_yaklasma": True}, es.PYROCLASTIC),
              ("orman", {"orman_yaklasma": True}, es.WILDFIRE), ("heli", {"heli_yaklasma": True}, es.HELICOPTER),
              ("hortum", {"hortum_yaklasma": True}, es.LANDFALL), ("cadde", {"cadde_yaklasma": True}, es.AVENUE)]
    for name, flags, ev in modes:
        out["modes"][name] = {str(s): mode_run(flags, ev, s) for s in range(1, 41)}
    return out


def snapshot_hash(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


class TestTexts(_Quiet):
    def test_verbatim_texts(self):
        self.assertEqual(hp.DONMA_MODE_LABEL, "❄️ Donduran fırtına")
        self.assertEqual(hp.DONMA_CATEGORY_LABEL, "❄️ Donduran fırtına")
        self.assertEqual(hp.DONMA_EVENT_LABEL, EVENT_LABEL)
        self.assertEqual(hp.DONMA_CONFIRM_DESC, CONFIRM_DESC)
        self.assertEqual(DF["camera"], CAMERA)
        self.assertEqual((hp.DONMA_EVENT, hp.DONMA_DOMAIN), (EVENT, DOMAIN))
        self.assertEqual({g: (DF["geos"][g]["name"], DF["geos"][g]["place"]) for g in DF["geos"]}, PLACES)
        a, b, c = es.SLICE_LABELS
        for g, (_, place) in PLACES.items():
            self.assertEqual(f"{a}: {hp.donma_opening(g)}", OPENING.format(place=place))
        for n, text in PEOPLE.items():
            self.assertEqual(hp.donma_people(n), text)
        for n in (2, 3, 4, 7):
            with self.assertRaises(es.StructureError):
                hp.donma_people(n)
        self.assertEqual(DF["vehicles"], VEHICLES)
        self.assertEqual({k: f"{b}: {v}" for k, v in DF["mids"].items()}, MIDS)
        self.assertEqual({k: f"{c}: {v}" for k, v in DF["finals"].items()}, FINALS)
        self.assertEqual(DF["vehicle_mids"], ("O1", "O2"))
        self.assertEqual(hp.donma_tail(), TAIL)
        self.assertEqual(DF["tail"], TAIL)
        self.assertFalse(hp.DONMA_SHORTENED)   # yedek kısaltma kullanılmadı (15 Kas (3): en uzun 214 kelime)
        self.assertEqual(hp.DONMA_TAIL_SHORTEN,
                         "Everything moves in real time, never in slow motion, people run at full speed.")
        self.assertEqual(hp.DONMA_TAIL_SHORTEN_TO, "People run at full speed.")
        self.assertIn(hp.DONMA_TAIL_SHORTEN, TAIL)
        with patch.object(hp, "DONMA_SHORTENED", True):   # yedek açılırsa yalnız bu cümle kısalır
            self.assertEqual(hp.donma_tail(), TAIL.replace(hp.DONMA_TAIL_SHORTEN, "People run at full speed."))
        self.assertEqual((hp.DONMA_GEO_BLOCK, hp.DONMA_VEHICLE_BLOCK, hp.DONMA_MID_BLOCK, hp.DONMA_FINAL_BLOCK),
                         (3, 2, 1, 1))
        self.assertEqual((hp.DONMA_MAX_WORDS, hp.DONMA_MAX_CHARS), (230, 1400))
        self.assertEqual(hp.DONMA_REQUIRED, REQUIRED)
        self.assertEqual(hp.DONMA_FORBIDDEN, FORBIDDEN)
        self.assertEqual(hp.DONMA_CAMERA_LINE, CAMERA_LINE)
        self.assertEqual(hp.DONMA_WARNING, WARNING)
        self.assertIn(hp.donma_camera_text(), TAIL)
        # sıra: açılış + insan + orta + final + stil eki
        self.assertEqual(hp.donma_prompt("G3", 6, "O2", "taxi", "F3"), expected("G3", 6, "taxi", "O2", "F3"))
        self.assertEqual(hp.donma_prompt("G1", 5, "O1", "city bus", "F1"),
                         "0-4s: A freezing blizzard front of dense, swirling snow and ice rolls down a New York avenue "
                         "of brownstone buildings toward the camera, and everything it swallows turns white with frost "
                         "in an instant, trees and parked cars freezing solid. Five people and a dog sprint toward the "
                         "camera ahead of it. 4-9s: The frost catches the people and the dog mid-stride, freezing them "
                         "solid into white ice statues, and a moving city bus freezes white and slides sideways into a "
                         "lamppost. 9-15s: Right across the street, the frost climbs the building, its windows bursting "
                         "white with ice, then ice races over the balcony railing in front of the camera. " + TAIL)
        # 1. sürüme dönüş: insan, O1, O2, F2 metinleri 1. sürümle birebir
        self.assertEqual(DF["people"], V1["PEOPLE_V1"])
        self.assertEqual((DF["mids"]["O1"], DF["mids"]["O2"], DF["finals"]["F2"]),
                         (V1["O1_V1"], V1["O2_V1"], V1["F2_V1"]))

    def test_vehicle_fill_and_bad_ids(self):
        for v in VEHICLES:
            for m in MIDS:
                self.assertEqual("4-9s: " + hp.donma_mid(m, v), MIDS[m].format(vehicle=v))
        for m in MIDS:
            with self.assertRaises(es.StructureError):
                hp.donma_mid(m, None)
            with self.assertRaises(es.StructureError):
                hp.donma_mid(m, "SUV")   # bu kategorinin havuzunda değil
        for bad in ("O3", "P6", "C1"):
            with self.assertRaises(es.StructureError):
                hp.donma_mid(bad, "taxi")
        for bad in ("F4", "Q3"):
            with self.assertRaises(es.StructureError):
                hp.donma_final(bad)
        with self.assertRaises(es.StructureError):
            hp.donma_opening("G7")

    def test_all_combos_within_limits(self):
        """216 kombinasyon: hepsi ≤ 230 kelime, ≤ 1400 karakter. 15 Kas (3) talimattaki hesap: en kısa 202 kelime, en
        uzun G5 + city bus + O1 + F2 = 214 kelime, en uzun karakter G5 + delivery van + O1 + F2 = 1232."""
        n, over = 0, []
        words, chars = [], []
        for key, p in all_combos():
            n += 1
            g, ppl, v, m, f = key
            w, c = len(p.split()), len(p)
            words.append((w, key))
            chars.append((c, key))
            if w > hp.DONMA_MAX_WORDS or c > hp.DONMA_MAX_CHARS:
                over.append((key, w, c))
            self.assertEqual(p, expected(g, ppl, v, m, f), key)
            self.assertEqual(sum(pl in p for _, pl in PLACES.values()), 1, key)
            self.assertEqual(hp.donma_camera_issues(p, g), [], key)
            self.assertTrue(p.endswith(" " + TAIL))
            for bad in FORBIDDEN + (sk.FULL_MOTION,):
                self.assertNotIn(bad.lower(), p.lower())
            for need in REQUIRED:
                self.assertIn(need.lower(), p.lower(), (key, need))
            self.assertNotIn("fountain", p.lower(), key)
            self.assertNotIn("storm's eye", p.lower(), key)
            # main.py zorunlu olay denetimi (iç anahtar "Storm's eye freezes the city"): blizzard = storm eş anlamlısı
            self.assertEqual(pg.event_fidelity_issues(EVENT, hp.donma_story(g, ppl, m, v, f)), [], key)
        self.assertEqual(n, 6 * 2 * 3 * 2 * 3)
        self.assertEqual(over, [])
        self.assertEqual(max(words)[0], 214)
        self.assertEqual(min(words)[0], 202)
        self.assertEqual(len(hp.donma_prompt("G5", 5, "O1", "city bus", "F2").split()), 214)
        self.assertEqual(max(chars)[0], 1232)
        self.assertEqual(max(chars)[1], ("G5", 5, "delivery van", "O1", "F2"))
        self.assertEqual(len(hp.donma_prompt("G5", 5, "O1", "delivery van", "F2")), 1232)
        self.assertLessEqual(max(chars)[0], 1400)

    def test_passive_texts_never_active(self):
        """_V1 (1. sürüm) ve _V2 (2. sürüm) metinleri DONMA_PASIF'te birebir. 2. sürüm metinlerinin ve 1. sürümün geri
        dönmeyen parçalarının (G5 uzun, açılış/fıskiye, eski stil eki) hiçbiri 216 aktif prompt'ta ve 40 tohumda yok."""
        self.assertEqual(hp.DONMA_PASIF, {**V1, **V2})
        marks = [V1["G5_V1"], *V1["OPENING_V1"].split("{place}"), V1["TAIL_V1"], "fountain's spray",
                 *V2["OPENING_V2"].split("{place}"), *V2["PEOPLE_V2"].values(),
                 *[t.split("{vehicle}")[0] for t in (V2["O1_V2"], V2["O2_V2"])], V2["F2_V2"], V2["F3_V2"],
                 V2["CAMERA_V2"], V2["TAIL_V2"], "frost wall", "No funnel", "circular hole", "far below the camera",
                 "storm's eye", "Natural light under a dark sky, never CGI", "middle of the street"]
        for _, p in all_combos():
            for m in marks:
                self.assertNotIn(m.lower(), p.lower(), m)
        for old in (V1["WARNING_V1"], V2["WARNING_V2"]):
            self.assertNotEqual(hp.DONMA_WARNING, old)
        self.assertNotEqual(hp.DONMA_EVENT_LABEL, V2["EVENT_LABEL_V2"])
        self.assertNotEqual(hp.DONMA_CONFIRM_DESC, V2["CONFIRM_DESC_V2"])
        self.assertNotEqual(hp.DONMA_WEATHER, V2["WEATHER_V2"])
        self.assertNotEqual(hp.DONMA_REQUIRED, V2["REQUIRED_V2"])
        self.assertTrue(set(V1["FORBIDDEN_V1"]) <= set(FORBIDDEN))   # eski yasaklar hâlâ yasak
        self.assertTrue(set(V2["FORBIDDEN_V2"]) <= set(FORBIDDEN))
        for gone in ("storm's eye", "circular hole", "far below the camera"):   # eski zorunlular artık yasak
            self.assertIn(gone, FORBIDDEN)
        for seed in range(1, 41):
            d = build(seed)
            p = d["scenes"][0]["prompt"]
            for m in marks:
                self.assertNotIn(m.lower(), p.lower(), (seed, m))
            shown = d["structure"]["donma_firtina"]["lines"].lower()
            for bad in ("storm's eye", "fountain", "fırtınanın gözü", "halka", "huni"):
                self.assertNotIn(bad, p.lower(), (seed, bad))
                self.assertNotIn(bad, shown, (seed, bad))

    def test_event_gate_synonym(self):
        """15 Kas (3): "stor" ← "bliz" eş anlamlısı (sadece ekleme). Normal hatta "stor" kökü taşıyan olay yok; blizzard
        geçmeyen ve sadece "freez" taşıyan bir metin hâlâ reddedilir."""
        self.assertEqual(pg._EVENT_SYNONYMS["stor"], {"bliz"})
        self.assertEqual([e for e in es.structured_events() if "stor" in pg._event_stems(e)], [])
        self.assertTrue(pg.event_fidelity_issues(EVENT, "The frost freezes everything on the street."))
        self.assertEqual(pg.event_fidelity_issues(EVENT, "A blizzard rolls in and freezes everything."), [])

    def test_no_eye_or_fountain_in_any_active_prompt(self):
        """ "storm's eye" ve "fountain" hiçbir aktif donma prompt'unda (216 kombinasyon + 40 tohum), stil ekinde,
        kamera metninde ve aktif metin havuzunda yok."""
        active = json.dumps({k: v for k, v in DF.items()}, ensure_ascii=False).lower()
        for bad in ("storm's eye", "fountain"):
            self.assertNotIn(bad, active)
            self.assertNotIn(bad, hp.donma_tail().lower())
            for _, p in all_combos():
                self.assertNotIn(bad, p.lower())
            for seed in range(1, 41):
                self.assertNotIn(bad, build(seed)["scenes"][0]["prompt"].lower(), seed)


class TestDonmaScene(_Quiet):
    def _check(self, d):
        sc, st = d["scenes"][0], d["structure"]
        tb = st["donma_firtina"]
        prompt = sc["prompt"]
        self.assertIn(tb["geo"], PLACES)
        self.assertIn(tb["vehicle"], VEHICLES)
        self.assertIn(tb["mid"], MIDS)
        self.assertIn(tb["final"], FINALS)
        self.assertIn(tb["people"], (5, 6))
        self.assertEqual(prompt, expected(tb["geo"], tb["people"], tb["vehicle"], tb["mid"], tb["final"]))
        self.assertEqual(sc["style_suffix"], TAIL)
        self.assertIn(PLACES[tb["geo"]][1], prompt)
        for need in REQUIRED:
            self.assertIn(need, prompt)
        for bad in FORBIDDEN:
            self.assertNotIn(bad.lower(), prompt.lower())
        self.assertLessEqual(len(prompt.split()), 230)
        self.assertLessEqual(len(prompt), 1400)
        self.assertEqual(d["combo_key"], f"{DOMAIN}|none|{EVENT.lower()}|high balcony across the street##"
                                         f"{tb['mid']}+{tb['final']}|bystander_handheld")
        self.assertEqual(cp.submit_issues(st, {"prompt": prompt, "story": sc["story"],
                                               "style_suffix": sc["style_suffix"]}), [])
        self.assertEqual((d["selection"]["domain_id"], d["selection"]["event"]), (DOMAIN, EVENT))
        return tb

    def test_40_seeds_no_error_and_no_gpt(self):
        """EK KONTROL: 40 tohumda hatasız; GPT (hikâye) hiç çağrılmaz, OpenAI istemcisi istenmez."""
        with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT çağrıldı"))) as gpt, \
             patch.object(pg, "_get_openai_client", side_effect=AssertionError("GPT istemcisi istendi")), \
             patch.object(cp, "build_creative_scene", AsyncMock(side_effect=AssertionError("normal hat"))) as normal:
            seen = set()
            for seed in range(1, 41):
                tb = self._check(build(seed))
                seen.add((tb["geo"], tb["mid"], tb["final"], tb["vehicle"], tb["people"]))
        gpt.assert_not_called()
        normal.assert_not_called()   # normal hat (build_creative_scene) hiç çalışmaz
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
            self.assertEqual(hp._DONMA_VEHICLE_MEMORY[-10:], v)
            self.assertEqual(hp._DONMA_GEO_MEMORY[-10:], g)
            geos |= set(g)
            mids |= {r["mid"] for r in runs}
            finals |= {r["final"] for r in runs}
        self.assertEqual(geos, set(PLACES))
        self.assertEqual(mids, set(MIDS))
        self.assertEqual(finals, set(FINALS))

    def test_history_sources(self):
        """Notion "Eksenler" kayıtları (iptaller dahil) varsa LRU oradan; okunamazsa süreç hafızası, üretim durmaz."""
        def rec(g, v, tag, event=EVENT, mod="donma_firtina"):
            return {"eksenler": json.dumps({"event": event, "axes": {"mod": mod, "cografya": g, "arac": v,
                                                                     "beats": tag}})}
        recs = [rec("G1", "taxi", "O1+F1"), rec("G2", "city bus", "O2+F2"), {"eksenler": "x"},
                rec("G3", "taxi", "O1+F3"), rec("G5", "delivery van", "O2+F1", event=es.AVENUE, mod="cadde_yaklasma")]
        self.assertEqual(hp.donma_axes_history(recs, "cografya"), ["G1", "G2", "G3"])
        self.assertEqual(hp.donma_axes_history(recs, "arac"), ["taxi", "city bus", "taxi"])
        self.assertEqual(hp.donma_axes_history(recs, "beats"), ["O1+F1", "O2+F2", "O1+F3"])
        self.assertIsNone(hp.donma_axes_history(None, "arac"))
        calls = []
        for seed in range(1, 11):
            reset()
            random.seed(seed)
            d = gen(axes_loader=lambda dom: calls.append(dom) or recs)
            tb = d["structure"]["donma_firtina"]
            self.assertIn(tb["geo"], ("G4", "G5", "G6"))   # son 3 (G1, G2, G3) elenir
            self.assertEqual(tb["vehicle"], "delivery van")   # son 2 (city bus, taxi) elenir
            self.assertEqual(tb["mid"], "O2")                 # son 1 (O1) elenir
            self.assertIn(tb["final"], ("F1", "F2"))          # son 1 (F3) elenir
            axes = json.loads(d["axes_json"])
            self.assertEqual(axes["event"], EVENT)
            self.assertEqual((axes["axes"]["mod"], axes["axes"]["cografya"], axes["axes"]["arac"],
                              axes["axes"]["beats"], axes["axes"]["kategori"]),
                             ("donma_firtina", tb["geo"], tb["vehicle"], f"{tb['mid']}+{tb['final']}",
                              "Donduran fırtına"))
            self.assertEqual(d["trace"]["axes_source"], "notion")
        self.assertEqual(set(calls), {DOMAIN})

        def broken(dom):
            raise RuntimeError("Notion yok")
        reset()
        random.seed(3)
        d = gen(axes_loader=broken)
        self.assertEqual(d["trace"]["axes_source"], "bellek")
        self._check(d)
        # combo geçmişi (Notion kaydı yoksa): orta/final son 1
        hist = [f"{DOMAIN}|none|{EVENT.lower()}|high balcony across the street##O2+F2|bystander_handheld"]
        for s in range(20):
            reset()
            tags = hp.donma_tags(hist)
            self.assertEqual(tags, ["O2+F2"])
            self.assertEqual(hp.donma_choose_mid(tags, random.Random(s)), "O1")
            self.assertIn(hp.donma_choose_final(tags, random.Random(s)), ("F1", "F3"))
        other = [f"coastal_tornado_landfall|none|{es.AVENUE.lower()}|x##O1+F2|bystander_handheld"]
        self.assertEqual(hp.donma_tags(other), [])   # cadde kaydı bu kategoriyi etkilemez

    def test_kie_final_check_required_and_forbidden(self):
        d = build(9)
        sc, st = d["scenes"][0], d["structure"]
        tb = st["donma_firtina"]
        info = {"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"]}
        self.assertEqual(cp.submit_issues(st, info), [])
        p0 = sc["prompt"]
        place = PLACES[tb["geo"]][1]
        other = PLACES["G2" if tb["geo"] != "G2" else "G3"][1]
        end = "people run at full speed."
        for need in REQUIRED:
            bad = p0.replace(need, "x").replace(need.capitalize(), "x")
            self.assertIn(f'"{need}" eksik', hp.donma_camera_issues(bad, tb["geo"]), need)
            self.assertTrue(cp.submit_issues(st, {**info, "prompt": bad}), need)
        self.assertIn("G1-G6 yer metni yok", hp.donma_camera_issues(p0.replace(place, "a city"), tb["geo"]))
        self.assertTrue(hp.donma_camera_issues(p0.replace(place, other), tb["geo"]))
        for bad in FORBIDDEN:
            text = p0.replace(end, end + f" {bad} x.")
            self.assertIn(f"bu kategoride olmayan ifade var: {bad}", hp.donma_camera_issues(text, tb["geo"]), bad)
            self.assertTrue(hp.donma_issues(st, {**info, "prompt": text}), bad)
            self.assertTrue(cp.submit_issues(st, {**info, "prompt": text}), bad)
        # büyük/küçük harf fark etmez
        self.assertTrue(hp.donma_camera_issues(p0 + " DEAD.", tb["geo"]))
        self.assertTrue(hp.donma_camera_issues(p0 + " the camera Pans To Follow.", tb["geo"]))
        for bad in ({"geo": "G7"}, {"mid": "P6"}, {"mid": "O3"}, {"final": "Q3"}, {"people": 4},
                    {"mid": "O1", "vehicle": None}, {"vehicle": "SUV"}):
            self.assertTrue(cp.submit_issues({**st, "donma_firtina": {**tb, **bad}}, info), bad)
        self.assertTrue(cp.submit_issues(st, {**info, "style_suffix": "x"}))
        self.assertTrue(cp.submit_issues(st, {**info, "prompt": p0.replace("4-9s: ", "")}))
        # Kie reddi sonrası yeni yazım yok: aynı hikâye döner, GPT çağrılmaz
        story = asyncio.run(cp.rewrite_structured(st, "test", AsyncMock(side_effect=AssertionError("GPT"))))
        self.assertEqual(story, sc["story"])
        self.assertIn("yeniden yazım yok", st["rewrite_log"][-1]["result"])
        with patch.object(hp, "DONMA_REQUIRED", REQUIRED + ("olmayan ifade",)):
            reset()
            random.seed(9)
            with self.assertRaises(es.StructureError):
                gen()

    def test_approval_lines_and_display(self):
        seen = set()
        for seed in range(1, 41):
            d = build(seed)
            sc, st = d["scenes"][0], d["structure"]
            tb = st["donma_firtina"]
            lines = tb["lines"].split("\n")
            self.assertEqual(lines[:8], [
                "Mod: ❄️ Donduran fırtına",
                f"Coğrafya: {tb['geo']} {PLACES[tb['geo']][0]}",
                f"Araç: {tb['vehicle']}",
                f"Orta (4-9s): {tb['mid']} «{MIDS[tb['mid']].format(vehicle=tb['vehicle'])[6:]}»",
                f"Final (9-15s): {tb['final']} «{FINALS[tb['final']][7:]}»",
                f"Kişi: {tb['people']}",
                CAMERA_LINE,
                f"Kelime: {len(sc['prompt'].split())} (en fazla 230) · karakter: {len(sc['prompt'])} (en fazla 1400)"])
            self.assertTrue(lines[8].startswith("Eksenler (❄️ Donduran fırtına): "), lines[8])
            for part in (f"coğrafya={tb['geo']} {PLACES[tb['geo']][0]}", f"araç={tb['vehicle']}", f"orta={tb['mid']}",
                         f"final={tb['final']}", f"kişi={tb['people']}"):
                self.assertIn(part, lines[8])
            self.assertTrue(lines[9].startswith("Tekrar önleme: coğrafya son 3 elendi · araç son 2 · orta son 1 · "
                                                "final son 1"), lines[9])
            self.assertEqual(lines[10], WARNING)
            self.assertEqual(len(lines), 11)
            seen.add(tb["mid"])
            shown = sections_to_text(format_generation(d["trace"], {"domain": "❄️ Donduran fırtına",
                                                                    "event": hp.DONMA_EVENT_LABEL}))
            self.assertIn(hp.DONMA_WEATHER, shown)
            self.assertIn("Mod: ❄️ Donduran fırtına", shown)
            self.assertIn("Hikâye: kod (birebir) · ❄️ Donduran fırtına", shown)
            self.assertNotIn("GPT'ye verildi", shown)
            _, body = format_final_prompt({"prompt": sc["prompt"], "story": sc["story"],
                                           "style_suffix": sc["style_suffix"], "hit_lines": tb["lines"],
                                           "story_source": st["story_source"], "axes_line": st["axes_line"]})
            self.assertIn("\nMod: ❄️ Donduran fırtına\n", body)
            self.assertEqual(body.count("Eksenler (❄️ Donduran fırtına)"), 1)   # eksenler satırı bir kez
            self.assertIn(WARNING, body)
            self.assertIn("\n\n" + sc["prompt"], body)
        self.assertEqual(seen, {"O1", "O2"})

    def test_notion_category_and_caption(self):
        """Notion üretim kaydında "Kategori" alanı yok: kategori "Eksenler" JSON'unda metin olarak (seçenek gerekmez);
        Paylaşımlar "Kategori" select'i caption'dan ("Donduran fırtına", seçenek ilk yazımda oluşur). Caption diğer
        olaylardaki gibi çalışır (GPT yok, şablon)."""
        self.assertEqual(hp.DONMA_NOTION_CATEGORY, "Donduran fırtına")
        self.assertEqual(cap.SHARE_CATEGORY[EVENT], "Donduran fırtına")
        self.assertEqual(cap.TAG_POOL[EVENT], "donma")
        for seed in range(1, 11):
            d = build(seed)
            self.assertEqual(json.loads(d["axes_json"])["axes"]["kategori"], "Donduran fırtına")
            c = d["caption"]
            self.assertIsNotNone(c)
            self.assertEqual(c["category"], "Donduran fırtına")
            self.assertEqual(len(c["hashtags"]), 5)
            broad, special = cap.event_tags(EVENT)
            self.assertTrue(set(c["hashtags"]) <= set(broad) | set(special))
            self.assertTrue(d["caption_block"])
            self.assertEqual(json.loads(d["axes_json"])["caption"]["category"], "Donduran fırtına")
            self.assertTrue(d["youtube_title"].endswith(" #Shorts"))
        # 🔄 Yeni caption (bot) aynı fonksiyonla: GPT yok
        st = d["caption_state"]
        c2 = cap.choose(st["event"], st["info"], st["candidates"], st["ctx"] or {}, random.Random(1),
                        exclude_titles=st["shown"])
        self.assertEqual(c2["category"], "Donduran fırtına")


class TestDonmaPipelineAndBot(_Quiet):
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
                return await orig(**{**kw, "domain": DOMAIN}, donma_firtina=True)
            with patch.object(main, "run_pipeline", run_with):
                r = t.run_pipe(gen=AsyncMock(side_effect=fake_gen), reporter=rep, event=EVENT, poll=poll)
        finally:
            t.doCleanups()
        return r, rep, seen, t

    def test_pipeline_passes_flag_and_sends_prompt(self):
        r, rep, seen, t = self._run()
        self.assertTrue(r["success"], r)
        self.assertIs(seen["config"]["donma_firtina"], True)
        self.assertEqual((seen["config"]["domain"], seen["config"]["event"]), (DOMAIN, EVENT))
        approve = [c[1] for c in rep.calls if c[0] == "approve"]
        self.assertEqual(len(approve), 1)   # Kie'ye göndermeden önce ✋ Onay
        info = approve[0]
        self.assertTrue(info["hit_lines"].startswith("Mod: ❄️ Donduran fırtına\nCoğrafya: G"))
        self.assertIn(WARNING, info["hit_lines"])
        self.assertEqual(t.create.await_count, 1)
        self.assertEqual(t.create.await_args.args[1], info["prompt"])   # Kie'ye giden = onaydaki
        axes = [c.args[0] for c in t.tracker.record_axes.call_args_list]
        self.assertEqual(json.loads(axes[0])["axes"]["kategori"], "Donduran fırtına")

    def test_kie_rejection_existing_behavior_and_message(self):
        """Kie içerik filtresi reddederse mevcut davranış: yapılandırılmış hatta tek tekrar (aynı hikâye, yeni yazım
        yok), ikinci retta akış durur; ret nedeni sonuca (Telegram) açıkça düşer."""
        from infrastructure.kie_client import ContentFilterError
        poll = AsyncMock(side_effect=ContentFilterError("İçerik filtresi: prohibited content"))
        r, rep, _, t = self._run(poll=poll)
        self.assertFalse(r["success"])
        self.assertEqual(r["reason"], "structure_check")
        self.assertIn("Kie içerik filtresi", r["error"])
        self.assertIn("prohibited content", r["error"])
        self.assertEqual(t.create.await_count, 2)   # mevcut davranış: aynı prompt bir kez daha
        self.assertEqual(t.create.await_args_list[0].args[1], t.create.await_args_list[1].args[1])

    def test_bot_rejection_message_shown(self):
        import bot
        from test_tur29_infra import _context
        ctx = _context()
        runner = AsyncMock(return_value={"success": False, "reason": "structure_check",
                                         "error": "Kie'ye gönderilmedi: Kie içerik filtresi yeniden yazımdan sonra da "
                                                  "reddetti: İçerik filtresi: prohibited content"})
        with patch.object(bot.pipeline, "run_pipeline", runner):
            asyncio.run(bot.produce(ctx.bot, 1, DOMAIN, EVENT, cfg=bot.default_cfg(), bot_data={}, donma_firtina=True))
        texts = " ".join(str(c.kwargs.get("text") or (c.args[1] if len(c.args) > 1 else ""))
                         for c in ctx.bot.send_message.await_args_list)
        self.assertIn("Kie içerik filtresi", texts)
        self.assertIn("prohibited content", texts)
        self.assertEqual(runner.await_args.kwargs["reporter"].labels,
                         {"domain": "❄️ Donduran fırtına", "event": EVENT_LABEL})

    def test_bot_button_and_flow(self):
        import bot
        from test_tur29_infra import _context, _update
        kb = bot.domain_keyboard(bot.default_cfg())
        texts = [b.text for r in kb.inline_keyboard for b in r]
        self.assertEqual(texts.count("❄️ Donduran fırtına"), 1)
        row = next(r for r in kb.inline_keyboard if r[0].text == "❄️ Donduran fırtına")
        self.assertEqual((len(row), row[0].callback_data), (1, "uret:df"))
        self.assertNotIn(DOMAIN, bot.DOMAIN_KEYS)   # normal kategori sıra numaraları değişmez
        self.assertNotIn(EVENT, bot.EVENT_LABELS)
        ctx = _context()
        upd = _update(data="uret:df")
        asyncio.run(bot.on_callback(upd, ctx))
        call = upd.callback_query.edit_message_text.await_args
        self.assertIn("❄️ Donduran fırtına", call.args[0])
        labels = [b.text for r in call.kwargs["reply_markup"].inline_keyboard for b in r]
        self.assertEqual(labels, [EVENT_LABEL, "🔙 Geri"])
        cbs = [b.callback_data for r in call.kwargs["reply_markup"].inline_keyboard for b in r]
        self.assertEqual(cbs, ["uret:dfe", "uret:back"])
        upd = _update(data="uret:dfe")
        asyncio.run(bot.on_callback(upd, ctx))
        call = upd.callback_query.edit_message_text.await_args
        text = call.args[0]
        for part in ("Kategori: ❄️ Donduran fırtına", f"Olay: {EVENT_LABEL}",
                     "Mod: ❄️ Donduran fırtına", CAMERA_LINE, "✋ Onay", CONFIRM_DESC):
            self.assertIn(part, text)
        for gone in ("gözü", "Fırtınanın", "halka"):
            self.assertNotIn(gone, text)
        self.assertEqual([b.text for r in call.kwargs["reply_markup"].inline_keyboard for b in r], ["✅ Üret", "❌ İptal"])
        upd = _update(data="uret:dfok")
        runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
        with patch.object(bot.pipeline, "run_pipeline", runner), patch.object(bot, "_production_lock", asyncio.Lock()):
            asyncio.run(bot.on_callback(upd, ctx))
        kw = runner.await_args.kwargs
        self.assertEqual((kw["domain"], kw["event"], kw["donma_firtina"]), (DOMAIN, EVENT, True))
        for other in ("cadde_yaklasma", "hortum_yaklasma", "heli_yaklasma", "kul_yaklasma", "orman_yaklasma",
                      "dalga24", "approach_env", "hit_env"):
            self.assertNotIn(other, kw)
        self.assertTrue(kw["reporter"].needs_approval)
        started = upd.callback_query.edit_message_text.await_args_list[0].args[0]
        self.assertIn(f"🚀 Üretim başladı: ❄️ Donduran fırtına / {EVENT_LABEL}", started)
        self.assertEqual(bot.CODE_EVENT_LABELS[EVENT], EVENT_LABEL)   # sadece etiket; iç anahtar aynı
        self.assertEqual(set(bot.CODE_EVENT_LABELS), {EVENT, hp.KASIRGA_EVENT})   # 15 Kas (4): + 🌀 Kasırga
        for bad in ("uret:df:1", "uret:dfe:0", "uret:dfok:x"):
            upd = _update(data=bad)
            asyncio.run(bot.on_callback(upd, ctx))
            self.assertIn("Geçersiz", upd.callback_query.edit_message_text.await_args.args[0])
        busy = asyncio.Lock()
        asyncio.run(busy.acquire())
        with patch.object(bot, "_production_lock", busy):
            upd = _update(data="uret:dfok")
            asyncio.run(bot.on_callback(upd, ctx))
            self.assertEqual(upd.callback_query.edit_message_text.await_args.args[0], bot.BUSY_TEXT)
        for b in (b for m in (kb, bot.donma_event_keyboard(), bot.donma_produce_keyboard())
                  for r in m.inline_keyboard for b in r):
            self.assertLessEqual(len(b.callback_data.encode()), 64)


class TestOthersUntouched(_Quiet):
    """Diğer 19 olay ve bütün modlar: 40 tohum prompt / hikâye / stil eki / combo / eksenler birebir (önceki kod)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.snap = others_snapshot()

    def test_other_prompts_verbatim_40_seeds(self):
        self.assertEqual(len(self.snap["events"]), 19)
        self.assertEqual(len(self.snap["modes"]), 12)
        self.assertNotIn(EVENT, self.snap["events"])
        self.assertEqual(snapshot_hash(self.snap), OTHERS_SHA256)

    def test_sentences_only_in_this_category(self):
        marks = ["A freezing blizzard front of dense, swirling snow", *PEOPLE.values(),
                 *[t.split("{vehicle}")[1] for t in DF["mids"].values()],
                 "The frost catches the people and the dog mid-stride", *DF["finals"].values(), TAIL,
                 DF["camera"], *[p for _, p in PLACES.values()], "storm's eye", "frost", "freez"]
        pools = json.dumps({e: {s: {k: v["text"] for k, v in b[s].items()} for s in ("slice_2", "slice_3")}
                            for e, b in es.EVENT_BEATS.items()}, ensure_ascii=False)
        others = pools + json.dumps(es.EVENT_KEY_VISUAL, ensure_ascii=False)
        for name in ("HIT_PROMPTS", "YAKLASMA_ATES_HORTUMU", "DALGA_24EYLUL", "YAKLASMA_KUL_BULUTU", "KUL_PASIF",
                     "YAKLASMA_ORMAN", "ORMAN_PASIF", "YAKLASMA_HELIKOPTER", "YAKLASMA_HORTUM", "HORTUM_PASIF",
                     "YAKLASMA_CADDE", "CADDE_PASIF"):
            others += json.dumps(getattr(hp, name), default=str, ensure_ascii=False)
        others += json.dumps(self.snap, ensure_ascii=False)
        for m in marks:
            self.assertNotIn(m, others, m)

    def test_locked_events_hash_file(self):
        import locked_prompts as lp
        now = lp.hashes()
        saved = lp.load()
        self.assertEqual(now, saved)


if __name__ == "__main__":
    unittest.main()
