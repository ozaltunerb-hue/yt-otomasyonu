# 17 Kas 2026, Bahadır: yeni kategori "🌍 Yer yarılması" (2012 filmi esinli), tek olay "🌍 Cadde yarılır"
# (core/hit_prompts.py YER_YARILMASI). KASIRGA ile aynı kod-hikâye yolu: GPT yok, hikâye koddan birebir.
# Prompt = AÇILIŞ + " " + ORTA + " " + FİNAL + " " + STİL; metinler talimattan birebir (aşağıda bağımsız kopya).
# Coğrafya G1-G6 (son 3), orta O1-O2 (son 1), final F1-F2 (son 1). Diğer 19 olay ve 15 mod birebir aynı (40 tohum).
# 18 Kas v3: ilk saniyede yarılma (düzensiz yarık), tek orta O2 (otobüs), tek final F1 (bina); O1/F2 pasif (_PASIF),
# v2 açılış/stil/orta/final _V2 pasif kopya. Coğrafya havuzu ve LRU (son 3) aynen.
# 18 Kas v4: yatay yarık (soldan sağa, kameranın önünden), köşe binası çatı terası (çapraz), tek orta O3 (otobüs),
# tek final F3 (köşe binası kadrajda büyük); v3 açılış/orta/final/stil/listeler/etiket _V3 pasif kopya.
# 25 Kas v5 (AKTİF sürüm: tests/test_yer_yarilmasi_v5.py): v4 silinmedi, config "yer_yarilmasi_surum": "v4" ile aynen
# çalışır; bu dosya v4 kalıbını ve 40 tohum kilidini korur (menü testi v5 dosyasında).
# Ağ yok, Kie yok, GPT yok.
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
import core.caption as cap   # noqa: E402
import core.hit_prompts as hp   # noqa: E402
import core.prompt_generator as pg   # noqa: E402
import prompt_snapshot as ps   # noqa: E402
from core.trace_format import format_final_prompt, format_generation, sections_to_text   # noqa: E402

EVENT = "Earthquake fissure splits a city avenue"
DOMAIN = "fissure_disasters"
EVENT_LABEL = "🌍 Cadde yarılır"
CATEGORY = "🌍 Yer yarılması"
MODE_LABEL = "Yer yarılması · kod hikâye (v4: yatay yarık + köşe terası)"   # 18 Kas v4
MODE_LABEL_V3 = "Yer yarılması · kod hikâye (v3: ilk saniyede yarılma + otobüs + bina)"
MODE_LABEL_V2 = "Yer yarılması · kod hikâye (v2: açık yarık + balkon kilidi)"
MODE_LABEL_V1 = "Yer yarılması · kod hikâye"
CAMERA_LINE = "Kamera: köşe binanın çatı terası, çapraz açı, normal lens, sabit, korkuluk kadrajın altında"
SPOT = "rooftop terrace of a corner building"
# Talimat metinleri, birebir (18 Kas v4: ilk kareden yatay yarık, köşe terası, otobüs + köşe binası)
OPENING = ("0-4s: From the very first frame {place} is breaking apart: a wide, jagged earthquake fissure cuts across "
           "the street from left to right in front of the camera, asphalt slabs dropping into it as it keeps "
           "widening. People sprint away from its edges.")
OPENING_V3 = ("In the very first second {place} violently splits open down the middle, slabs of asphalt heaving up "
              "as a long, jagged earthquake fissure tears toward the camera. Five or six people sprint away along the "
              "sidewalks.")
OPENING_V2 = ("A massive earthquake fissure has already torn open down the middle of {place}, a long, straight chasm "
              "running down the length of the avenue, its edges still collapsing as it keeps ripping wider toward the "
              "camera. Five or six people sprint away along the sidewalks as the ground drops behind them.")
OPENING_V1 = ("A massive earthquake fissure rips open down the middle of {place}, the asphalt splitting apart and "
              "collapsing into a deep, wide chasm that races along the avenue toward the camera. Five or six people "
              "sprint away along the sidewalks as the ground drops behind them.")
PLACES = {
    "G1": "a wide palm-lined boulevard in a Southern Californian city",
    "G2": "a busy downtown avenue of brick buildings and glass towers in an American city",
    "G3": "a busy avenue of colonial-style buildings and jacaranda trees in Mexico City",
    "G4": "a crowded avenue of tall apartment blocks in São Paulo",
    "G5": "a busy avenue of Santiago with the Andes rising behind it",
    "G6": "a busy shopping street lined with narrow buildings in a Japanese city",
}
MIDS = {
    "O3": "4-9s: A city bus brakes at the edge, tilts sideways and topples into the fissure in a burst of dust as more "
          "road breaks off.",
}
FINALS = {
    "F3": "9-15s: The corner building on the far edge, big in frame, tilts and collapses into the fissure in a roar of "
          "dust.",
}
MIDS_V3 = {
    "O2": "A city bus on the edge tilts sideways and topples into the fissure in a burst of dust.",
}
FINALS_V3 = {
    "F1": "The front of a building on the far side leans out and collapses into the fissure in a roar of dust and "
          "debris.",
}
MIDS_V2 = {
    "O1": "Parked cars along the edge tip over and slide nose-first into the chasm, one after another.",
    "O2": "A city bus at the edge tilts sideways and topples into the chasm in a burst of dust.",
}
FINALS_V2 = {
    "F1": "The front of a building on the far side of the chasm leans out and collapses into it in a roar of dust "
          "and debris.",
    "F2": "A whole section of the avenue, cars still on it, drops straight down into the chasm.",
}
STYLE = ("Handheld footage shot by a person standing on the rooftop terrace of a corner building diagonally across "
         "the street, normal lens; slight hand shake, the camera stays fixed on the fissure, shaking with the quake; no "
         "zoom, no cuts. The terrace railing stays at the bottom of the frame the whole time; the camera never moves "
         "forward or tilts down into the fissure. The ground keeps shaking and the fissure keeps widening the whole "
         "time, never a calm moment. Real earthquake footage: irregular broken asphalt, soil and rock, never thin "
         "drawn cracks, never glossy or CGI; no lava, no fire, no glowing light, no explosions. No readable signs or "
         "text. Everything moves in real time, never in slow motion, people run at full speed.")
