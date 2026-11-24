# 24 Kas 2026, Bahadır: Volkan "⭐ Hit kopyası (kül bulutu)" modu (core/hit_prompts.py HIT_KOPYA_KUL).
# Kaynak: 13 Eki 2026 11:23 üretimi "Pyroclastic Cloud Engulfs Village Street" (13 Eki paylaşımı, 2,1M izlenme). Sel
# ve orman Hit kopyası akışı örnek alındı. Şablon Bahadır'ın metni, süslü parantez dışı birebir (24 Kas kararları:
# "the volcano above {place} erupts"; F2'de "blasts" yerine "hurls"). {place} = kül bulutu Yaklaşma modunun V1-V6 yer
# metni, aynen. GPT yok, metni kod üretir. Yasaklar (tüm çıktıda alt dize): bus, explosion, blast, collapse, sunset,
# GPT. LRU: coğrafya (rastgele) son 2, M son 1, F son 1, kişi son 1; kamera ve ışık sabit. Diğer bütün olaylar ve
# modlar 40 tohum birebir aynı. Ağ yok.
# 24 Kas (v2, Bahadır; ilk test 3/10): yeni şablon (bulut ilk karede, lav arka planda, kamera yüksek yamaçta), bu moda
# özel V1-V6 yer metinleri, yeni M1-M2 / F1-F2 (karanlık yok). Yasaklara colonial, darkness, erupts eklendi. v1
# metinleri _V1 pasif; hiçbir aktif çıktıda geçmez. v1 fixture duruyor (pasif kilit), v2 fixture eklendi.
# 24 Kas (v3, Bahadır; Japonya testi: volkan yakın ve devasa, kamera yukarı bakıp çatı hizasına indi, bulut dar sütun,
# ağaç görünmedi): yeni şablon (volkan ufukta, kamera dik aşağı bakar, geniş bulut duvarı), M1-M2 ikisi de direk. F1-F2,
# yer metinleri aynen. Yasaklara upper third, tilting down no more than slightly, tree, single huge eklendi (kelime
# başından; V2 "palm trees" istisna, 24 Kas kararı). v2 şablonu ve M1-M2 _V2 pasif; v2 fixture pasif kilit, v3 eklendi.
import asyncio
import hashlib
import itertools
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

import test_hit_kopya_sel as ths   # noqa: E402  (önce: core.* döngüsel import sırası)
import test_kasirga as tk   # noqa: E402
import core.event_structure as es   # noqa: E402
import core.creative_pipeline as cp   # noqa: E402
import core.hit_prompts as hp   # noqa: E402
import core.prompt_generator as pg   # noqa: E402

PY = es.PYROCLASTIC
DOMAIN = "volcano_disasters"
HKK = hp.HIT_KOPYA_KUL
# Bahadır'ın v3 şablonu, birebir (24 Kas v3)
TEMPLATE = (
    "0-4s: From the very first frame a wide wall of pyroclastic cloud, as wide as the whole mountainside, rolls down a "
    "distant volcano on the horizon, glowing lava streaking down its slopes behind it, and slams into the far end of "
    "{place} far below. {People} people, small in the distance, run up the village street toward the camera. 4-9s: {M} "
    "9-15s: {F} Handheld footage shot from a terrace high on a steep hillside, far above the rooftops, looking steeply "
    "down at the whole village spread out small far below, with the distant erupting volcano on the horizon; slight "
    "hand shake, the camera stays fixed on the terrace and never descends, a corner of the terrace railing in the "
    "foreground; one continuous shot, no zoom, no cuts. Bystanders wear civilian clothes, no hazmat suits. Raw natural "
    "light under an ash-grey sky, never glossy or CGI. No readable signs, text or flags.")
TAIL = TEMPLATE[TEMPLATE.index("Handheld footage"):]
# v2 şablonu (24 Kas), pasif
TEMPLATE_V2 = (
    "0-4s: From the very first frame a single huge pyroclastic cloud races down the flank of the volcano, glowing lava "
    "pouring down the slope behind it, and slams into the far end of {place} far below. {People} people, small in the "
    "distance, run up the village street toward the camera. 4-9s: {M} 9-15s: {F} Handheld footage shot from a terrace "
    "high on a steep hillside, far above the rooftops, the whole village spread out below, looking down over the "
    "village street toward the erupting volcano; slight hand shake, the camera stays fixed on the terrace, tilting "
    "down no more than slightly and never descending, the erupting volcano always visible in the upper third of the "
    "frame, a corner of the terrace railing in the foreground; one continuous shot, no zoom, no cuts. Bystanders wear "
    "civilian clothes, no hazmat suits. Raw natural light under an ash-grey sky, never glossy or CGI. No readable "
    "signs, text or flags.")
TAIL_V2 = TEMPLATE_V2[TEMPLATE_V2.index("Handheld footage"):]
# v1 şablonu (24 Kas), pasif
TEMPLATE_V1 = (
    "0-4s: From the very first frame the volcano above {place} erupts, fountains of glowing lava spurting from its "
    "crater, and a single huge pyroclastic cloud races down its flank and slams into the far end of the village street. "
    "{People} people run desperately up the street toward the camera. 4-9s: {M} 9-15s: {F} Handheld footage shot by a "
    "person standing on a hillside terrace above the village, high vantage looking down over the village street toward "
    "the erupting volcano; slight hand shake, the camera stays fixed on the terrace, tilting down no more than slightly "
    "and never descending, the erupting volcano always visible in the upper third of the frame, a corner of the terrace "
    "railing in the foreground; one continuous shot, no zoom, no cuts. Bystanders wear civilian clothes, no hi-vis PPE; "
    "responders wear service uniforms. Raw natural light under an ash-grey sky, never glossy or CGI; no hazmat suits. "
    "No readable signs, text or flags.")
# 13 Eki hit'inin stil eki, birebir (Bahadır'ın talimatından)
HIT_TAIL = (
    "Handheld footage shot by a person standing on a hillside terrace above the village, high vantage looking down over "
    "the village street toward the erupting volcano; slight hand shake, the camera stays fixed on the terrace, tilting "
    "down no more than slightly and never descending, the erupting volcano always visible in the upper third of the "
    "frame, a corner of the terrace railing in the foreground; one continuous shot, no zoom, no cuts. Bystanders wear "
    "civilian clothes, no hi-vis PPE; responders wear service uniforms. Raw natural light matching the weather, never "
    "glossy or CGI; no hazmat suits. No readable signs, text or flags.")
