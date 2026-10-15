#!/usr/bin/env python3
"""
Canlı retler kalıcı regresyon (15 Eki 2026, Bahadır): tests/fixtures/rejected_real.json.
- false_rejections: kapının yanlış reddettiği gerçek GPT cümleleri; seçilen maddenin kapısından geçmeli.
- correct_rejections: kapının doğru reddettiği cümleler; ret sürmeli.
Yeni bir canlı ret görülürse JSON'a eklenir, test kendiliğinden kapsar. Ağ yok, Kie/GPT çağrısı yok.
"""
import json
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import core.event_structure as es

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "rejected_real.json")


def load():
    with open(FIXTURE, encoding="utf-8") as f:
        return json.load(f)


def slot_of(event, bid):
    return next(sl for sl in ("slice_2", "slice_3") if bid in es.EVENT_BEATS[event][sl])


class TestRejectedReal(unittest.TestCase):
    def test_false_rejections_now_pass(self):
        data = load()["false_rejections"]
        self.assertGreaterEqual(len(data), 9)
        for r in data:
            e, bid, text = r["event"], r["beat"], r["text"]
            with self.subTest(event=e, beat=bid, text=text):
                sl = slot_of(e, bid)
                self.assertEqual(es.beat_missing(es.EVENT_BEATS[e][sl][bid], text), [])
                if r.get("vehicle"):   # araç kapısı da geçer (madde araçlıysa)
                    vt = dict(es.event_vehicles(e, None))[r["vehicle"]]
                    self.assertTrue(es.find_terms(vt, text))
                # tam dilim kapısında "seçilen olay görünmüyor" ve araç retleri yok
                b2 = bid if sl == "slice_2" else next(iter(es.EVENT_BEATS[e]["slice_2"]))
                b3 = bid if sl == "slice_3" else next(iter(es.EVENT_BEATS[e]["slice_3"]))
                vehicle = r.get("vehicle") or next(v for v, _ in es.event_vehicles(e, None))
                issues = es.slice_issues(
                    es.build_spec(e, None, _spot(e), None, b2, b3, vehicle, 3),
                    {"slice_1_rest": "Three people run from it right below.",
                     "slice_2": text if sl == "slice_2" else es.beat_text(e, "slice_2", b2, vehicle),
                     "slice_3": text if sl == "slice_3" else es.beat_text(e, "slice_3", b3)})
                self.assertFalse({i["rule"] for i in issues} & {"beat_terms", "beat_vehicle"},
                                 [i["missing"] for i in issues])

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


if __name__ == "__main__":
    unittest.main()
