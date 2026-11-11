# 11 Kas 2026 (8), Bahadır: dev dalga yapay görünüyordu (dalga uzakta donuk, insanlar dalgaya doğru koştu, kamera
# sinematik). (1) K_R1, K_R2, kül bulutu K_V elde çekim ifadesi; (2) K_R3 pasif, K_R4 yeni; (3) dev dalga insan
# cümleleri kameraya göre yön (I10-I12), önceki aktifler pasif. Kilitli 8 olay değişmez (test_kilit_6kas).
import logging
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import core.event_structure as es   # noqa: E402
import core.creative_pipeline as cp   # noqa: E402
import core.frame_axis as fx   # noqa: E402
import core.pool_word_gate as gate   # noqa: E402
import prompt_snapshot as ps   # noqa: E402

PY, TI = es.PYROCLASTIC, es.TIDAL
K_R4 = ("Handheld footage filmed from the top-floor balcony of a seafront hotel right on the promenade, high vantage, "
        "wide angle, the sea and the coastal street directly below in frame; slight hand shake, the camera stays fixed, "
        "never descending, the camera never pans, turns or follows.")
I_NEW = ("{N} people sprint up the street toward the camera, the wave right behind them.",
         "{N} pedestrians run toward the camera and into the apartment entrance right below it.",
         # Bahadır onayıyla kısa hâl (verilen 20 kelimelik metin 0-4s sınırına, 18, sığmıyordu)
         "{N} people race up the steps of the building below the camera as the wave hits.")


class _Quiet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.disable(logging.WARNING)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)


class TestFrames(_Quiet):
    def test_handheld_phrase(self):
        for e, k in ((TI, "K_R1"), (TI, "K_R2"), (TI, "K_R4"), (PY, "K_V")):
            t = fx.VERBATIM_FRAMES[e][k][0]
            with self.subTest(frame=k):
                self.assertTrue(t.startswith("Handheld footage filmed from "), t)
                self.assertIn("; slight hand shake, the camera stays fixed, never descending, ", t)
                self.assertNotIn("Filmed from", t)
                self.assertEqual(gate.term_hits(t, e), [])

    def test_k_r3_passive_k_r4_new(self):
        self.assertEqual(fx.VERBATIM_FRAMES[TI]["K_R4"], (K_R4, "korkuluk"))
        self.assertIn("K_R3", fx.VERBATIM_FRAMES[TI])   # silinmedi
        self.assertEqual(fx.PASSIVE_VERBATIM_FRAMES[TI], {"K_R3"})
        self.assertEqual({f["type"] for f in fx.verbatim_variants(TI)}, {"K_R1", "K_R2", "K_R4"})
        cam = fx.verbatim_camera(TI, {"type": "K_R4", "pos_spot": None, "fg": "korkuluk", "mode": None})
        self.assertEqual(cam, K_R4 + " A railing corner in the foreground, one continuous shot, no zoom, no cuts.")


class TestPeople(_Quiet):
    def test_lines_verbatim_and_passive(self):
        pool = es.FALLBACK_PEOPLE[TI]
        self.assertEqual(pool[9:12], I_NEW)
        self.assertEqual(len(pool), 12)   # I1-I9 silinmedi
        self.assertEqual(es.DISABLED_PEOPLE_LINES[TI], {f"I{i}" for i in range(1, 10)})
        self.assertEqual(es.people_axis_proven(TI), ("I10", "I11", "I12"))
        for t in I_NEW:
            self.assertEqual(gate.term_hits(t, TI), [], t)
            self.assertNotIn("away from", t)

    def test_all_fit_every_frame_and_pair(self):
        mids = [b for b in es.EVENT_BEATS[TI]["slice_2"] if b not in es.disabled_beats(TI)]
        fins = [b for b in es.EVENT_BEATS[TI]["slice_3"] if b not in es.disabled_beats(TI)]
        for f in fx.verbatim_variants(TI):
            for m in mids:
                for w in fins:
                    spec = es.build_spec(TI, None, "Coastal street of low shopfronts", "riviera", m, w, "red SUV", 6,
                                         frame=f, light="driving rain and wind")
                    with self.subTest(frame=f["type"], pair=(m, w)):
                        self.assertEqual({i for i, _ in es.fallback_candidates_ids(spec)}, {"I10", "I11", "I12"})

    def test_camera_word_exempt_only_code_sentence(self):
        self.assertIn(TI, es.CAMERA_EXEMPT_EVENTS)
        spec = es.build_spec(TI, None, "Coastal street of low shopfronts", "riviera", "T2", "W10", "red SUV", 4,
                             frame=fx.verbatim_variants(TI)[0], light="driving rain and wind")
        pid, code = es.fallback_candidates_ids(spec)[0]
        spec = {**spec, "people_line": pid}   # hatta seçilen insan kimliği spec'te
        gpt = dict(code, slice_2="The camera shakes as the red SUV is swept into a row of parked cars.")
        def rules(sl):
            return [i["rule"] for i in es.verbatim_story_exempt(
                spec, sl, cp.story_rule_issues(TI, spec["ship"], es.plain_story(spec, sl)))]
        self.assertNotIn("b_no_camera_words", rules(code))   # sadece birebir kod cümlesinde kamera: muaf
        self.assertIn("b_no_camera_words", rules(gpt))   # GPT'nin yazdığı cümlede kamera kelimesi yine ret

    def test_snapshots(self):
        lines = {es.clean_slice(t.format(N=n)).split(" ", 1)[1] for t in I_NEW
                 for n in ("Three", "Four", "Five", "Six")}
        for seed in range(1, 41):
            snap = ps.snapshot_event(TI, seed)
            self.assertNotIn("error", snap, seed)
            self.assertIn(snap["axes"]["kadraj"], {"K_R1", "K_R2", "K_R4"})
            head = snap["prompt"].split("4-9s:")[0]
            self.assertTrue(any(l in head for l in lines), (seed, head))
            self.assertNotIn("away from", head)
            self.assertIn("Handheld footage filmed from", snap["prompt"])
            self.assertLessEqual(len(snap["prompt"].split()), es.max_prompt_words(TI))


if __name__ == "__main__":
    unittest.main()