HIT_LIGHT = "Raw natural light matching the weather,"
OUR_LIGHT = "Raw natural light under an ash-grey sky,"
PEOPLE = {6: "Six", 7: "Seven", 8: "Eight"}
MIDS = {
    "M1": "One man trips and falls; right in front of him the cloud snaps a power pole and it crashes across the road "
          "in a burst of sparks, and he scrambles up and runs on.",
    "M2": "Far down the street a whole row of power poles snaps one after another in bursts of sparks and crashes "
          "across the road just in front of the running people; one man falls, scrambles up and runs on.",
}
# v2 M1-M2 (pasif; v2 M1 metni v3 M1 ile aynı)
MIDS_V2 = {
    "M1": "One man trips and falls; right in front of him the cloud snaps a power pole and it crashes across the road "
          "in a burst of sparks, and he scrambles up and runs on.",
    "M2": "One man trips and falls; right in front of him the cloud snaps a large tree and it crashes across the road, "
          "and he scrambles up and runs on.",
}
FINALS = {
    "F1": "The cloud rolls up the village toward the terrace, swallows the houses just below and engulfs the terrace "
          "in thick brown ash.",
    "F2": "The cloud tears the roof tiles off the houses just below the terrace and hurls them toward the camera, then "
          "engulfs the terrace in thick brown ash.",
}
# v2: bu moda özel yer metinleri
PLACES = {
    "V1": "a hillside village of low stone houses with terracotta roofs",
    "V2": "a hillside village of low tin-roofed houses among palm trees",
    "V3": "a hillside village of low tiled-roof wooden houses",
    "V4": "a hillside village of low colorful wooden houses",
    "V5": "a hillside village of low pastel houses with tin roofs",
    "V6": "a hillside village of low concrete houses with tin roofs",
}
# v1 (pasif)
MIDS_V1 = {
    "M1": "One man trips and falls on the road; right in front of him the cloud snaps a power pole and it crashes "
          "across the street in a burst of sparks, and he scrambles up and keeps running.",
    "M2": "One man trips and falls on the road; right in front of him the cloud snaps a large tree and it crashes "
          "across the street, and he scrambles up and keeps running.",
}
FINALS_V1 = {
    "F1": "The cloud rolls up the street, swallows the houses below the terrace and engulfs the camera in darkness.",
    "F2": "Right below the terrace the cloud tears the roof tiles off the nearest house and hurls them toward the "
          "camera, then engulfs the camera in darkness.",
}
# v1 yer metinleri = kül bulutu Yaklaşma modunun V1-V6 yer metinleri (değişmedi), pasif
PLACES_V1 = {
    "V1": "a village of stone houses with terracotta roofs",
    "V2": "a village of tin-roofed houses among palm trees",
    "V3": "a town of tiled-roof Japanese houses",
    "V4": "a town of colorful wooden houses",
    "V5": "a town of pastel colonial houses",
    "V6": "a town of concrete houses with tin roofs",
}
BUTTONS = {"V1": "🇮🇹 İtalya", "V2": "🇮🇩 Endonezya", "V3": "🇯🇵 Japonya", "V4": "🇨🇱 Şili", "V5": "🇬🇹 Guatemala",
           "V6": "🇵🇭 Filipinler"}
REQUIRED = ("wide wall of pyroclastic cloud", "distant volcano on the horizon", "looking steeply down", "power pole")
FORBIDDEN = ("bus", "explosion", "blast", "collapse", "sunset", "GPT", "colonial", "darkness", "erupts", "upper third",
             "tilting down no more than slightly", "tree", "single huge")
VERSION_LINE = "Sürüm: hit_kul v3 (volkan ufukta, kamera dik aşağı bakar, geniş bulut duvarı, hep direk)"
CAMERA_LINE = "Kamera: sabit yüksek yamaç terası, köye dik aşağı bakar, volkan uzakta ufukta"
CAMERA_AXIS = "sabit yüksek yamaç terası, köye dik aşağı bakar, volkan uzakta ufukta"
VERSION_LINE_V2 = "Sürüm: hit_kul v2 (yüksek yamaç kamerası, bulut ilk karede, lav arka planda)"
CAMERA_AXIS_V2 = "sabit yüksek yamaç terası, köy aşağıda serili, volkan üst üçte birde"


def forbidden_hits(text: str) -> list[str]:
    """Yasaklar kelime başından ("street" içindeki "tree" sayılmaz); V2 "palm trees" istisna (24 Kas v3 kararı)."""
    import re
    low = text.lower().replace("palm trees", " ")
    return [b for b in FORBIDDEN if re.search(r"\b" + re.escape(b.lower()), low)]


def passive_clauses(template: str) -> list[str]:
    """Pasif şablonun aktif v3 şablonunda bulunmayan cümlecikleri (yer tutucular dışı, 12 karakterden uzun)."""
    import re
    parts = re.split(r"\{[A-Za-z]+\}|[;,.]\s", template)
    return [p.strip() for p in parts if len(p.strip()) > 12 and p.strip() not in TEMPLATE]
SOURCE = ('Kaynak: 13 Eki 11:23 üretimi "Pyroclastic Cloud Engulfs Village Street" (13 Eki paylaşımı, 2,1M), iskelet '
          've dil')
REPEAT = "Tekrar önleme: coğrafya son 2 (yalnız rastgele) · M son 1 · F son 1 · kişi son 1 · kamera ve ışık sabit"
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "hit_kopya_kul_v3_runs_40.json")
FIXTURE_V2 = os.path.join(ROOT, "tests", "fixtures", "hit_kopya_kul_v2_runs_40.json")   # pasif v2 kilidi
FIXTURE_V1 = os.path.join(ROOT, "tests", "fixtures", "hit_kopya_kul_v1_runs_40.json")   # pasif v1 kilidi

