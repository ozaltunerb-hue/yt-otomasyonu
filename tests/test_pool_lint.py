#!/usr/bin/env python3
"""
Havuz kontrolü (14 Eki 2026, Bahadır): yapılandırılmış olayların 4-9s / 9-15s maddeleri kameraya yakın, BÜYÜK, KOYU ve
kar/toz bulutunda kaybolmayan bir nesneye temas etmeli. Sebep: 14 Eki çığ testinde A5 (ince direkler) çıktı; zayıf
maddeler havuzda duruyordu.

Kurallar (her madde):
  (a) büyük/koyu bir yapı nesnesi içerir (STRONG),
  (b) zayıf nesneyi (WEAK: direk, kablo, korkuluk, cam, tabela...) tek başına hedef almaz: metindeki ilk nesne zayıfsa
      ihlal ("glass-fronted lodge entrance", "windows of a long wooden building"),
  (c) gömülme/kaybolma fiili ana fiil değildir: bu fiillerden biri var ve yıkım fiili yoksa ihlal.
Çığda ZORUNLU (kırmızıysa paket hata verir). Diğer kategorilerde sadece UYARI: ihlaller yazdırılır, maddeler
değiştirilmez. Ağ yok, Kie/GPT çağrısı yok.
"""
import os
import re
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import core.event_structure as es
from core.creative_pipeline import _term_re

STRONG = ("chalet", "lodge", "barn", "cabin", "shed", "woodshed", "hut", "annex", "wall", "porch", "deck", "log",
          "trunk", "tower", "house", "farmhouse", "shop", "building", "stable", "storefront", "garage",
          # Bahadır'ın listesine ek (büyük ve koyu, kaybolmaz): araçlar, çatı, büfe/ofis/durak, reklam panosu
          "car", "truck", "bus", "trailer", "roof", "rooftop", "kiosk", "office", "shelter", "billboard", "café",
          "cafe")
WEAK = ("fence post", "power pole", "utility pole", "pole", "railing", "cable", "wire", "window", "glass", "pane",
        "bench", "sign", "lamp", "awning")
# 14 Eki, Bahadır: SADECE deprem için ek büyük nesneler (kat, beton döşeme, blok). Diğer kategorilerin uyarıları değişmez.
EQ_STRONG_EXTRA = ("floor", "storey", "slab", "block")
BURY = ("bury", "buried", "engulf", "cover", "disappear", "swallow", "smother", "submerge", "vanish")
DESTROY = ("smash", "crash", "slam", "burst", "tear", "tore", "torn", "rip", "collapse", "topple", "hurl", "fling",
           "flung", "snap", "break", "broke", "shatter", "crush", "flatten", "sweep", "swept", "carry", "carried", "ram",
           "hit", "blow", "blew", "explode", "scatter", "split", "crack", "peel", "lift", "toss", "knock", "punch",
           "ignite", "cave", "tumble", "fall", "fell", "drag", "shove", "push", "strike", "struck", "plow", "spill")
# Öznedeki "snow wall", "wall of water" gibi ifadeler nesne sayılmaz
_SUBJECT = re.compile(r"\b(?:snow|mud|water|fire|flame|ash|dust|debris)\s+walls?\b|\bwalls? of (?:snow|water|mud|flames?|"
                      r"fire|ash|dust|debris|white)\b")
# Çığ dışında kalan zorunlu olmayan alanlar: araç yer tutucusu nesne sayılır (havuz aracı kendisi seçer)
_VEHICLE = "{vehicle}"


def _first(terms, text):
    hits = [m.start() for t in terms for m in [re.search(_term_re(t), text)] if m]
    return min(hits) if hits else None


def lint_beat(text: str, extra_strong: tuple = ()) -> list[str]:
    """Bir maddenin ihlalleri (boş liste = temiz). extra_strong: kategoriye özel ek büyük nesneler (14 Eki: deprem)."""
    low = _SUBJECT.sub(" ", (text or "").lower().replace(_VEHICLE, " vehicle "))
    out = []
    strong = _first(STRONG + ("vehicle",) + tuple(extra_strong), low)
    weak = _first(WEAK, low)
    if strong is None:
        out.append("(a) büyük/koyu yapı nesnesi yok")
    if weak is not None and (strong is None or weak < strong):
        out.append("(b) zayıf nesneyi tek başına hedef alıyor")
    if es.find_terms(BURY, low) and not es.find_terms(DESTROY, low):
        out.append("(c) gömülme/kaybolma ana fiil")
    return out