STYLE_V3 = ("Handheld footage shot by a person standing on a high balcony across the avenue, normal lens; slight hand "
         "shake, the camera stays fixed on the avenue, shaking with the quake; no zoom, no cuts. The balcony railing "
         "stays at the bottom of the frame the whole time; the camera never moves forward or tilts down into the "
         "fissure. The ground keeps shaking and the fissure keeps tearing wider the whole time, never a calm moment. "
         "Real earthquake footage: irregular broken asphalt, soil and rock, never a clean straight trench, never "
         "glossy or CGI; no lava, no fire, no glowing light, no explosions, no flood water. No readable signs or "
         "text. Everything moves in real time, never in slow motion, people run at full speed.")
STYLE_V2 = ("Handheld footage shot by a person standing on a high balcony across the avenue, eye level, normal lens; "
         "slight hand shake, the camera stays fixed on the avenue, shaking with the quake; no zoom, no cuts. "
         "The balcony railing stays at the bottom of the frame the whole time; the camera never moves forward or "
         "tilts down into the chasm. Bystanders wear everyday clothes. Raw natural daylight, dust in the air, "
         "never glossy or CGI. A real earthquake fissure of torn asphalt, soil and rock, no lava, no fire, no glowing "
         "light, no explosions, no flood water. No readable signs or text. Everything moves in real time, never in "
         "slow motion, people run at full speed.")
STYLE_V1 = ("Handheld footage shot by a person standing on a high balcony across the avenue, eye level, normal lens; "
         "slight hand shake, the camera stays fixed on the avenue, shaking with the quake; no zoom, no cuts. "
         "Bystanders wear everyday clothes, never hi-vis PPE on civilians. Raw natural daylight, dust in the air, "
         "never glossy or CGI. A real earthquake fissure of torn asphalt, soil and rock, no lava, no fire, no glowing "
         "light, no explosions, no flood water. No readable signs or text. Everything moves in real time, never in "
         "slow motion, people run at full speed.")
REQUIRED = ("very first frame", "jagged earthquake fissure", "from left to right", "rooftop terrace of a corner building",
            "diagonally across the street", "normal lens", "terrace railing stays", "never moves forward",
            "never a calm moment", "big in frame", "never thin drawn cracks")
FORBIDDEN = ("tornado", "funnel", "tsunami", "drone", "aerial", "slow-motion", "sinkhole", "crater", "trench",
             "has already torn open", "straight chasm", "very first second", "splits open", "balcony", "parked cars",
             "section of the avenue")
REQUIRED_V3 = ("very first second", "jagged earthquake fissure", "high balcony", "normal lens", "balcony railing stays",
               "never moves forward", "never a calm moment")
FORBIDDEN_V3 = ("tornado", "funnel", "tsunami", "drone", "aerial", "slow-motion", "sinkhole", "crater",
                "has already torn open", "straight chasm", "parked cars", "section of the avenue")
REQUIRED_V2 = ("earthquake fissure", "chasm", "high balcony", "normal lens", "has already torn open",
               "long, straight chasm", "balcony railing stays", "never moves forward")
FORBIDDEN_V2 = ("tornado", "funnel", "tsunami", "drone", "aerial", "slow-motion", "sinkhole", "crater", "rips open")
# v2 (8b4341f) 40 tohumun coğrafya seçimleri (tohum 1-40, G1-G6 rakamı): v3'te birebir aynı kalmalı
V2_GEOS = "2122553245443123526622364661551155536624"
# Değişiklikten önceki kod (a4d9673): 19 olay (normal yol) + 13 mod + 🌀 Kasırga + ⭐ Hit kopyası, 40 tohum
OTHERS_SHA256 = "608f98ca3e858ea0192ba221ea34be82d2f8c49b3572c2312974b6b24b8c353f"
# 🌍 Yer yarılması kendi 40 tohum kilidi (prompt / hikâye / stil eki / combo / eksenler)
YY_SHA256 = "14a7c6076280c10b1679f21b781df33f28caff7b101ea8b2d221e5489ce9c195"      # 18 Kas v4
YY_V3_SHA256 = "99c49edd54ed8e199503487e7ae02d9beba87f289648910771b0a76ad77106cb"   # 816dc36 (v3)
YY_V2_SHA256 = "c31ea61471a8edd6753fa16eb845e7e68116ba61e9e6bb413e942909e7889e14"   # 8b4341f (v2)
YY_V1_SHA256 = "8ee10bac6fb9fb6c6add729e93ee2b786784eaf5998f71e2f131af3037cada63"   # 318ee24 (v1)


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
    return asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": EVENT, "yer_yarilmasi": True,
                                                     "yer_yarilmasi_surum": "v4",   # 25 Kas: aktif sürüm v5
                                                     "used_combos": [], "recent_topics": [], **extra}))