# Değişiklikten önceki kod (8b4c19f): test_kasirga_cografya_menu tam zinciri (19 olay + bütün modlar + ⭐ Hit kopyası
# (ani sel), FULL_SHA256 4db63034) + canlı 🌀 Kasırga v3 🎲 Rastgele (KASIRGA_SHA256 9e9b0103); 40 tohum
OTHERS_SHA256 = "f35ab4dfb22a337016f7ea2cf36f8162470415eb385adb0bfc648e9f9806d854"
# ⭐ Hit kopyası (kül bulutu) v3, 40 tohum kilidi (prompt / hikâye / stil eki / combo / eksenler; caption hariç)
HIT_KOPYA_KUL_SHA256 = "937e53e2a1da7a6d4c82b8fdeb17b71ce57db6b1fee0f908c958cb59ff264c5b"
# v2 kilidi (pasif fixture)
HIT_KOPYA_KUL_SHA256_V2 = "aea27e7b0c5605bc6a8745dc6bf7ff7b387d0bb9d0e70ac82a0563e41c978478"
# v1 kilidi (pasif fixture)
HIT_KOPYA_KUL_SHA256_V1 = "0ae410e34376ac3271871ee86dcae1b5a0969e14f2208e0aff65c35f10da2932"


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


reset = ths.reset
snapshot_hash = ths.snapshot_hash


def gen(**extra) -> dict:
    return asyncio.run(pg.generate_creative_prompts({"domain": DOMAIN, "event": PY, "hit_kopya_kul": True,
                                                     "used_combos": [], "recent_topics": [], **extra}))


def expected(geo: str, mid: str, final: str, n: int) -> str:
    """Bahadır'ın şablonundan bağımsız kurulum."""
    return TEMPLATE.format(place=PLACES[geo], People=PEOPLE[n], M=MIDS[mid], F=FINALS[final])


def combos():
    return list(itertools.product(PLACES, MIDS, FINALS, PEOPLE))


def others_snapshot() -> dict:
    """test_kasirga_cografya_menu tam zinciri (bütün olaylar + modlar + ⭐ Hit kopyası (ani sel)) + canlı 🌀 Kasırga v3
    (🎲 Rastgele); 40 tohum."""
    snap = ths.others_snapshot()
    snap["modes"]["hit_kopya_sel"] = ths.hks_snapshot()
    snap["modes"]["kasirga_canli"] = tk.TestKasirgaV2Lock.live_runs()
    return snap


def hkk_snapshot() -> dict:
    """⭐ Hit kopyası (kül bulutu) 40 tohum (🎲 Rastgele): prompt, hikâye, stil eki, combo, eksenler (caption hariç)."""
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


