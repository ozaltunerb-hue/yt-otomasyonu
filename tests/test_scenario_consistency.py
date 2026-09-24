#!/usr/bin/env python3
"""
Özet ↔ beat tutarlılığı (validate_scenario_consistency), 2026-09-24 TUR 6.

Faz 3: özet "beachgoers scramble for safety" diyordu, 3 beat'te insan yoktu; simplifier özeti de
okuduğu için insanlar Kie prompt'una taşındı. Kaynak düzeltmesi: yazıcı kuralı + bu kapı.
Gerçek API çağrısı yapılmaz.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.creative_engine import MARITIME_INSPIRATION_DOMAINS, build_scenario_writer_system
from core.prompt_generator import _person_mentions, validate_scenario_consistency

FAZ3_BEACH = {  # gerçek Faz 3 kazananı (2026-09-24)
    "scenario_summary": "Sudden towering waves crash onto a coastal resort beach, sweeping away chairs and "
                        "washing over the promenade as beachgoers scramble for safety.",
    "visible_start": "Massive waves slam onto the sandy beach, sending water rushing towards the beach chairs and umbrellas.",
    "physical_movement": "The waves surge forward with powerful force, lifting and dragging beach chairs and sand "
                         "toys away from their spots, creating a chaotic scene.",
    "visible_consequence": "The water continues to flood over the beach, rushing across the promenade and leaving "
                           "a trail of scattered beach equipment in its wake.",
}
N14_BEACH = {  # gerçek N14 senaryosu
    "scenario_summary": "A powerful ocean wave crashes over a coastal road, forcing people to flee the beach as the "
                        "water surges onto the street.",
    "visible_start": "A massive wave crests and crashes fiercely onto the sandy beach, sending water rushing toward the coastal road.",
    "physical_movement": "The wave sweeps across the beach and slams into the road, quickly inundating it with a torrent of water.",
    "visible_consequence": "Floodwaters continue to push inland, covering the street and sidewalks, with debris "
                           "floating and swirling in the powerful current.",
}


class TestConsistency(unittest.TestCase):
    def test_real_summary_introduces_people(self):
        for name, sc in (("faz3", FAZ3_BEACH), ("n14", N14_BEACH)):
            with self.subTest(name):
                ok, failures = validate_scenario_consistency(sc)
                self.assertFalse(ok)
                self.assertIn("Özet beat'lerde olmayan insanlardan bahsediyor", failures[0])

    def test_no_people_anywhere_passes(self):
        sc = {**FAZ3_BEACH, "scenario_summary": "Towering waves crash onto a resort beach and flood the promenade."}
        self.assertEqual(validate_scenario_consistency(sc), (True, []))

    def test_people_in_beats_and_summary_passes(self):
        sc = {**FAZ3_BEACH, "physical_movement": "The waves surge forward as two beachgoers sprint up the sand."}
        self.assertTrue(validate_scenario_consistency(sc)[0])

    def test_people_only_in_beats_passes(self):
        sc = {"scenario_summary": "A mooring line snaps at the marina.",
              "visible_start": "A mooring line snaps as three dockworkers leap back."}
        self.assertTrue(validate_scenario_consistency(sc)[0])

    def test_object_phrases_not_people(self):
        sc = {**FAZ3_BEACH, "scenario_summary": "Waves crash over the guard rail and topple a lifeguard tower "
                                                "beside a man-made breakwater near the passenger car ferry terminal."}
        self.assertEqual(validate_scenario_consistency(sc), (True, []))


class TestPersonMentions(unittest.TestCase):
    def test_false_friends(self):
        for text in ("the guard rail bends", "guardrails twist", "a lifeguard tower collapses",
                     "lifeguard stands topple", "a man-made jetty", "the Passenger Car Ferry rolls",
                     "the passenger deck floods", "crew quarters flood", "the crew boat lurches"):
            with self.subTest(text=text):
                self.assertEqual(_person_mentions(text), [])

    def test_real_people_still_found(self):
        for text, expected in (("a guard waves", ["guard"]), ("two lifeguards sprint", ["lifeguards"]),
                               ("a man slips", ["man"]), ("passengers scatter", ["passengers"]),
                               ("the crew scrambles", ["crew"]), ("beachgoers flee", ["beachgoers"])):
            with self.subTest(text=text):
                self.assertEqual(_person_mentions(text), expected)


class TestWriterRule(unittest.TestCase):
    def test_summary_instruction_in_all_domains(self):
        for d in MARITIME_INSPIRATION_DOMAINS:
            with self.subTest(domain=d):
                s = build_scenario_writer_system(15, d)
                self.assertIn("must not introduce any person, vessel, or object that is not in visible_start", s)
                self.assertNotIn("the normal moment", s)


if __name__ == "__main__":
    unittest.main()