def pool_violations(events, extra_strong: tuple = ()) -> dict[str, list[str]]:
    out = {}
    for e in events:
        for slot in ("slice_2", "slice_3"):
            for bid, beat in es.EVENT_BEATS[e][slot].items():
                v = lint_beat(beat["text"], extra_strong)
                if v:
                    out[f"{e} / {bid}: {beat['text']}"] = v
    return out


class TestPoolLint(unittest.TestCase):
    def test_lint_catches_old_weak_avalanche_beats(self):
        # 14 Eki (3) öncesi zayıf maddeler kontrolden geçmemeli
        for text in ("the snow blast snaps a row of wooden fence posts and power poles",
                     "the snow wall buries a whole row of houses up to their roofs",
                     "the snow wall shatters a glass-fronted lodge entrance",
                     "the avalanche rips the wooden terrace railing off the lodge and sweeps it away",
                     "the snow blast flattens a line of wooden snow barriers and orange safety fences",
                     "the snow cloud engulfs the chairlift cables and a cable pylon topples",
                     "the snow cloud swallows a stand of tall pines whole, their tops whipping flat",
                     "the snow wall buries a wooden cabin to the roofline",
                     "the avalanche sweeps a row of fences and a footbridge railing away",
                     "the snow cloud blows the windows out of a long wooden building"):
            with self.subTest(text=text):
                self.assertTrue(lint_beat(text), text)
        # "snow wall" özne, nesne sayılmaz
        self.assertIn("(a) büyük/koyu yapı nesnesi yok", lint_beat("the snow wall rolls over the slope"))

    def test_avalanche_pools_mandatory(self):
        v = pool_violations(es.AVALANCHE_EVENTS)
        self.assertEqual(v, {}, "\n".join(f"{k}: {x}" for k, x in v.items()))

    def test_earthquake_pools_mandatory(self):
        # 14 Eki, Bahadır: deprem de zorunlu; kat/döşeme/blok sadece burada büyük nesne sayılır
        v = pool_violations(es.EARTHQUAKE_EVENTS, EQ_STRONG_EXTRA)
        self.assertEqual(v, {}, "\n".join(f"{k}: {x}" for k, x in v.items()))
        # onaydan önceki metinler yakalanırdı (Q2 gömme fiili, R3 yapı yok)
        self.assertTrue(lint_beat("the dust wave rolls down the street and engulfs the buildings opposite",
                                  EQ_STRONG_EXTRA))
        self.assertTrue(lint_beat("a thick dust cloud pours down the narrow street from the collapse", EQ_STRONG_EXTRA))
        # ek liste diğer kategorilere uygulanmaz
        self.assertIn("(a) büyük/koyu yapı nesnesi yok", lint_beat("the upper floors give way"))

    def test_avalanche_lift_beats_excluded_at_lift_station(self):
        # (†) teleferik maddesi istasyon terasında seçilmez. 14 Eki (3) itibarıyla teleferik maddesi yok; kural,
        # madde geri gelirse dışlamanın unutulmaması için duruyor.
        b = es.EVENT_BEATS[es.AVALANCHE_SKI]
        for slot in ("slice_2", "slice_3"):
            for bid, beat in b[slot].items():
                if es.find_terms(es._AVA_LIFT, beat["text"]):
                    with self.subTest(beat=bid):
                        self.assertIn("Terrace of the lift station", b["excluded_spots"].get(bid, set()))
        self.assertTrue(es.find_terms(es._AVA_LIFT, "the avalanche front mows down a row of ski-lift towers"))

    def test_other_categories_warning_only(self):
        # Volkan, kıyı, sel, heyelan, hortum, yangın: sadece rapor (Bahadır: değiştirme)
        others = [e for e in es.EVENT_BEATS if e not in es.AVALANCHE_EVENTS + es.EARTHQUAKE_EVENTS]
        self.assertTrue(others)
        v = pool_violations(others)
        if v:
            sys.stderr.write(f"\n⚠️ HAVUZ KONTROLÜ UYARI ({len(v)} madde, çığ ve deprem dışı, değiştirilmedi):\n")
            for k, x in v.items():
                sys.stderr.write(f"  - {k} -> {', '.join(x)}\n")


if __name__ == "__main__":
    unittest.main()