class TestTemplate(_Quiet):
    def test_template_verbatim(self):
        self.assertEqual(HKK["template"], TEMPLATE)
        for ph in ("{place}", "{People}", "{M}", "{F}"):
            self.assertEqual(TEMPLATE.count(ph), 1, ph)
        self.assertEqual(HKK["tail_start"], "Handheld footage shot from a terrace high on a steep hillside")
        self.assertEqual(hp.HIT_KOPYA_KUL_TAIL, TAIL)
        self.assertIn("slams into the far end of {place} far below", TEMPLATE)

    def test_v1_passive_kept(self):
        """v1 şablonu, M, F, yer metinleri ve satırları _V1 olarak duruyor (silinmedi)."""
        v1 = hp.HIT_KOPYA_KUL_V1
        self.assertEqual(v1["template"], TEMPLATE_V1)
        self.assertEqual(v1["mids"], MIDS_V1)
        self.assertEqual(v1["finals"], FINALS_V1)
        self.assertEqual(v1["people"], ("Six", "Seven", "Eight"))
        self.assertEqual(hp.HIT_KOPYA_KUL_PLACES_V1, PLACES_V1)
        self.assertEqual(hp.HIT_KOPYA_KUL_VERSION_LINE_V1, "Sürüm: hit_kul v1")
        self.assertEqual(hp.HIT_KOPYA_KUL_CAMERA_V1, "sabit tepe terası, volkan üst üçte birde (hit ile aynı)")
        self.assertEqual(hp.HIT_KOPYA_KUL_SURUM_V1, "v1")
        for name in ("CAMERA_AXIS_V1", "REQUIRED_V1", "FORBIDDEN_V1", "NAMES_V1", "WARNING_V1", "CONFIRM_DESC_V1"):
            self.assertTrue(hasattr(hp, "HIT_KOPYA_KUL_" + name), name)

    def test_v2_passive_kept(self):
        """v2 şablonu, M1-M2 ve satırları _V2 olarak duruyor (silinmedi); F1-F2 v3'te aynen."""
        v2 = hp.HIT_KOPYA_KUL_V2
        self.assertEqual(v2["template"], TEMPLATE_V2)
        self.assertEqual(v2["mids"], MIDS_V2)
        self.assertEqual(v2["finals"], FINALS)
        self.assertEqual(v2["people"], ("Six", "Seven", "Eight"))
        self.assertEqual(v2["tail_start"], HKK["tail_start"])
        self.assertEqual(hp.HIT_KOPYA_KUL_TAIL_V2, TAIL_V2)
        self.assertEqual(hp.HIT_KOPYA_KUL_VERSION_LINE_V2, VERSION_LINE_V2)
        self.assertEqual(hp.HIT_KOPYA_KUL_CAMERA_V2, CAMERA_AXIS_V2)
        self.assertEqual(hp.HIT_KOPYA_KUL_CAMERA_AXIS_V2, CAMERA_AXIS_V2)
        self.assertEqual(hp.HIT_KOPYA_KUL_SURUM_V2, "v2")
        self.assertEqual(hp.HIT_KOPYA_KUL_FORBIDDEN_V2, FORBIDDEN[:9])
        for name in ("REQUIRED_V2", "NAMES_V2", "WARNING_V2", "CONFIRM_DESC_V2"):
            self.assertTrue(hasattr(hp, "HIT_KOPYA_KUL_" + name), name)
        self.assertEqual(hp.HIT_KOPYA_KUL_NAMES_V2["M2"], "adam düşer, büyük ağaç yola devrilir")

    def test_v1_texts_never_in_active_output(self):
        import re
        frags = [x for x in re.split(r"\{[A-Za-z]+\}", TEMPLATE_V1) if len(x.strip()) > 12]
        passive = [*MIDS_V1.values(), *FINALS_V1.values(), *PLACES_V1.values(), *frags, HIT_TAIL]
        # v2: şablonun v3'te olmayan bütün cümlecikleri, stil eki, M2 (v2 M1 ve F1-F2 v3'te aynen)
        v2_only = [MIDS_V2["M2"], TAIL_V2, *passive_clauses(TEMPLATE_V2)]
        self.assertTrue(any("upper third" in t for t in v2_only))
        self.assertTrue(any("single huge pyroclastic cloud" in t for t in v2_only))
        for c in combos():
            p = hp.hit_kopya_kul_prompt(*c)
            for t in passive + v2_only:
                self.assertNotIn(t, p, (c, t))
        for t in (hp.HIT_KOPYA_KUL_CONFIRM_DESC_V1, hp.HIT_KOPYA_KUL_WARNING_V1, *hp.HIT_KOPYA_KUL_NAMES_V1.values(),
                  hp.HIT_KOPYA_KUL_CONFIRM_DESC_V2, hp.HIT_KOPYA_KUL_WARNING_V2):
            self.assertNotEqual(t, hp.HIT_KOPYA_KUL_CONFIRM_DESC)
            self.assertNotEqual(t, hp.HIT_KOPYA_KUL_WARNING)

    def test_constants(self):
        self.assertEqual(hp.HIT_KOPYA_KUL_MODE_LABEL, "⭐ Hit kopyası (kül bulutu)")
        self.assertEqual(hp.HIT_KOPYA_KUL_EVENTS, (PY,))
        self.assertEqual(hp.HIT_KOPYA_KUL_DOMAIN, DOMAIN)
        self.assertEqual(hp.HIT_KOPYA_KUL_MOD, "hit_kopya_kul")
        self.assertEqual(hp.HIT_KOPYA_KUL_SURUM, "v3")
        self.assertEqual(hp.HIT_KOPYA_KUL_CAMERA_AXIS, CAMERA_AXIS)
        self.assertEqual(hp.HIT_KOPYA_KUL_PLACES, PLACES)
        self.assertEqual(hp.HIT_KOPYA_KUL_VERSION_LINE, VERSION_LINE)
        self.assertEqual("Kamera: " + hp.HIT_KOPYA_KUL_CAMERA, CAMERA_LINE)
        self.assertEqual(hp.HIT_KOPYA_KUL_SOURCE, SOURCE)
        self.assertEqual((hp.HIT_KOPYA_KUL_MAX_WORDS, hp.HIT_KOPYA_KUL_MAX_CHARS), (230, 1400))
        self.assertEqual((hp.HIT_KOPYA_KUL_GEO_BLOCK, hp.HIT_KOPYA_KUL_MID_BLOCK, hp.HIT_KOPYA_KUL_FINAL_BLOCK,
                          hp.HIT_KOPYA_KUL_PEOPLE_BLOCK), (2, 1, 1, 1))
        self.assertEqual(HKK["people"], ("Six", "Seven", "Eight"))
        self.assertEqual(HKK["mids"], MIDS)
        self.assertEqual(HKK["finals"], FINALS)
        self.assertEqual(hp.HIT_KOPYA_KUL_GEO_BUTTONS, BUTTONS)
        self.assertEqual(hp.HIT_KOPYA_KUL_FORBIDDEN, FORBIDDEN)
        self.assertEqual(hp.HIT_KOPYA_KUL_FORBIDDEN_EXCEPTIONS, ("palm trees",))
        self.assertEqual(hp.HIT_KOPYA_KUL_NAMES["M1"], "adam düşer, önüne elektrik direği kıvılcımlarla yola devrilir")
        self.assertEqual(hp.HIT_KOPYA_KUL_NAMES["M2"],
                         "caddede bir sıra direk peş peşe kıvılcımlarla yola devrilir, bir adam düşer")
        self.assertNotIn("ağaç", hp.HIT_KOPYA_KUL_NAMES["M1"] + hp.HIT_KOPYA_KUL_NAMES["M2"])
        for t in (hp.HIT_KOPYA_KUL_WARNING, hp.HIT_KOPYA_KUL_CONFIRM_DESC):
            self.assertNotIn("üst üçte bir", t)
            self.assertNotIn("ağaç", t)
            self.assertIn("v3" if t is hp.HIT_KOPYA_KUL_CONFIRM_DESC else "ufukta", t)
        self.assertEqual(hp.HIT_KOPYA_KUL_HIT_TAIL, HIT_TAIL)
        for t in (hp.HIT_KOPYA_KUL_CONFIRM_DESC, hp.HIT_KOPYA_KUL_WARNING, SOURCE, VERSION_LINE, CAMERA_LINE,
                  *BUTTONS.values(), *hp.HIT_KOPYA_KUL_NAMES.values()):
            self.assertNotIn("—", t)

    def test_places_mode_specific_yaklasma_unchanged(self):
        """{place} = bu moda özel v2 yer metni, aynen; kül bulutu Yaklaşma havuzu değişmedi (v1 metinleri)."""
        self.assertEqual(hp.hit_kopya_kul_geos(), list(PLACES))
        self.assertEqual(list(hp.YAKLASMA_KUL_BULUTU["geos"]), list(PLACES))
        self.assertEqual({g: v["place"] for g, v in hp.YAKLASMA_KUL_BULUTU["geos"].items()}, PLACES_V1)
        for g, text in PLACES.items():
            self.assertEqual(hp.hit_kopya_kul_place(g), text, g)
            self.assertEqual(BUTTONS[g].split(" ", 1)[1], hp.YAKLASMA_KUL_BULUTU["geos"][g]["name"], g)

    def test_camera_style_v3_verbatim(self):
        """Stil eki ("Handheld footage..." ile başlayan bölüm) v3 şablonunun stil ekiyle birebir, her kombinasyonda
        aynı; 13 Eki hit stil eki ve v2 stil eki referans/pasif olarak duruyor."""
        self.assertEqual(HIT_TAIL.count(HIT_LIGHT), 1)
        self.assertIn(OUR_LIGHT, TAIL)
        for c in combos():
            tail = hp.hit_kopya_kul_tail(*c)
            self.assertEqual(tail, TAIL, c)
            self.assertNotEqual(tail, HIT_TAIL)
            self.assertNotEqual(tail, TAIL_V2)

    def test_all_combos_within_limits(self):
        cs = combos()
        self.assertEqual(len(cs), 72)   # 6 coğrafya × 2 M × 2 F × 3 kişi
        words, chars = [], []
        for c in cs:
            p = hp.hit_kopya_kul_prompt(*c)
            self.assertEqual(p, expected(*c), c)
            words.append(len(p.split()))
            chars.append(len(p))
        self.assertLessEqual(max(words), 230)
        self.assertLessEqual(max(chars), 1400)
        self.assertEqual((min(words), max(words), min(chars), max(chars)), (211, 222, 1187, 1258))

    def test_required_phrases_every_output(self):
        for c in combos():
            p = hp.hit_kopya_kul_prompt(*c)
            for need in REQUIRED:
                self.assertIn(need, p, (c, need))
            for need in hp.HIT_KOPYA_KUL_REQUIRED:
                self.assertIn(need, p, (c, need))
        self.assertEqual(hp.HIT_KOPYA_KUL_REQUIRED[:4], REQUIRED)

    def test_forbidden_words(self):
        import re
        for c in combos():
            p = hp.hit_kopya_kul_prompt(*c)
            self.assertEqual(forbidden_hits(p), [], c)
            # "tree" yalnız V2 "palm trees" içinde (istisna), devrilen ağaç hiç yok
            self.assertEqual(len(re.findall(r"\btree", p.lower())), 1 if c[0] == "V2" else 0, c)
        for text in (*MIDS.values(), *FINALS.values(), TEMPLATE):
            self.assertEqual(forbidden_hits(text), [], text)
            self.assertNotRegex(text.lower(), r"\btree")
            for bad in FORBIDDEN:
                if bad != "tree":   # "street" içindeki alt dize hariç, diğerleri alt dize olarak da yok
                    self.assertNotIn(bad.lower(), text.lower(), (text, bad))
        for text in PLACES.values():
            self.assertEqual(forbidden_hits(text), [], text)
        self.assertEqual(forbidden_hits("a large tree; Trees; upper third"), ["upper third", "tree"])
        self.assertNotIn("blasts", FINALS["F2"])
        self.assertIn("erupting volcano", TEMPLATE)   # "erupts" yasak, "erupting" serbest
        self.assertIn("hurls them toward the camera", FINALS["F2"])

    def test_text_issues_detect_violations(self):
        good = hp.hit_kopya_kul_prompt("V1", "M1", "F1", 6)
        self.assertEqual(hp.hit_kopya_kul_text_issues(good), [])
        for need in REQUIRED:
            self.assertTrue(hp.hit_kopya_kul_text_issues(good.replace(need, "x")), need)
        for bad in ("A bus.", "An EXPLOSION.", "blasts", "collapses", "Sunset.", "gpt", "colonial", "Darkness.",
                    "erupts", "the upper third", "tilting down no more than slightly", "a large tree", "Trees.",
                    "a single huge cloud"):
            self.assertTrue(hp.hit_kopya_kul_text_issues(good + " " + bad), bad)

    def test_bad_ids(self):
        for args in (("V7", "M1", "F1", 6), ("V1", "M3", "F1", 6), ("V1", "M1", "F3", 6), ("V1", "M1", "F1", 5),
                     ("V1", "M1", "F1", 9)):
            with self.assertRaises(es.StructureError):
                hp.hit_kopya_kul_prompt(*args)

    def test_event_gate(self):
        for c in combos()[::5]:
            self.assertEqual(pg.event_fidelity_issues(PY, hp.hit_kopya_kul_story(*c)), [], c)
            self.assertEqual(pg.event_fidelity_issues(PY, hp.hit_kopya_kul_prompt(*c)), [], c)

    def test_example_v2_m1_f2(self):
        p = hp.hit_kopya_kul_prompt("V2", "M1", "F2", 7)
        self.assertTrue(p.startswith("0-4s: From the very first frame a wide wall of pyroclastic cloud, as wide as the "
                                     "whole mountainside, rolls down a distant volcano on the horizon, glowing lava "
                                     "streaking down its slopes behind it, and slams into the far end of a hillside "
                                     "village of low tin-roofed houses among palm trees far below. Seven people, "
                                     "small in the distance,"))
        self.assertIn(" 4-9s: " + MIDS["M1"] + " 9-15s: " + FINALS["F2"] + " Handheld footage", p)
        self.assertEqual(hp.hit_kopya_kul_text_issues(p), [])


