#!/usr/bin/env python3
"""4 Kas 2026 (3), Bahadır: Özgürlük Anıtı kamera düzeltmesi + küçük çift düzeltmeleri.

1) Anıt kamera eki: "the tornado always in frame" -> "the camera never pans, turns or follows" (sadece bu olay).
2) Anıt çiftleri: (B1, C2) dışlı; C6 sadece B5 ile.
3) Anıt ilk iyi video kaydı (tests/fixtures/liberty_good_videos.json); OZGURLUK_DOGRULAMA açık kalır.
4) Sel: (V11, D18) dışlı.
"""
import json
import logging
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (ROOT, os.path.join(ROOT, "scripts"), os.path.join(ROOT, "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import prompt_snapshot as ps   # noqa: E402
import core.event_structure as es   # noqa: E402
import core.frame_axis as fx   # noqa: E402
import core.skeleton_pipeline as sk   # noqa: E402

L = es.LIBERTY
F = es.FLOOD
OLD = "the tornado always in frame"
NEW = "the camera never pans, turns or follows"
TAIL = ("slight hand shake, the camera stays fixed, never descending, the camera never pans, turns or follows; one "
        "continuous shot, no zoom, no cuts.")
B = ("B1", "B2", "B3", "B4", "B5", "B6")
C = ("C1", "C2", "C3", "C4", "C6")


class _Quiet(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.WARNING)

    def tearDown(self):
        logging.disable(logging.NOTSET)


class TestLibertyCamera(_Quiet):
    def test_tail_text(self):
        self.assertEqual(sk.LIBERTY_CAMERA_TAIL, TAIL)
        self.assertIn(OLD, sk.LIBERTY_CAMERA_TAIL_4KAS)   # önceki hâl silinmedi
        for spot in sk.LIBERTY_CAMERA:
            cam = sk.liberty_camera(spot)
            self.assertIn(NEW, cam)
            self.assertNotIn(OLD, cam)
            self.assertIn("the Statue of Liberty standing intact in the distance across the harbor", cam)

    def test_frames_use_new_tail(self):
        for spot in sk.EVENT_SKELETONS[L]["spots"]:
            frame = fx.all_frames(L, spot, [spot])[0]
            cam = sk.camera_rules(fx.frame_camera(L, spot, frame, legacy=sk.legacy_camera))
            self.assertIn(NEW, cam)
            self.assertNotIn("always in frame", cam)

    def test_snapshot_prompts(self):
        for seed, r in ps.snapshot_all([L], seeds=range(1, 41))[L].items():
            self.assertNotIn("error", r, seed)
            self.assertIn(NEW, r["prompt"], seed)
            self.assertNotIn(OLD, r["prompt"], seed)
            self.assertLessEqual(len(r["prompt"].split()), 205, seed)
            self.assertLessEqual(len(r["prompt"]), 1400, seed)

    def test_other_events_untouched(self):
        # 'always in frame' kuyrukları başka olaylarda aynen duruyor (ör. cephe yangını, frame_axis)
        self.assertIn("always in frame", open(fx.__file__, encoding="utf-8").read())
        for seed, r in ps.snapshot_all([es.AVENUE], seeds=range(1, 6))[es.AVENUE].items():
            self.assertNotIn(NEW, r["prompt"], seed)


class TestLibertyPairs(_Quiet):
    def test_exclusions(self):
        ex = es.EVENT_BEATS[L]["excluded_pairs"]
        self.assertIn(("B1", "C2"), ex)
        for b in ("B1", "B2", "B3", "B4", "B6"):
            self.assertIn((b, "C6"), ex, b)
        self.assertNotIn(("B5", "C6"), ex)

    def test_pair_count(self):
        for spot in sk.view_spots(L, None):
            pairs = es.allowed_pairs(L, None, spot)
            self.assertEqual(len(pairs), 22, spot)
            self.assertEqual([p for p in pairs if p[1] == "C6"], [("B5", "C6")])
            self.assertNotIn(("B1", "C2"), pairs)
            for bid in B + C:   # her öğe en az bir çiftte
                self.assertTrue(any(bid in p for p in pairs), bid)


class TestLibertyGoodVideo(_Quiet):
    def test_fixture(self):
        with open(os.path.join(ROOT, "tests", "fixtures", "liberty_good_videos.json"), encoding="utf-8") as f:
            v = json.load(f)["videos"][0]
        self.assertEqual((v["date"], v["event"], v["frame"], v["light_id"], v["beats"], v["people"], v["score"]),
                         ("2026-11-04 04:13", L, "K1", "L2", "B5+C3", "P2", "8/10"))
        self.assertTrue(v["lock_sentence"])
        self.assertIn(v["spot"], sk.LIBERTY_CAMERA)
        self.assertIn(v["light"], sk.EVENT_SKELETONS[L]["weather"])
        self.assertTrue(es.OZGURLUK_DOGRULAMA)   # statü değişmedi
        self.assertIn("B5", es.TRIAL_BEATS[L])
        self.assertIn("C3", es.TRIAL_BEATS[L])


class TestFloodPair(_Quiet):
    def test_v11_d18_excluded(self):
        self.assertIn(("V11", "D18"), es.EVENT_BEATS[F]["excluded_pairs"])
        for view in es.structure_views(F):
            for spot in sk.view_spots(F, view):
                pairs = es.allowed_pairs(F, view, spot)
                self.assertNotIn(("V11", "D18"), pairs)
                self.assertEqual(len(pairs), 37, (view, spot))
                self.assertGreaterEqual(len([p for p in pairs if "V11" in p]), 2)
                self.assertGreaterEqual(len([p for p in pairs if "D18" in p]), 2)


if __name__ == "__main__":
    unittest.main()