def build(seed: int) -> dict:
    reset()
    random.seed(seed)
    return gen()


def expected(g: str, m: str, f: str) -> str:
    return OPENING.format(place=PLACES[g]) + " " + MIDS[m] + " " + FINALS[f] + " " + STYLE


def all_combos():
    for g in PLACES:
        for m in MIDS:
            for f in FINALS:
                yield (g, m, f), hp.yer_yarilmasi_prompt(g, m, f)


def others_snapshot() -> dict:
    """test_hit_kopya_ates kaydı (19 olay + 13 mod + 🌀 Kasırga) + ⭐ Hit kopyası (ateş hortumu); 40 tohum."""
    import test_hit_kopya_ates as th
    snap = th.others_snapshot()
    # 26 Kas 2026: ⭐ Hit kopyası (ateş hortumu) v3 bilerek değişti. Bu kilit diğer olay/modlar içindir; ateş hortumu
    # kaydı v2 (17 Kas a4d9673) fixture'ından gelir (th.FIXTURE_V2), canlı v3 test_hit_kopya_ates ile kilitli.
    with open(th.FIXTURE_V2, encoding="utf-8") as fh:
        snap["modes"]["hit_kopya_ates"] = json.load(fh)
    return snap


def yy_snapshot() -> dict:
    """🌍 Yer yarılması 40 tohum: prompt, hikâye, stil eki, combo, eksenler (caption hariç)."""
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