class TestScene(_Quiet):
    def _check(self, d, geo=None) -> dict:
        tb = d["structure"]["hit_kopya_kul"]
        sc = d["scenes"][0]
        if geo is not None:
            self.assertEqual(tb["geo"], geo)
        self.assertEqual(sc["prompt"], expected(tb["geo"], tb["mid"], tb["final"], tb["people"]))
        self.assertEqual(sc["prompt"], tb["prompt"])
        self.assertEqual(sc["story"] + " " + sc["style_suffix"], sc["prompt"])
        self.assertEqual(d["combo_key"],
                         f"{DOMAIN}|none|{PY.lower()}|hillside terrace above the village##HKK:{tb['geo']}|"
                         "bystander_handheld")
        self.assertIsNone(es.beats_of_combo(d["combo_key"]))   # olay çifti yok: normal LRU saymaz
        ax = json.loads(d["axes_json"])
        self.assertEqual(ax["event"], PY)
        a = ax["axes"]
        for k in ("spot", "view", "light", "vehicle", "people", "beats"):
            self.assertIsNone(a[k], k)
        self.assertEqual((a["mod"], a["surum"], a["cografya"], a["m"], a["f"], a["kisi"]),
                         ("hit_kopya_kul", "v3", tb["geo"], tb["mid"], tb["final"], tb["people"]))
        return {"geo": tb["geo"], "mid": tb["mid"], "final": tb["final"], "people": tb["people"]}

    def test_40_seeds_no_gpt_no_normal_path(self):
        seen = {"geo": set(), "mid": set(), "final": set(), "people": set()}
        with patch.object(pg, "_call_gpt", AsyncMock(side_effect=AssertionError("GPT"))), \
             patch.object(hp, "kul_apply", side_effect=AssertionError("Yaklaşma")), \
             patch.object(cp, "build_creative_scene", side_effect=AssertionError("normal hat")):
            for s in range(1, 41):
                reset()
                random.seed(s)
                r = self._check(gen())
                for k in seen:
                    seen[k].add(r[k])
        self.assertEqual(seen["geo"], set(PLACES))
        self.assertEqual(seen["mid"], set(MIDS))
        self.assertEqual(seen["final"], set(FINALS))
        self.assertEqual(seen["people"], set(PEOPLE))

    def test_lru_memory(self):
        for seed in range(1, 11):
            reset()
            random.seed(seed)
            runs = [self._check(gen()) for _ in range(12)]
            for key, block in (("geo", 2), ("mid", 1), ("final", 1), ("people", 1)):
                v = [r[key] for r in runs]
                for i in range(len(v)):
                    self.assertNotIn(v[i], v[max(0, i - block):i], (seed, key, v))
            self.assertEqual(hp._HIT_KOPYA_KUL_GEO_MEMORY[-12:], [r["geo"] for r in runs])
        # diğer kül bulutu modlarının hafızası etkilenmez
        self.assertEqual(hp._KUL_GEO_MEMORY, [])
        self.assertEqual(hp._KUL_VEHICLE_MEMORY, [])
        self.assertEqual(es._BEAT_MEMORY.get(PY, []), [])

    def test_menu_geo_fixed(self):
        """Menüden seçilen coğrafya aynen gelir (tekrar olsa bile); LRU yalnız 🎲 Rastgele'de."""
        reset()
        random.seed(4)
        for _ in range(4):
            d = gen(hit_kopya_kul_geo="V3")
            self._check(d, geo="V3")
            self.assertEqual(json.loads(d["axes_json"])["axes"]["cografya_kaynak"], "menü")
        reset()
        random.seed(4)
        d = gen(hit_kopya_kul_geo="V3")
        self.assertEqual(json.loads(d["axes_json"])["excluded"]["cografya"], [])
        self.assertIn("Coğrafya: V3 🇯🇵 Japonya «" + PLACES["V3"] + "» (menü)", d["structure"]["hit_kopya_kul"]["lines"])
        r = self._check(gen())   # rastgele: menü seçimi de sayılır
        self.assertNotEqual(r["geo"], "V3")
        with self.assertRaises(es.StructureError):
            hp.hit_kopya_kul_build_scene(DOMAIN, PY, geo="V9")

    def test_history_sources_and_isolation(self):
        def rec(event=PY, mod="hit_kopya_kul", **axes):
            return {"eksenler": json.dumps({"event": event, "axes": {"mod": mod, **axes}})}
        recs = [rec(cografya="V1", m="M2", f="F2", kisi=6),
                {"eksenler": "x"},
                rec(cografya="V4", m="M1", f="F1", kisi=8),
                rec(mod="kul_yaklasma", cografya="V2", m="M2", f="F2", kisi=3),
                rec(event=es.WILDFIRE, cografya="V5", m="M2", f="F2")]
        self.assertEqual(hp.hit_kopya_kul_axes_history(recs, "cografya"), ["V1", "V4"])
        self.assertEqual(hp.hit_kopya_kul_axes_history(recs, "kisi"), [6, 8])
        self.assertIsNone(hp.hit_kopya_kul_axes_history(None, "m"))
        # normal kül bulutu Yaklaşma hattı bu modun kayıtlarını saymaz
        self.assertEqual(hp.kul_axes_history(recs[:3], "cografya"), [])
        calls = []
        for seed in range(1, 11):
            reset()
            random.seed(seed)
            d = gen(axes_loader=lambda dom: calls.append(dom) or recs)
            tb = self._check(d)
            self.assertNotIn(tb["geo"], ("V1", "V4"))
            self.assertEqual(tb["mid"], "M2")
            self.assertEqual(tb["final"], "F2")
            self.assertNotEqual(tb["people"], 8)
            ex = json.loads(d["axes_json"])["excluded"]
            self.assertEqual(ex, {"cografya": ["V1", "V4"], "m": ["M1"], "f": ["F1"], "kisi": [8]})
            self.assertEqual(d["trace"]["axes_source"], "notion")
        self.assertEqual(set(calls), {DOMAIN})

        def broken(dom):
            raise RuntimeError("Notion yok")
        reset()
        random.seed(3)
        d = gen(axes_loader=broken)
        self.assertEqual(d["trace"]["axes_source"], "bellek")
        self._check(d)

    def test_kie_final_check(self):
        reset()
        random.seed(5)
        d = gen()
        st, sc = d["structure"], d["scenes"][0]
        tb = st["hit_kopya_kul"]
        good = {"prompt": sc["prompt"], "story": sc["story"], "style_suffix": sc["style_suffix"]}
        self.assertEqual(cp.submit_issues(st, good), [])
        for need in REQUIRED:
            self.assertTrue(cp.submit_issues(st, {**good, "prompt": sc["prompt"].replace(need, "x")}), need)
        self.assertTrue(cp.submit_issues(st, {**good, "prompt": sc["prompt"] + " A blast."}))
        self.assertTrue(cp.submit_issues(st, {**good, "style_suffix": "x"}))
        self.assertTrue(cp.submit_issues(st, {**good, "story": sc["story"] + " x"}))
        for key, val in (("mid", "M4"), ("final", "F9"), ("people", 5), ("geo", "V9")):
            self.assertTrue(cp.submit_issues({**st, "hit_kopya_kul": {**tb, key: val}}, good), key)
        other = next(f for f in FINALS if f != tb["final"])
        self.assertTrue(cp.submit_issues({**st, "hit_kopya_kul": {**tb, "final": other}}, good))
        long = sc["prompt"] + " word" * 80
        self.assertTrue(any("kelime" in x for x in hp.hit_kopya_kul_issues(st, {**good, "prompt": long})))
        self.assertEqual(asyncio.run(cp.rewrite_structured(st, "ret", AsyncMock(side_effect=AssertionError("GPT")))),
                         sc["story"])

    def test_approval_lines(self):
        reset()
        random.seed(7)
        d = gen()
        tb = d["structure"]["hit_kopya_kul"]
        lines = tb["lines"].split("\n")
        self.assertEqual(lines[0], "Mod: ⭐ Hit kopyası (kül bulutu)")
        self.assertEqual(lines[1], VERSION_LINE)
        self.assertEqual(lines[2], SOURCE)
        self.assertEqual(lines[3], f"Coğrafya: {tb['geo']} {BUTTONS[tb['geo']]} «{PLACES[tb['geo']]}» (rastgele)")
        self.assertTrue(lines[4].startswith(f"M (4-9s): {tb['mid']} "))
        self.assertTrue(lines[5].startswith(f"F (9-15s): {tb['final']} "))
        self.assertEqual(lines[6], f"Kişi: {tb['people']}")
        self.assertEqual(lines[7], CAMERA_LINE)
        p = tb["prompt"]
        self.assertEqual(lines[8], f"Kelime: {len(p.split())} (en fazla 230) · karakter: {len(p)} (en fazla 1400)")
        self.assertTrue(lines[9].startswith("Eksenler (⭐ Hit kopyası (kül bulutu)): sürüm=v3 · coğrafya="))
        for part in (f"M={tb['mid']}", f"F={tb['final']}", f"kişi={tb['people']}",
                     "kamera modu=" + CAMERA_AXIS):
            self.assertIn(part, lines[9])
        self.assertEqual(lines[10], REPEAT)
        self.assertEqual(lines[11], hp.HIT_KOPYA_KUL_WARNING)
        self.assertEqual(len(lines), 12)
        self.assertNotIn("—", tb["lines"])
        from core.trace_format import format_generation
        text = "\n".join(b for _, b in format_generation(d["trace"]))
        self.assertIn(CAMERA_LINE + "\n", text)


