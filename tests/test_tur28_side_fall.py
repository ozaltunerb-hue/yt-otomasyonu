#!/usr/bin/env python3
"""
TUR 28 (2026-09-27): side launch'ta "slipway" yok ("side-launch berth at the quay edge"), gemi uzun yanı
kameraya dönük yan düşer (bow-first/stern-first yasak), kamera aynı rıhtımda ~50 m, sabit büyüklük.
Gerçek API yok.
"""
import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import core.prompt_generator as pg
from core.creative_engine import (
    DOMAIN_ATTRIBUTES,
    SIDE_LAUNCH_ENV,
    SIDE_LAUNCH_EVENT,
    style_lock_suffix,
)

D = "shipyard_and_drydock_engineering"
CAT = {"domain_id": D, "forced_ship": "Passenger Car Ferry", "forced_event": SIDE_LAUNCH_EVENT,
       "forced_environment": SIDE_LAUNCH_ENV}
FIRST = ("The passenger car ferry, its entire long side facing the camera, tips sideways off the quay edge and "
         "drops broadside into the water as six workers sprint clear.")
STORY = (FIRST + " It heels 35 degrees as it hits the water, throwing up a wall of water. "
         "The ferry keeps rolling as the wave slams onto the quay and six workers run back.")
SCEN = {"visible_start": FIRST, "beat1_action_verb": "tips"}


def n_fails(story, event=SIDE_LAUNCH_EVENT):
    return [m for m, _ in pg._simplified_checks(story, SCEN, D, "Passenger Car Ferry", event)
            if m.startswith(pg.SIMPLIFIER_GATES["N"])]


class TestNoSlipway(unittest.TestCase):
    def test_names_have_no_slipway(self):
        self.assertNotIn("slipway", SIDE_LAUNCH_EVENT.lower())
        self.assertNotIn("slipway", SIDE_LAUNCH_ENV.lower())
        self.assertEqual(SIDE_LAUNCH_ENV, "Side-launch berth at the quay edge")
        self.assertIn(SIDE_LAUNCH_ENV, DOMAIN_ATTRIBUTES[D]["environments"])

    def test_suffix_has_no_slipway(self):
        for cam in ("fixed_cctv", "bystander_handheld"):
            self.assertNotIn("slipway", style_lock_suffix(cam, CAT).lower())

    def test_writer_message_has_no_slipway_except_ban(self):
        mock = AsyncMock(return_value={})
        base = {"domain_title": "t", "guidance": "Slipway launches on inclined slipway rails",
                "example_elements": ["inclined slipway rails"], "camera_styles": [],
                "existing_library_reference": ["[x]: A restraining cable snaps early on a shipyard slipway.",
                                               "[y]: A wave crashes over the bow."]}
        with patch.object(pg, "_call_gpt", mock):
            asyncio.run(pg._generate_scenario({**base, **CAT}, "fixed_cctv"))
        user = mock.call_args.args[1]
        # Tek izinli geçiş: "Never write 'slipway'" yasağı
        self.assertEqual(user.lower().count("slipway"), 1, user)
        self.assertIn("Never write 'slipway'", user)
        self.assertIn("A wave crashes over the bow.", user)


class TestGateN(unittest.TestCase):
    def test_good_story_passes(self):
        self.assertTrue(45 <= len(STORY.split()) <= 60)
        self.assertEqual(pg._simplified_checks(STORY, SCEN, D, "Passenger Car Ferry", SIDE_LAUNCH_EVENT), [])

    def test_slipway_rejected(self):
        self.assertTrue(n_fails(STORY.replace("quay edge", "slipway", 1)))

    def test_bow_or_stern_first_rejected(self):
        for w in ("bow-first", "stern first"):
            with self.subTest(w=w):
                self.assertTrue(n_fails(STORY.replace("hits the water", f"hits the water {w}")))

    def test_first_sentence_must_be_side_fall(self):
        bad = STORY.replace("its entire long side facing the camera, tips sideways off the quay edge and drops "
                            "broadside into the water", "tips off the quay edge and drops into the water")
        self.assertTrue(n_fails(bad))

    def test_other_events_unaffected(self):
        self.assertFalse(n_fails(STORY.replace("quay edge", "slipway", 1), event="Drydock flood gate bursts open"))

    def test_rewrite_validator_applies_n(self):
        v = pg.make_story_validator({"scenario": SCEN, "domain_id": D, "ship": "Passenger Car Ferry",
                                     "event": SIDE_LAUNCH_EVENT})
        self.assertTrue([m for m, _ in v(STORY.replace("quay edge", "slipway", 1)) if "side launch" in m])

    def test_tips_is_trigger(self):
        """K1 dry-run: 4 side launch adayı 'tips sideways off the quay edge' tetiği yüzünden eleniyordu."""
        sc = {"visible_start": FIRST, "physical_movement": "It heels 35 degrees.",
              "visible_trigger": "The passenger car ferry tips sideways off the quay edge"}
        self.assertEqual(pg.validate_visible_trigger(sc, D), (True, []))

    def test_scenario_gate(self):
        sc = {"scenario_summary": "The ferry tips sideways off the quay edge and a wave slams onto the quay.",
              "visible_start": FIRST, "physical_movement": "It heels 35 degrees into the water.",
              "visible_consequence": "The ferry keeps rolling as the wave slams onto the quay and six workers run back."}
        self.assertTrue(pg.validate_scene_physics(sc, CAT)[0])
        bad = {**sc, "visible_start": "The passenger car ferry slides bow-first down the slipway into the water."}
        ok, f = pg.validate_scene_physics(bad, CAT)
        self.assertFalse(ok)
        self.assertTrue(any("yasak ifade" in x for x in f) and any("ilk cümle" in x for x in f), f)


class TestRanking(unittest.TestCase):
    """K1 dry-run: 5/5 geçti ama skor vinç adayını (8) side launch'lara (4-5) tercih etti."""

    def _cand(self, event, score, domain=D):
        return {"catalyst": {"domain_id": domain, "forced_event": event}, "score": score, "scenario": {}}

    def test_side_launch_mostly_first(self):
        cands = [self._cand(SIDE_LAUNCH_EVENT, 4), self._cand(SIDE_LAUNCH_EVENT, 5),
                 self._cand("Crane sling snaps while lowering the hull into the water", 8),
                 self._cand("Timber shores snap and the hull tips on its keel blocks", 7)]
        first = [pg.rank_candidates(cands)[0] for _ in range(1000)]
        side = sum(c["catalyst"]["forced_event"] == SIDE_LAUNCH_EVENT for c in first)
        self.assertGreater(side, 750)     # beklenen 10/12 ≈ %83
        self.assertLess(side, 950)        # diğer olaylar tamamen kaybolmaz
        # grup içinde skor sırası: side launch seçildiğinde önce skor 5
        self.assertTrue(all(c["score"] == 5 for c in first if c["catalyst"]["forced_event"] == SIDE_LAUNCH_EVENT))

    def test_unweighted_domain_score_order(self):
        cands = [self._cand("a", 3, "ferry_operations"), self._cand("b", 9, "ferry_operations")]
        self.assertEqual([c["score"] for c in pg.rank_candidates(cands)], [9, 3])


if __name__ == "__main__":
    unittest.main()