def snapshot_hash(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


class TestTemplate(_Quiet):
    def test_texts_verbatim(self):
        self.assertEqual((hp.YER_YARILMASI_EVENT, hp.YER_YARILMASI_DOMAIN), (EVENT, DOMAIN))
        self.assertEqual(hp.YER_YARILMASI_MODE_LABEL, MODE_LABEL)
        self.assertEqual(hp.YER_YARILMASI_CATEGORY_LABEL, CATEGORY)
        self.assertEqual(hp.YER_YARILMASI_EVENT_LABEL, EVENT_LABEL)
        self.assertEqual(hp.YER_YARILMASI_NOTION_CATEGORY, "Yer yarılması")
        self.assertEqual({g: v["place"] for g, v in hp.YER_YARILMASI["geos"].items()}, PLACES)
        self.assertEqual(hp.yer_yarilmasi_tail(), STYLE)
        a, b, c = es.SLICE_LABELS
        for g, place in PLACES.items():
            self.assertEqual(f"{a}: {hp.yer_yarilmasi_opening(g)}", OPENING.format(place=place))
        for m, t in MIDS.items():
            self.assertEqual(f"{b}: {hp.yer_yarilmasi_mid(m)}", t)
        for f, t in FINALS.items():
            self.assertEqual(f"{c}: {hp.yer_yarilmasi_final(f)}", t)
        self.assertEqual((hp.YER_YARILMASI_GEO_BLOCK, hp.YER_YARILMASI_MID_BLOCK, hp.YER_YARILMASI_FINAL_BLOCK),
                         (3, 1, 1))
        self.assertEqual((hp.YER_YARILMASI_MAX_WORDS, hp.YER_YARILMASI_MAX_CHARS), (230, 1400))
        self.assertEqual(hp.YER_YARILMASI_REQUIRED, REQUIRED)
        self.assertEqual(hp.YER_YARILMASI_FORBIDDEN, FORBIDDEN)
        self.assertEqual(hp.YER_YARILMASI_CAMERA_LINE, CAMERA_LINE)
        self.assertEqual(hp.YER_YARILMASI_SPOT, SPOT)
        for bad in ("G7",):
            with self.assertRaises(es.StructureError):
                hp.yer_yarilmasi_opening(bad)
        for bad in ("O4", "O1", "O2"):   # pasif (O1, v3 O2) beat aktif yoldan istenemez
            with self.assertRaises(es.StructureError):
                hp.yer_yarilmasi_mid(bad)
        for bad in ("F4", "F1", "F2"):   # pasif (F2, v3 F1)
            with self.assertRaises(es.StructureError):
                hp.yer_yarilmasi_final(bad)
        self.assertNotIn("—", hp.YER_YARILMASI_CONFIRM_DESC + hp.YER_YARILMASI_WARNING
                         + hp.YER_YARILMASI_CAMERA_LINE)   # em-dash yok

    def test_all_6_combos_within_limits(self):
        """v4: 6 coğrafya × 1 orta × 1 final = 6: hepsi ≤ 230 kelime, ≤ 1400 karakter (222-227 kelime, 1256-1280
        karakter, yedek kısaltma gerekmedi); zorunlu ifadelerin hepsi var, yasakların hiçbiri yok; olay kapısı eş
        anlamlısız geçer."""
        n, words, chars = 0, [], []
        for key, p in all_combos():
            n += 1
            g, m, f = key
            self.assertEqual(p, expected(g, m, f), key)
            w, c = len(p.split()), len(p)
            words.append(w)
            chars.append(c)
            self.assertLessEqual(w, 230, key)
            self.assertLessEqual(c, 1400, key)
            low = p.lower()
            for need in REQUIRED:
                self.assertIn(need, low, (key, need))
            for bad in FORBIDDEN:
                self.assertNotIn(bad, low, (key, bad))
            self.assertEqual(sum(pl in p for pl in PLACES.values()), 1, key)
            self.assertEqual(hp.yer_yarilmasi_camera_issues(p, g), [], key)
            self.assertEqual(pg.event_fidelity_issues(EVENT, hp.yer_yarilmasi_story(g, m, f)), [], key)
            self.assertEqual(pg.event_fidelity_issues(EVENT, p), [], key)
        self.assertEqual(n, 6)
        self.assertEqual((min(words), max(words)), (222, 227))
        self.assertEqual((min(chars), max(chars)), (1256, 1280))
        self.assertEqual(len(hp.yer_yarilmasi_prompt("G2", "O3", "F3").split()), 227)
        self.assertEqual(len(hp.yer_yarilmasi_prompt("G2", "O3", "F3")), 1280)
        self.assertIn("No readable signs or text.", STYLE)   # yedek kısaltma kullanılmadı

    def test_v1_v2_v3_passive_copies(self):
        """v1, v2 ve v3 açılış/stil/etiket/orta/final silinmedi, pasif kopya; O1 ve F2 pasif beat; hiçbir aktif yol
        kullanmaz, seçilmez."""
        self.assertEqual(hp.YER_YARILMASI_OPENING_V3, OPENING_V3)
        self.assertEqual(hp.YER_YARILMASI_TAIL_V3, STYLE_V3)
        self.assertEqual(hp.YER_YARILMASI_MODE_LABEL_V3, MODE_LABEL_V3)
        self.assertEqual(hp.YER_YARILMASI_MIDS_V3, MIDS_V3)
        self.assertEqual(hp.YER_YARILMASI_FINALS_V3, FINALS_V3)
        self.assertEqual(hp.YER_YARILMASI_REQUIRED_V3, REQUIRED_V3)
        self.assertEqual(hp.YER_YARILMASI_FORBIDDEN_V3, FORBIDDEN_V3)
        self.assertEqual(hp.YER_YARILMASI_SPOT_V3, "high balcony across the avenue")
        self.assertTrue(hp.YER_YARILMASI_CAMERA_LINE_V3.startswith("Kamera: hit kamerası (caddenin karşısında"))
        self.assertTrue(hp.YER_YARILMASI_CONFIRM_DESC_V3.startswith("İlk saniyede cadde ortadan yarılır"))
        self.assertEqual(hp.YER_YARILMASI_OPENING_V1, OPENING_V1)
        self.assertEqual(hp.YER_YARILMASI_TAIL_V1, STYLE_V1)
        self.assertEqual(hp.YER_YARILMASI_MODE_LABEL_V1, MODE_LABEL_V1)
        self.assertEqual(hp.YER_YARILMASI_OPENING_V2, OPENING_V2)
        self.assertEqual(hp.YER_YARILMASI_TAIL_V2, STYLE_V2)
        self.assertEqual(hp.YER_YARILMASI_MODE_LABEL_V2, MODE_LABEL_V2)
        self.assertEqual(hp.YER_YARILMASI_MIDS_V2, MIDS_V2)
        self.assertEqual(hp.YER_YARILMASI_FINALS_V2, FINALS_V2)
        self.assertEqual(hp.YER_YARILMASI_REQUIRED_V2, REQUIRED_V2)
        self.assertEqual(hp.YER_YARILMASI_FORBIDDEN_V2, FORBIDDEN_V2)
        self.assertEqual(hp.YER_YARILMASI_MIDS_PASIF, {"O1": MIDS_V2["O1"]})
        self.assertEqual(hp.YER_YARILMASI_FINALS_PASIF, {"F2": FINALS_V2["F2"]})
        self.assertEqual(list(hp.YER_YARILMASI["mids"]), ["O3"])
        self.assertEqual(list(hp.YER_YARILMASI["finals"]), ["F3"])
        for old_open, old_style, old_mids, old_finals in ((OPENING_V1, STYLE_V1, MIDS_V2, FINALS_V2),
                                                          (OPENING_V2, STYLE_V2, MIDS_V2, FINALS_V2),
                                                          (OPENING_V3, STYLE_V3, MIDS_V3, FINALS_V3)):
            self.assertNotEqual(hp.YER_YARILMASI["opening"], old_open)
            self.assertNotEqual(hp.yer_yarilmasi_tail(), old_style)
            for (g, m, f), p in all_combos():
                self.assertNotIn(old_open.format(place=PLACES[g]), p)
                self.assertNotIn(old_style, p)
                self.assertNotIn("hi-vis", p)
                for t in list(old_mids.values()) + list(old_finals.values()):
                    self.assertNotIn(t, p)
                # eski metinle kurulan prompt yeni kapıdan geçmez (eski metin geri sızarsa Kie'ye gitmez)
                for om in old_mids:
                    for of in old_finals:
                        old = f"0-4s: {old_open.format(place=PLACES[g])} 4-9s: {old_mids[om]} 9-15s: " \
                              f"{old_finals[of]} {old_style}"
                        self.assertTrue(hp.yer_yarilmasi_camera_issues(old, g), (g, om, of))
        # pasif beat'ler 40 tohumda ve dolu/boş geçmişte hiç seçilmez
        for s in range(50):
            for tags in ([], ["O2+F1"], ["O1+F2"], ["O3+F3"], ["O3+F3", "O3+F3"]):
                self.assertEqual(hp.yer_yarilmasi_choose_mid(tags, random.Random(s)), "O3")
                self.assertEqual(hp.yer_yarilmasi_choose_final(tags, random.Random(s)), "F3")
        import inspect
        src = inspect.getsource(hp.yer_yarilmasi_build_scene) + inspect.getsource(hp.yer_yarilmasi_prompt)
        for name in ("_V1", "_V2", "_V3", "_PASIF"):
            self.assertNotIn(name, src)

    def test_single_option_skips_lru(self):
        """Tek seçenekli orta/final: LRU atlanır, hata yok, rastgelelik tüketilmez (coğrafya seçimi etkilenmez)."""
        r = random.Random(5)
        state = r.getstate()
        self.assertEqual(hp.yer_yarilmasi_choose_mid(["O3+F3"] * 5, r), "O3")
        self.assertEqual(hp.yer_yarilmasi_choose_final(["O3+F3"] * 5, r), "F3")
        self.assertEqual(r.getstate(), state)
        self.assertEqual(hp._yy_pick(["A", "B"], ["A"], 1, random.Random(1)), "B")   # çok seçenekte LRU çalışır

    def test_event_gate_without_synonym(self):
        """Olay kapısı açık ve eş anlamlı eklemeden geçiyor: iç anahtarın kökleri içinden "eart" + "fiss" + "aven"
        her açılışta. _EVENT_SYNONYMS değişmedi; yarıksız metin reddedilir."""
        self.assertEqual(pg._event_stems(EVENT), {"eart", "fiss", "spli", "city", "aven"})
        for k in ("fiss", "chas", "eart"):
            self.assertNotIn(k, pg._EVENT_SYNONYMS)
        self.assertTrue(pg.event_fidelity_issues(EVENT, "Rain falls on the beach."))
        for g in PLACES:
            self.assertEqual(pg.event_fidelity_issues(EVENT, hp.yer_yarilmasi_opening(g)), [], g)


class TestScene(_Quiet):
    def _check(self, d):
        sc, st = d["scenes"][0], d["structure"]
        tb = st["yer_yarilmasi"]
        self.assertIn(tb["geo"], PLACES)
        self.assertIn(tb["mid"], MIDS)
        self.assertIn(tb["final"], FINALS)
        self.assertEqual(sc["prompt"], expected(tb["geo"], tb["mid"], tb["final"]))
        self.assertEqual(sc["style_suffix"], STYLE)
        self.assertEqual(d["combo_key"], f"{DOMAIN}|none|{EVENT.lower()}|{SPOT}##"
                                         f"{tb['mid']}+{tb['final']}|bystander_handheld")
        self.assertEqual(st["caption_info"]["kadraj"], "teras")
        self.assertEqual(cp.submit_issues(st, {"prompt": sc["prompt"], "story": sc["story"],
                                               "style_suffix": sc["style_suffix"]}), [])
        self.assertEqual((d["selection"]["domain_id"], d["selection"]["event"]), (DOMAIN, EVENT))
        for other in ("kasirga", "donma_firtina", "hit_kopya_ates"):
            self.assertNotIn(other, st)
        return tb

    def test_40_seeds_no_gpt(self):
        """40 tohumda hatasız; GPT (hikâye) hiç çağrılmaz, OpenAI istemcisi istenmez, normal hat çalışmaz."""
        with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT çağrıldı"))) as gpt, \
             patch.object(pg, "_get_openai_client", side_effect=AssertionError("GPT istemcisi istendi")), \
             patch.object(cp, "build_creative_scene", AsyncMock(side_effect=AssertionError("normal hat"))) as normal:
            seen = set()
            for seed in range(1, 41):
                tb = self._check(build(seed))
                seen.add((tb["geo"], tb["mid"], tb["final"]))
        gpt.assert_not_called()
        normal.assert_not_called()
        self.assertEqual(len(seen), 6)   # v4: 6 coğrafya × O3 × F3, hepsi görüldü
        self.assertEqual(es.CODE_STORY_FORCE.get(), frozenset())
        self.assertFalse(es.is_structured(EVENT))   # normal havuzda yok

    def test_lru(self):
        """Coğrafya son 3 tekrar etmez; v4: orta/final tek seçenek (hep O3 + F3, hata yok)."""
        geos, mids, finals = set(), set(), set()
        for seed in range(1, 16):
            reset()
            random.seed(seed)
            runs = [self._check(gen()) for _ in range(10)]
            self.assertEqual({(r["mid"], r["final"]) for r in runs}, {("O3", "F3")})
            g = [r["geo"] for r in runs]
            for i in range(len(g)):
                self.assertNotIn(g[i], g[max(0, i - 3):i], (seed, g))
            self.assertEqual(hp._YER_YARILMASI_GEO_MEMORY[-10:], g)
            geos |= set(g)
            mids |= {r["mid"] for r in runs}
            finals |= {r["final"] for r in runs}
        self.assertEqual(geos, set(PLACES))
        self.assertEqual(mids, set(MIDS))
        self.assertEqual(finals, set(FINALS))
        self.assertEqual(hp._KASIRGA_GEO_MEMORY, [])   # başka modların hafızası etkilenmez

    def test_history_sources(self):
        """Notion "Eksenler" kayıtları varsa LRU oradan; okunamazsa süreç hafızası, üretim durmaz."""
        def rec(g, tag, event=EVENT, mod="yer_yarilmasi"):
            return {"eksenler": json.dumps({"event": event, "axes": {"mod": mod, "cografya": g, "beats": tag}})}
        recs = [rec("G1", "O1+F1"), rec("G2", "O2+F2"), {"eksenler": "x"}, rec("G3", "O1+F2"),
                rec("G5", "O2+F1", event=hp.KASIRGA_EVENT, mod="kasirga")]
        self.assertEqual(hp.yer_yarilmasi_axes_history(recs, "cografya"), ["G1", "G2", "G3"])
        self.assertEqual(hp.yer_yarilmasi_axes_history(recs, "beats"), ["O1+F1", "O2+F2", "O1+F2"])
        self.assertIsNone(hp.yer_yarilmasi_axes_history(None, "cografya"))
        calls = []
        for seed in range(1, 11):
            reset()
            random.seed(seed)
            d = gen(axes_loader=lambda dom: calls.append(dom) or recs)
            tb = d["structure"]["yer_yarilmasi"]
            self.assertIn(tb["geo"], ("G4", "G5", "G6"))   # son 3 (G1, G2, G3) elenir
            self.assertEqual(tb["mid"], "O3")              # tek seçenek
            self.assertEqual(tb["final"], "F3")            # tek seçenek
            axes = json.loads(d["axes_json"])
            self.assertEqual(axes["event"], EVENT)
            self.assertEqual((axes["axes"]["mod"], axes["axes"]["cografya"], axes["axes"]["beats"],
                              axes["axes"]["kategori"]),
                             ("yer_yarilmasi", tb["geo"], f"{tb['mid']}+{tb['final']}", "Yer yarılması"))
            self.assertEqual(d["trace"]["axes_source"], "notion")
        self.assertEqual(set(calls), {DOMAIN})

        def broken(dom):
            raise RuntimeError("Notion yok")
        reset()
        random.seed(3)
        d = gen(axes_loader=broken)
        self.assertEqual(d["trace"]["axes_source"], "bellek")
        self._check(d)
        hist = [f"{DOMAIN}|none|{EVENT.lower()}|high balcony across the avenue##O2+F2|bystander_handheld"]
        for s in range(20):
            reset()
            tags = hp.yer_yarilmasi_tags(hist)
            self.assertEqual(tags, ["O2+F2"])
            self.assertEqual(hp.yer_yarilmasi_choose_mid(tags, random.Random(s)), "O3")    # tek seçenek, LRU yok
            self.assertEqual(hp.yer_yarilmasi_choose_final(tags, random.Random(s)), "F3")
            self.assertNotIn(hp.yer_yarilmasi_choose_geo(["G1", "G2", "G3"], random.Random(s)), ("G1", "G2", "G3"))
        ks = [f"{hp.KASIRGA_DOMAIN}|none|{hp.KASIRGA_EVENT.lower()}|x##O1+F2|bystander_handheld"]
        self.assertEqual(hp.yer_yarilmasi_tags(ks), [])   # kasırga kaydı bu kategoriyi etkilemez

    def test_kie_final_check_required_and_forbidden(self):
        d = build(9)
        sc, st = d["scenes"][0], d["structure"]
        tb = st["yer_yarilmasi"]
        info = {"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"]}
        self.assertEqual(cp.submit_issues(st, info), [])
        p0 = sc["prompt"]
        for need in REQUIRED:
            bad = p0.replace(need, "x")
            self.assertIn(f'"{need}" eksik', hp.yer_yarilmasi_camera_issues(bad, tb["geo"]), need)
            self.assertTrue(cp.submit_issues(st, {**info, "prompt": bad}), need)
        self.assertIn("G1-G6 yer metni yok",
                      hp.yer_yarilmasi_camera_issues(p0.replace(PLACES[tb["geo"]], "a town"), tb["geo"]))
        other = PLACES["G2" if tb["geo"] != "G2" else "G3"]
        self.assertTrue(hp.yer_yarilmasi_camera_issues(p0.replace(PLACES[tb["geo"]], other), tb["geo"]))
        for bad in FORBIDDEN:
            for form in (bad, bad.upper(), bad.capitalize()):   # büyük/küçük harf fark etmez
                text = p0 + f" {form} x."
                self.assertIn(f"bu kategoride olmayan ifade var: {bad}",
                              hp.yer_yarilmasi_camera_issues(text, tb["geo"]), form)
                self.assertTrue(cp.submit_issues(st, {**info, "prompt": text}), form)
        for bad in ({"geo": "G7"}, {"mid": "O4"}, {"final": "F4"}, {"mid": "O1"}, {"final": "F2"}, {"mid": "O2"},
                    {"final": "F1"}):
            self.assertTrue(cp.submit_issues({**st, "yer_yarilmasi": {**tb, **bad}}, info), bad)
        self.assertTrue(cp.submit_issues(st, {**info, "style_suffix": "x"}))
        self.assertTrue(cp.submit_issues(st, {**info, "prompt": p0.replace("4-9s: ", "")}))
        # Kie reddi sonrası yeni yazım yok: aynı hikâye döner, GPT çağrılmaz
        story = asyncio.run(cp.rewrite_structured(st, "test", AsyncMock(side_effect=AssertionError("GPT"))))
        self.assertEqual(story, sc["story"])
        self.assertIn("yeniden yazım yok", st["rewrite_log"][-1]["result"])
        with patch.object(hp, "YER_YARILMASI_REQUIRED", REQUIRED + ("olmayan ifade",)):
            reset()
            random.seed(9)
            with self.assertRaises(es.StructureError):
                gen()

    def test_approval_lines_show_codes_and_full_prompt(self):
        for seed in range(1, 21):
            d = build(seed)
            sc, st = d["scenes"][0], d["structure"]
            tb = st["yer_yarilmasi"]
            lines = tb["lines"].split("\n")
            self.assertEqual(lines[0], "Mod: Yer yarılması · kod hikâye (v4: yatay yarık + köşe terası)")
            self.assertTrue(lines[1].startswith(f"Coğrafya: {tb['geo']} "), lines[1])
            self.assertIn(PLACES[tb["geo"]], lines[1])
            self.assertEqual(lines[2], f"Orta (4-9s): {tb['mid']} «{MIDS[tb['mid']][6:]}»")
            self.assertEqual(lines[3], f"Final (9-15s): {tb['final']} «{FINALS[tb['final']][7:]}»")
            self.assertEqual(lines[4], CAMERA_LINE)
            self.assertEqual(lines[5], f"Kelime: {len(sc['prompt'].split())} (en fazla 230) · karakter: "
                                       f"{len(sc['prompt'])} (en fazla 1400)")
            self.assertTrue(lines[6].startswith(f"Eksenler ({MODE_LABEL}): "), lines[6])
            for part in (f"coğrafya={tb['geo']}", f"orta={tb['mid']}", f"final={tb['final']}"):
                self.assertIn(part, lines[6])
            self.assertTrue(lines[7].startswith("Tekrar önleme: coğrafya son 3 elendi · orta son 1 · final son 1"))
            self.assertEqual(lines[8], hp.YER_YARILMASI_WARNING)
            shown = sections_to_text(format_generation(d["trace"], {"domain": CATEGORY, "event": EVENT_LABEL}))
            self.assertIn(f"Hikâye: kod (birebir) · {MODE_LABEL}", shown)
            self.assertNotIn("GPT'ye verildi", shown)
            _, body = format_final_prompt({"prompt": sc["prompt"], "story": sc["story"],
                                           "style_suffix": sc["style_suffix"], "hit_lines": tb["lines"],
                                           "story_source": st["story_source"], "axes_line": st["axes_line"]})
            self.assertIn(f"\nMod: {MODE_LABEL}\n", body)
            self.assertIn("\n\n" + sc["prompt"], body)   # tam prompt onay mesajında

    def test_notion_category_and_caption(self):
        self.assertEqual(cap.YER_YARILMASI, EVENT)
        self.assertEqual(cap.SHARE_CATEGORY[EVENT], "Yer yarılması")
        broad, special = cap.event_tags(EVENT)
        for t in broad + special:
            self.assertFalse(cap.is_banned_tag(t), t)
            for bad in ("tornado", "tsunami", "flood", "lava", "earthquake"):
                self.assertNotIn(bad, t)
        for seed in range(1, 11):
            d = build(seed)
            self.assertEqual(json.loads(d["axes_json"])["axes"]["kategori"], "Yer yarılması")
            c = d["caption"]
            self.assertEqual(c["category"], "Yer yarılması")
            self.assertEqual(len(c["hashtags"]), 5)
            self.assertTrue(set(c["hashtags"]) <= set(broad) | set(special))
            self.assertTrue(d["youtube_title"].endswith(" #Shorts"))