class TestPipelineAndBot(_Quiet):
    def _run(self, approve=True, geo=None):
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
                return await orig(**{**kw, "domain": DOMAIN}, hit_kopya_kul=True, hit_kopya_kul_geo=geo)
            with patch.object(main, "run_pipeline", run_with):
                r = t.run_pipe(gen=AsyncMock(side_effect=fake_gen), reporter=rep, event=PY)
        finally:
            t.doCleanups()
        return r, rep, seen, t

    def test_pipeline_sends_verbatim_prompt_after_approval(self):
        r, rep, seen, t = self._run(geo="V6")
        self.assertTrue(r["success"], r)
        self.assertIs(seen["config"]["hit_kopya_kul"], True)
        self.assertEqual(seen["config"]["hit_kopya_kul_geo"], "V6")
        for other in ("hit_kopya_sel", "hit_kopya_orman", "hit_kopya_ates", "kul_yaklasma", "kasirga", "hit_env"):
            self.assertNotIn(other, seen["config"])
        approve = [c[1] for c in rep.calls if c[0] == "approve"]
        self.assertEqual(len(approve), 1)
        info = approve[0]
        self.assertTrue(info["hit_lines"].startswith("Mod: ⭐ Hit kopyası (kül bulutu)\n" + VERSION_LINE + "\n"))
        self.assertIn(CAMERA_LINE, info["hit_lines"])
        self.assertEqual(t.create.await_count, 1)
        self.assertEqual(t.create.await_args.args[1], info["prompt"])
        ax = json.loads(t.tracker.record_axes.call_args_list[0].args[0])["axes"]
        self.assertEqual((ax["mod"], ax["surum"], ax["cografya"]), ("hit_kopya_kul", "v3", "V6"))
        self.assertEqual(info["prompt"], expected(ax["cografya"], ax["m"], ax["f"], ax["kisi"]))

    def test_random_geo_not_passed(self):
        r, _, seen, _ = self._run(geo=None)
        self.assertTrue(r["success"], r)
        self.assertNotIn("hit_kopya_kul_geo", seen["config"])

    def test_rejected_approval_no_kie(self):
        r, _, _, t = self._run(approve=False)
        self.assertFalse(r["success"])
        self.assertEqual(t.create.await_count, 0)

    def test_menu_flow(self):
        import bot
        from test_tur29_infra import _context, _update
        di = str(bot.DOMAIN_KEYS.index(DOMAIN))
        ctx = _context()
        upd = _update(data=f"uret:d:{di}")
        asyncio.run(bot.on_callback(upd, ctx))
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        rows = [[b.text for b in r] for r in kb.inline_keyboard]
        self.assertEqual(rows[-2:], [["⭐ Hit kopyası (kül bulutu)"], ["🔙 Geri"]])
        self.assertEqual(rows[-3], ["🎲 Rastgele"])
        self.assertEqual(kb.inline_keyboard[-2][0].callback_data, "uret:hkk")
        # coğrafya menüsü: V1-V6 + 🎲 Rastgele + 🔙 Geri
        upd = _update(data="uret:hkk")
        asyncio.run(bot.on_callback(upd, ctx))
        self.assertIn("Hangi coğrafya?", upd.callback_query.edit_message_text.await_args.args[0])
        kb = upd.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
        btns = [b for r in kb.inline_keyboard for b in r]
        self.assertEqual([b.text for b in btns], list(BUTTONS.values()) + ["🎲 Rastgele", "🔙 Geri"])
        self.assertEqual([b.callback_data for b in btns],
                         [f"uret:hkk:{g}" for g in BUTTONS] + ["uret:hkk:r", f"uret:d:{di}"])
        upd = _update(data="uret:hkk:V2")
        asyncio.run(bot.on_callback(upd, ctx))
        call = upd.callback_query.edit_message_text.await_args
        text = call.args[0]
        for part in ("Coğrafya: V2 🇮🇩 Endonezya", "Mod: ⭐ Hit kopyası (kül bulutu)", VERSION_LINE, SOURCE,
                     CAMERA_LINE, hp.HIT_KOPYA_KUL_CONFIRM_DESC, "✋ Onay"):
            self.assertIn(part, text)
        self.assertNotIn("—", text)
        self.assertEqual([b.callback_data for r in call.kwargs["reply_markup"].inline_keyboard for b in r],
                         ["uret:hkkok:V2", "uret:x"])
        upd = _update(data="uret:hkk:r")
        asyncio.run(bot.on_callback(upd, ctx))
        self.assertIn("Coğrafya: 🎲 Rastgele (son 2 coğrafya elenir)",
                      upd.callback_query.edit_message_text.await_args.args[0])
        for gid, geo in (("V2", "V2"), ("r", None)):
            upd = _update(data=f"uret:hkkok:{gid}")
            runner = AsyncMock(return_value={"success": False, "reason": "cancelled"})
            with patch.object(bot.pipeline, "run_pipeline", runner), \
                 patch.object(bot, "_production_lock", asyncio.Lock()):
                asyncio.run(bot.on_callback(upd, ctx))
            kw = runner.await_args.kwargs
            self.assertEqual((kw["domain"], kw["event"], kw["hit_kopya_kul"]), (DOMAIN, PY, True))
            self.assertEqual(kw.get("hit_kopya_kul_geo"), geo)
            for other in ("hit_kopya_sel", "hit_kopya_orman", "hit_kopya_ates", "kul_yaklasma", "kasirga", "hit_env"):
                self.assertNotIn(other, kw)
            self.assertTrue(kw["reporter"].needs_approval)
            self.assertIn("/ ⭐ Hit kopyası (kül bulutu)",
                          upd.callback_query.edit_message_text.await_args_list[0].args[0])
        for bad in ("uret:hkk:V7", "uret:hkk:x", "uret:hkkok", "uret:hkkok:G1", "uret:hkkok:V1:2"):
            upd = _update(data=bad)
            asyncio.run(bot.on_callback(upd, ctx))
            self.assertIn("Geçersiz", upd.callback_query.edit_message_text.await_args.args[0], bad)
        busy = asyncio.Lock()
        asyncio.run(busy.acquire())
        with patch.object(bot, "_production_lock", busy):
            upd = _update(data="uret:hkkok:r")
            asyncio.run(bot.on_callback(upd, ctx))
            self.assertEqual(upd.callback_query.edit_message_text.await_args.args[0], bot.BUSY_TEXT)
        for m in (bot.hit_kopya_kul_geo_keyboard(), bot.hit_kopya_kul_produce_keyboard("V1")):
            for b in (b for r in m.inline_keyboard for b in r):
                self.assertLessEqual(len(b.callback_data.encode()), 64)

    def test_other_domains_no_button(self):
        import bot
        for i, d in enumerate(bot.DOMAIN_KEYS):
            if d == DOMAIN or not bot.domain_active(d):
                continue
            cbs = [b.callback_data for r in bot.event_keyboard(i).inline_keyboard for b in r]
            self.assertNotIn("uret:hkk", cbs, d)

    def test_only_pyroclastic(self):
        for e in es.EVENT_SKELETONS:
            self.assertEqual(hp.hit_kopya_kul_is_active(e), e == PY, e)
        with self.assertRaises(es.StructureError):
            hp.hit_kopya_kul_build_scene(DOMAIN, es.WILDFIRE)
        with self.assertRaises(es.StructureError):
            hp.hit_kopya_kul_build_scene("fire_disasters", PY)


