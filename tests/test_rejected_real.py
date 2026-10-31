#!/usr/bin/env python3
"""
Canlı retler kalıcı regresyon (15 Eki 2026, Bahadır): tests/fixtures/rejected_real.json.
- false_rejections: kapının yanlış reddettiği gerçek GPT cümleleri; seçilen maddenin kapısından geçmeli.
- correct_rejections: kapının doğru reddettiği cümleler; ret sürmeli.
Yeni bir canlı ret görülürse JSON'a eklenir, test kendiliğinden kapsar. Ağ yok, Kie/GPT çağrısı yok.
16 Eki 2026 (hibrit hikâye): beat kapısı yumuşak (ana nesne). Bütün yanlış retler yeni kapıdan (dilim kapısında beat_*
kodu yok) geçer. 15 Eki canlı retleri ("source" alanı yok) eski sıkı kapıdan da geçer (o gün düzeltildiler). "source"
alanlı kayıtlar 2i gerçek GPT kuru denemesinden otomatik eklendi (scripts/dry_run_hybrid.py --fixtures-from): eski kapı
reddediyordu, yeni kapı geçiriyor; üretim birebir kurulur (nokta, görünüm, beat çifti, araç, kişi).
"""
import json
import re
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import core.event_structure as es

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "rejected_real.json")
BEAT_RULES = {"beat_terms", "beat_vehicle", "beat_object", "beat_other_object"}


def load():
    with open(FIXTURE, encoding="utf-8") as f:
        return json.load(f)


def retired(r) -> bool:
    """17 Eki (temizlik turu): kaydın maddesi havuzdan çıktı (es.RETIRED_BEATS). Kayıt dosyada kalır (geçmiş), test
    atlar ve sayar."""
    return r["beat"] in es.RETIRED_BEATS.get(r["event"], {})


def current(r) -> dict:
    """Kaydı bugünkü havuza çevirir (17 Eki): çıkarılan küçük araç adı yerine gelen büyük araç (kayıt ve cümlede),
    çiftin diğer maddesi çıkmışsa çift bilgisi düşer (rebuild dilimin ilk maddesini alır)."""
    r = dict(r)
    old = r.get("vehicle")
    if old in es.RETIRED_VEHICLES:
        new = es.retired_vehicle(old, r.get("view"))
        text = re.sub(re.escape(old), new, r["text"], count=1, flags=re.IGNORECASE)
        if text == r["text"]:   # cümle aracı kısa adla anıyor ("the hatchback", "the car")
            text = re.sub(r"\b%s\b" % re.escape(old.split()[-1]), new, r["text"], count=1, flags=re.IGNORECASE)
        r["vehicle"], r["text"] = new, text
    if r.get("beats") and any(b in es.RETIRED_BEATS.get(r["event"], {}) for b in r["beats"].split("+")):
        r.pop("beats")
    return r


# 22 Eki (heyelan denetimi): metni değişen beat'ler (kod aynı). Eski metne göre kaydedilen 2i cümleleri (ör. M6 "porch")
# artık eski kapının reddettiği cümle değil; bu testte atlanır, kayıt dosyada kalır.
REWRITTEN = {(es.MUDSLIDE, b) for b in ("H2", "H4", "H6", "M3", "M6")} | \
            {(es.SLOPE, b) for b in ("R2", "R4", "R6", "S4")} | {(es.VILLAGE, b) for b in ("K3", "L5", "L6")}
# 23 Eki (hortum denetimi): karaya vurur ve marinada metni değişen beat'ler. Eski metne göre kaydedilen cümleler (ör. Z1
# "awning") yeni maddeyi anlatmıyor; iki testte de atlanır, kayıt dosyada kalır.
REWRITTEN_TORNADO = {(es.LANDFALL, b) for b in ("C1", "C2", "E1", "E2")} |                     {(es.MARINA_TORNADO, b) for b in ("Y1", "Y3", "Y5", "Z1", "Z2", "Z3", "Z6", "Z7")}
# 30 Eki (cadde P/Q onaylı + Aşama B zayıf beat değişimi): metni değişen beat'ler; eski metne göre kaydedilen cümleler
# (ör. N5 "windows", Q3 "signs") yeni maddeyi anlatmıyor; iki testte de atlanır, kayıt dosyada kalır.
REWRITTEN_30OCT = {(es.FLOOD, b) for b in ("V6", "V7", "V8")} | {(es.TIDAL, b) for b in ("T4", "T8")} |                   {(es.WILDFIRE, "K2"), (es.VOLCANIC_BOMBS, "T7"), (es.PYROCLASTIC, "Q6"), (es.AVALANCHE_VILLAGE, "A1"),
                   (es.EARTHQUAKE_APARTMENT, "Q2"), (es.EARTHQUAKE_OLD_STREET, "T3"), (es.EARTHQUAKE_OLD_STREET, "T4")} |                   {(es.FACADE_FIRE, b) for b in ("M11", "N3", "N5")} |                   {(es.HELICOPTER, b) for b in ("F2", "F4", "F6", "G6", "G7")} |                   {(es.AVENUE, b) for b in ("P1", "P2", "P5", "Q3", "Q4", "Q6")} | \
                  {(es.WILDFIRE, "K9"), (es.HELICOPTER, "G3"), (es.AVALANCHE_VILLAGE, "B2"),
                   (es.EARTHQUAKE_OLD_STREET, "R3")} | {(es.AVALANCHE_SKI, b) for b in ("C4", "C6", "D5")} | \
                  {(es.AVENUE, "Q2")}   # 30 Eki (2)-(3)
