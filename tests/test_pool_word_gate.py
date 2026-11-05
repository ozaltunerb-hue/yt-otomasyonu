#!/usr/bin/env python3
"""6 Kasım 2026, Bahadır (Aşama 3): kilitsiz havuz metni kelime kapısı. Yeni bir havuz öğesine yasak kök eklenirse bu test
kırılır. Kilitli 8 olay muaf. Ağ yok, Kie/GPT çağrısı yok."""
import logging
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import prompt_snapshot  # noqa: E402,F401
import core.event_structure as es   # noqa: E402
import core.opening_axis as ox   # noqa: E402
import core.pool_word_gate as gate   # noqa: E402


class _Quiet(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.WARNING)

    def tearDown(self):
        logging.disable(logging.NOTSET)


class TestTerms(unittest.TestCase):
    def test_every_banned_form(self):
        for text, term in (("the car is swept up", "swept up"), ("lift", "lift"), ("it lifted", "lift"),
                           ("lifting a van", "lift"), ("planks fly", "fly"), ("it flies", "fly"),
                           ("sent flying", "fly"), ("flung into the air", "flung into the air"), ("spin", "spin"),
                           ("it spun", "spin"), ("spinning", "spin"), ("flip", "flip"), ("flipped", "flip"),
                           ("roll over", "roll over"), ("rolls over", "roll over"), ("rolled over", "roll over"),
                           ("rolls the {vehicle} over", "roll over"), ("onto its roof", "onto its roof"),
                           ("toss", "toss"), ("tossed", "toss"), ("tosses", "toss"), ("crushed", "crushed"),
                           ("concrete", "concrete"), ("follow", "follow"), ("follows", "follow"),
                           ("the wave always in frame", "always in frame")):
            with self.subTest(text=text):
                self.assertIn(term, gate.term_hits(text))

    def test_clean_words_pass(self):
        for text in ("the cloud front rolls on across the street", "the fire tornado tears across the road",
                     "the kite is uplifted", "buttoned spinach", "a stone wall collapses"):
            with self.subTest(text=text):
                self.assertEqual(gate.term_hits(text), [])

    def test_mandated_camera_phrase_allowed_only_exact(self):
        self.assertEqual(gate.term_hits("the camera never pans, turns or follows"), [])
        self.assertEqual(gate.term_hits("the camera follows the wave"), ["follow"])


class TestGate(_Quiet):
    def test_no_new_hits(self):
        """Yeni takılma yok. Takılanların listesi gate.KNOWN_HITS (dokunulmadı, karar Bahadır'da)."""
        new = {k: v for k, v in gate.scan(gate.unlocked_events()).items() if k not in gate.KNOWN_HITS}
        self.assertEqual(new, {})

    def test_new_beat_breaks(self):
        event = es.METEOR
        pool = es.EVENT_BEATS[event]["slice_3"]
        pool["X9"] = {"text": "the blast flips a bus into a villa wall", "terms": []}
        try:
            found = gate.scan([event], camera_seeds=())
        finally:
            del pool["X9"]
        self.assertIn((event, "beat", "X9", "flip"), found)
        self.assertNotIn((event, "beat", "X9", "flip"), gate.KNOWN_HITS)

    def test_new_opening_breaks(self):
        event = es.AVENUE
        ox.OPENINGS[event]["Z"] = "The tornado tosses a bus."
        try:
            found = gate.scan([event], camera_seeds=())
        finally:
            del ox.OPENINGS[event]["Z"]
        self.assertIn((event, "acilis", "Z", "toss"), found)

    def test_passive_items_not_counted(self):
        found = gate.scan([es.TIDAL], camera_seeds=())
        self.assertNotIn((es.TIDAL, "beat", "T4", "crushed"), found)   # T4 pasif, "crushing" içerir

    def test_locked_exempt(self):
        self.assertFalse(set(gate.unlocked_events()) & set(es.LOCKED_EVENTS))
        self.assertFalse({k[0] for k in gate.KNOWN_HITS} & set(es.LOCKED_EVENTS))

    def test_tidal_camera_clean(self):
        found = gate.scan([es.TIDAL], camera_seeds=range(1, 5))
        self.assertFalse([k for k in found if k[1] == "kamera"], found)


if __name__ == "__main__":
    unittest.main()
