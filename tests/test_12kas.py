# 12 Kas 2026, Bahadır: dev dalga kadrajında tehlikenin boyutu (ateş hortumunun kanıtlanmış kalıbı). (2) K_R1, K_R2,
# K_R4'te "high vantage, wide angle, " ifadesinden hemen sonra birebir parça; K_R3 (pasif) aynen. (3) sadece dev dalga
# tavanı 230 kelime / 1400 karakter. Kilitli 8 olay değişmez (test_kilit_6kas).
import logging
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import core.event_structure as es   # noqa: E402
import core.creative_pipeline as cp   # noqa: E402,F401
import core.frame_axis as fx   # noqa: E402
import prompt_snapshot as ps   # noqa: E402

TI = es.TIDAL
DANGER = "the tidal wave filling half the frame, its crest never cut off, people fleeing below, "
ANCHOR = "high vantage, wide angle, "


class _Quiet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.disable(logging.WARNING)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)


class TestDangerSize(_Quiet):
    def test_active_frames_have_phrase_right_after_anchor(self):
        for k in ("K_R1", "K_R2", "K_R4"):
            text = fx.VERBATIM_FRAMES[TI][k][0]
            self.assertEqual(text.count(DANGER), 1, k)
            self.assertIn(ANCHOR + DANGER, text, k)

    def test_passive_k_r3_unchanged(self):
        self.assertNotIn(DANGER, fx.VERBATIM_FRAMES[TI]["K_R3"][0])
        self.assertEqual(fx.PASSIVE_VERBATIM_FRAMES[TI], {"K_R3"})

    def test_other_events_have_no_phrase(self):
        for e, frames in fx.VERBATIM_FRAMES.items():
            if e == TI:
                continue
            for k, (text, _) in frames.items():
                self.assertNotIn("tidal wave filling half the frame", text, (e, k))

    def test_cap_230_only_tidal(self):
        self.assertEqual(es.max_prompt_words(TI), 230)
        self.assertEqual(es.max_prompt_chars(TI), 1400)
        self.assertEqual(es.max_prompt_words(es.FIRE_TORNADO), 215)
        self.assertEqual(es.max_prompt_words(es.PYROCLASTIC), 215)

    def test_40_seeds_build_with_phrase_within_caps(self):
        for seed in range(1, 41):
            snap = ps.snapshot_event(TI, seed)
            self.assertNotIn("error", snap, seed)
            self.assertIn(ANCHOR + DANGER.rstrip(), snap["prompt"] + " " + snap["style_suffix"], seed)
            self.assertLessEqual(len(snap["prompt"].split()), 230, seed)
            self.assertLessEqual(len(snap["prompt"]), 1400, seed)


if __name__ == "__main__":
    unittest.main()