class TestLocks(_Quiet):
    """Bu mod dışındaki bütün olaylar ve modlar (önceki kod 8b4c19f) 40 tohum birebir; bu modun kilidi
    HIT_KOPYA_KUL_SHA256 + fixture hit_kopya_kul_v3_runs_40.json (v1 ve v2 fixture pasif kilit olarak duruyor)."""

    def test_others_verbatim_40_seeds(self):
        snap = others_snapshot()
        self.assertEqual(len(snap["events"]), 19)
        for name, runs in snap["modes"].items():
            for s, r in runs.items():
                self.assertNotIn("error", r, (name, s))
        self.assertNotIn("hit_kopya_kul", snap["modes"])
        self.assertEqual(snapshot_hash(snap), OTHERS_SHA256)

    def test_hit_kopya_kul_lock_and_fixture(self):
        runs = hkk_snapshot()
        self.assertEqual(len(runs), 40)
        with open(FIXTURE, encoding="utf-8") as f:
            fixture = json.load(f)
        self.assertEqual(runs, fixture)
        self.assertEqual(snapshot_hash(fixture), HIT_KOPYA_KUL_SHA256)
        for s, r in runs.items():
            ax = r["axes"]["axes"]
            self.assertEqual((ax["mod"], ax["surum"], ax["cografya_kaynak"]), ("hit_kopya_kul", "v3", "rastgele"))
            self.assertEqual(r["prompt"], expected(ax["cografya"], ax["m"], ax["f"], ax["kisi"]))
            self.assertTrue(r["combo"].endswith(f"##HKK:{ax['cografya']}|bystander_handheld"), s)

    def test_v2_fixture_kept(self):
        with open(FIXTURE_V2, encoding="utf-8") as f:
            v2 = json.load(f)
        self.assertEqual(len(v2), 40)
        self.assertEqual(snapshot_hash(v2), HIT_KOPYA_KUL_SHA256_V2)
        for s, r in v2.items():
            ax = r["axes"]["axes"]
            self.assertEqual(ax["surum"], "v2")
            self.assertEqual(r["prompt"], TEMPLATE_V2.format(place=PLACES[ax["cografya"]], People=PEOPLE[ax["kisi"]],
                                                             M=MIDS_V2[ax["m"]], F=FINALS[ax["f"]]), s)

    def test_v1_fixture_kept(self):
        with open(FIXTURE_V1, encoding="utf-8") as f:
            v1 = json.load(f)
        self.assertEqual(len(v1), 40)
        self.assertEqual(snapshot_hash(v1), HIT_KOPYA_KUL_SHA256_V1)
        for s, r in v1.items():
            ax = r["axes"]["axes"]
            self.assertEqual(ax["surum"], "v1")
            self.assertEqual(r["prompt"], TEMPLATE_V1.format(place=PLACES_V1[ax["cografya"]], People=PEOPLE[ax["kisi"]],
                                                             M=MIDS_V1[ax["m"]], F=FINALS_V1[ax["f"]]), s)

    def test_locked_events_hash_file(self):
        import locked_prompts as lp
        self.assertEqual(lp.hashes(), lp.load())


if __name__ == "__main__":
    unittest.main()