class TestPipelineAndBot(_Quiet):
    def _run(self, poll=None, preflight=None):
        import main
        from test_tur29_infra import TestPipelineTur29, _Reporter
        seen = {}

        async def fake_gen(config):
            seen["config"] = dict(config)
            reset()
            random.seed(21)
            cfg = {k: v for k, v in config.items() if k not in ("axes_loader", "caption_loader")}
            return await pg.generate_creative_prompts({**cfg, "yer_yarilmasi_surum": "v4"})
        t = TestPipelineTur29("test_test_mode_never_uploads_and_archives_full_meta")
        t.setUp()
        try:
            rep = _Reporter(approve=True, needs_approval=True)
            orig = main.run_pipeline

            async def run_with(**kw):
                return await orig(**{**kw, "domain": DOMAIN}, yer_yarilmasi=True)
            with patch.object(main, "run_pipeline", run_with):
                r = t.run_pipe(gen=AsyncMock(side_effect=fake_gen), reporter=rep, event=EVENT, poll=poll,
                               preflight=preflight)
        finally:
            t.doCleanups()
        return r, rep, seen, t

    def test_pipeline_passes_flag_and_sends_prompt(self):
        r, rep, seen, t = self._run()
        self.assertTrue(r["success"], r)
        self.assertIs(seen["config"]["yer_yarilmasi"], True)
        self.assertNotIn("kasirga", seen["config"])
        approve = [c[1] for c in rep.calls if c[0] == "approve"]
        self.assertEqual(len(approve), 1)
        info = approve[0]
        self.assertTrue(info["hit_lines"].startswith(f"Mod: {MODE_LABEL}\nCoğrafya: G"))
        self.assertEqual(t.create.await_count, 1)
        self.assertEqual(t.create.await_args.args[1], info["prompt"])
        self.assertTrue(info["prompt"].endswith(STYLE))
        axes = [c.args[0] for c in t.tracker.record_axes.call_args_list]
        self.assertEqual(json.loads(axes[0])["axes"]["kategori"], "Yer yarılması")

    def test_preflight_is_advisory_only(self):
        """Preflight riskli deyip metni yeniden yazsa da Kie'ye kodun prompt'u birebir gider (danışman)."""
        pre = AsyncMock(side_effect=lambda s: ("REWRITTEN BY PREFLIGHT", True, {"risk_score": 8,
                                                                                "risk_reasons": ["x"]}))
        r, rep, _, t = self._run(preflight=pre)
        self.assertTrue(r["success"], r)
        pre.assert_awaited()
        sent = t.create.await_args.args[1]
        self.assertNotIn("REWRITTEN BY PREFLIGHT", sent)
        info = [c[1] for c in rep.calls if c[0] == "approve"][0]
        self.assertEqual(sent, info["prompt"])
        self.assertTrue(sent.startswith("0-4s: From the very first frame "))
        self.assertTrue(sent.endswith(STYLE))

    def test_kie_rejection_existing_behavior(self):
        from infrastructure.kie_client import ContentFilterError
        poll = AsyncMock(side_effect=ContentFilterError("İçerik filtresi: prohibited content"))
        r, _, _, t = self._run(poll=poll)
        self.assertFalse(r["success"])
        self.assertEqual(t.create.await_count, 2)   # mevcut davranış: aynı prompt bir kez daha
        self.assertEqual(t.create.await_args_list[0].args[1], t.create.await_args_list[1].args[1])

    def test_bot_labels(self):
        import bot
        from test_tur29_infra import _context
        ctx = _context()
        runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
        with patch.object(bot.pipeline, "run_pipeline", runner):
            asyncio.run(bot.produce(ctx.bot, 1, DOMAIN, EVENT, cfg=bot.default_cfg(), bot_data={},
                                    yer_yarilmasi=True))
        kw = runner.await_args.kwargs
        self.assertIs(kw["yer_yarilmasi"], True)
        self.assertNotIn("kasirga", kw)
        self.assertEqual(kw["reporter"].labels, {"domain": CATEGORY, "event": EVENT_LABEL})
        self.assertEqual(bot.CODE_DOMAIN_LABELS[DOMAIN], CATEGORY)
        self.assertEqual(bot.CODE_EVENT_LABELS[EVENT], EVENT_LABEL)