# 31 Eki (3), Bahadır (zayıf finaller): heyelan M4, cephe N1, helikopter F5 yeni metin (M3 yukarıda). Eski metne göre
# kaydedilen cümleler (F5 "cascade of water hits a burning house") yeni maddeyi anlatmıyor; atlanır, kayıt dosyada kalır.
REWRITTEN_31OCT = {(es.MUDSLIDE, "M4"), (es.FACADE_FIRE, "N1"), (es.HELICOPTER, "F5")}
REWRITTEN = REWRITTEN | REWRITTEN_TORNADO | REWRITTEN_30OCT | REWRITTEN_31OCT


def slot_of(event, bid):
    return next(sl for sl in ("slice_2", "slice_3") if bid in es.EVENT_BEATS[event][sl])


def rebuild(r):
    """(spec, dilimler): kaydın cümlesi kendi diliminde, diğer dilimler madde metni."""
    e, bid, text = r["event"], r["beat"], r["text"]
    sl = slot_of(e, bid)
    if r.get("beats"):
        b2, b3 = r["beats"].split("+")
    else:
        b2 = bid if sl == "slice_2" else next(iter(es.EVENT_BEATS[e]["slice_2"]))
        b3 = bid if sl == "slice_3" else next(iter(es.EVENT_BEATS[e]["slice_3"]))
    view = r.get("view")
    spot = r.get("spot") or _spot(e)
    if es.uses_vehicle(e):
        vehicle = r.get("vehicle") or next(v for v, _ in es.event_vehicles(e, view))
        if r.get("beats") and not r.get("vehicle"):   # 9-15s kaydı: aracı üretimden bilinmiyor, listenin ilki
            vehicle = next(v for v, _ in es.event_vehicles(e, view))
    else:
        vehicle = None
    lo, _ = _count(e)
    people = r.get("people") or (lo if es.has_people_rule(e) else None)
    spec = es.build_spec(e, None, spot, view, b2, b3, vehicle, people if es.has_people_rule(e) else None)
    slices = {"slice_1_rest": "Three people run from it right below.",
              "slice_2": text if sl == "slice_2" else es.beat_text(e, "slice_2", b2, vehicle),
              "slice_3": text if sl == "slice_3" else es.beat_text(e, "slice_3", b3)}
    return spec, slices, sl


