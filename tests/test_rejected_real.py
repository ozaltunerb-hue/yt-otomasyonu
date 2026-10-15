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
        for r in data:
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
            if "source" not in r:
                continue
            spec, slices, sl = rebuild(r)
            label = "4-9s" if sl == "slice_2" else "9-15"
            with self.subTest(text=r["text"]):
                self.assertIn(label, {i["missing"][:4] for i in es.strict_beat_issues(spec, slices)})
                self.assertNotIn(label, {i["missing"][:4] for i in es.soft_beat_issues(spec, slices)})

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