class TestOwnSnapshot(_Quiet):
    def test_yy_40_seeds_v4_lock(self):
        """18 Kas v4: 40 tohum kilidi YY_SHA256 (v3 kaydı YY_V3_SHA256, v2 YY_V2_SHA256, v1 YY_V1_SHA256 saklı).
        Coğrafya seçimleri tohum tohum v2/v3 ile birebir (havuz + LRU aynen); orta/final hep O3 + F3."""
        snap = yy_snapshot()
        self.assertEqual(snapshot_hash(snap), YY_SHA256)
        self.assertNotIn(snapshot_hash(snap), (YY_V3_SHA256, YY_V2_SHA256, YY_V1_SHA256))
        order = sorted(snap, key=int)
        self.assertEqual("".join(snap[s]["axes"]["axes"]["cografya"][1] for s in order), V2_GEOS)
        self.assertEqual({snap[s]["axes"]["axes"]["beats"] for s in order}, {"O3+F3"})
        self.assertEqual({snap[s]["axes"]["axes"]["spot"] for s in order}, {SPOT})


class TestOthersUntouched(_Quiet):
    """Diğer 19 olay (normal yol), 13 mod, 🌀 Kasırga ve ⭐ Hit kopyası: 40 tohum prompt / hikâye / stil eki / combo /
    eksenler birebir (önceki kod a4d9673)."""

    def test_other_prompts_verbatim_40_seeds(self):
        snap = others_snapshot()
        self.assertEqual(len(snap["events"]), 19)
        self.assertEqual(len(snap["modes"]), 15)
        for name, runs in snap["modes"].items():
            for s, r in runs.items():
                self.assertNotIn("error", r, (name, s))
        self.assertEqual(snapshot_hash(snap), OTHERS_SHA256)


if __name__ == "__main__":
    unittest.main()