class TestRejectedReal(unittest.TestCase):
    def test_false_rejections_now_pass(self):
        data = load()["false_rejections"]
        self.assertGreaterEqual(len(data), 9)
        skipped = [r for r in data if retired(r)]
        # 17 Eki: çıkarılan maddelerin kayıtları (ateş hortumu T3/U3/U4, heyelan S6 ...) atlanır, sayısı kilitli
        self.assertEqual(len(skipped), 30, sorted({(r["event"][:20], r["beat"]) for r in skipped}))
        for r in data:
            if retired(r) or (r["event"], r["beat"]) in REWRITTEN_TORNADO | REWRITTEN_30OCT | REWRITTEN_31OCT:
                continue
            r = current(r)
            e, bid, text = r["event"], r["beat"], r["text"]
            with self.subTest(event=e, beat=bid, text=text):
                spec, slices, sl = rebuild(r)
                if "source" not in r:   # 15 Eki canlı retleri: eski sıkı kapıdan da geçer
                    self.assertEqual(es.beat_missing(es.EVENT_BEATS[e][sl][bid], text), [])
                if r.get("vehicle") and "{vehicle}" in es.EVENT_BEATS[e][sl][bid]["text"]:   # madde araçlıysa araç adı da var
                    self.assertTrue(es.find_terms(es.spec_vehicle_terms({**spec, "vehicle": r["vehicle"]}), text))
                issues = es.slice_issues(spec, slices)
                self.assertFalse({i["rule"] for i in issues} & BEAT_RULES, [i["missing"] for i in issues])

    def test_auto_added_entries_were_old_gate_rejections(self):
        # 2i kayıtları: eski sıkı kapı reddeder, yeni yumuşak kapı geçirir (kaydın nedeni)
        for r in load()["false_rejections"]:
            if "source" not in r or retired(r) or (r["event"], r["beat"]) in REWRITTEN:
                continue
            r = current(r)
            spec, slices, sl = rebuild(r)
            label = "4-9s" if sl == "slice_2" else "9-15"
            with self.subTest(text=r["text"]):
                self.assertIn(label, {i["missing"][:4] for i in es.strict_beat_issues(spec, slices)})
                self.assertNotIn(label, {i["missing"][:4] for i in es.soft_beat_issues(spec, slices)})

    def test_17oct_soft_gate_fixes(self):
        # 17 Eki, Bahadır: 2i kuru denemede yanlış reddedilen üç cümle tipi artık geçer (kayıtlar "origin" alanlı)
        fixed = [r for r in load()["false_rejections"] if "17 Eki" in r.get("origin", "")]
        self.assertEqual({(r["event"], r["beat"]) for r in fixed},
                         {(es.HELICOPTER, "F5"), (es.HELICOPTER, "G1"), (es.EARTHQUAKE_OLD_STREET, "T2")})
        for r in fixed:
            if retired(r):   # 18 Eki (2): deprem T2 çıktı (Parti 2); kaydı tarih olarak durur
                self.assertEqual((r["event"], r["beat"]), (es.EARTHQUAKE_OLD_STREET, "T2"))
                continue
            if (r["event"], r["beat"]) in REWRITTEN_31OCT:   # 31 Eki (3): F5 yeni metin (güverte), kayıt tarih
                continue
            spec, slices, sl = rebuild(current(r))
            with self.subTest(text=r["text"]):
                self.assertEqual(es.soft_beat_issues(spec, slices), [])
        # helikopter: kural kapatılırsa F5 cümlesi yine F1'e benzetilip reddedilirdi (düzeltmenin sebebi). 31 Eki (3):
        # F5 yeni metin (güverte), eski ev cümlesiyle bu ölçüm yapılamaz; kural aynen duruyor
        self.assertEqual(es.OWN_OBJECT_ENOUGH_EVENTS, (es.HELICOPTER,))   # diğer olaylarda benzerlik kontrolü aynen
        # "treetops" sadece helikopter listesinde; orman yangınının _FIRE_TREE listesi değişmedi
        self.assertTrue(es.find_terms(es._FIRE_HELI_TREE, "the treetops burn"))
        self.assertFalse(es.find_terms(es._FIRE_TREE, "the treetops burn"))
        # deprem T2 (18 Eki (2): havuzdan çıktı); "sequentially" zincir grubunda kalır
        self.assertNotIn("T2", es.OBJECT_GROUPS[es.EARTHQUAKE_OLD_STREET])
        self.assertIn("sequentially", es._EQ_CHAIN)

    def test_correct_rejections_still_rejected(self):
        for r in load()["correct_rejections"]:
            e = r["event"]
            with self.subTest(event=e, text=r["text"]):
                b2, b3 = next(iter(es.EVENT_BEATS[e]["slice_2"])), next(iter(es.EVENT_BEATS[e]["slice_3"]))
                vehicle = next(v for v, _ in es.event_vehicles(e, None))
                spec = es.build_spec(e, None, _spot(e), None, b2, b3, vehicle, r["people"])
                sl = {"slice_1_rest": es.beat_text(e, "slice_2", b2, vehicle),
                      "slice_2": es.beat_text(e, "slice_2", b2, vehicle), "slice_3": es.beat_text(e, "slice_3", b3)}
                sl[r["field"]] = r["text"]
                self.assertIn(r["rule"], {i["rule"] for i in es.slice_issues(spec, sl)})


def _spot(event):
    import core.skeleton_pipeline as sk
    return next(iter(sk.EVENT_SKELETONS[event]["spots"]))


def _count(event):
    import core.skeleton_pipeline as sk
    return sk.count_range(event, None)


if __name__ == "__main__":
    unittest.main()
