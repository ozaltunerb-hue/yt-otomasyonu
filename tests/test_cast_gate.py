#!/usr/bin/env python3
"""
Cast sayı kapısı (validate_cast_size) ve rotasyonun sadece geçerli combo sayması (2026-09-24).

Fixture'daki 12 senaryo, cast tablosu sonrası gerçek dry-run'lardan (N10, N14, N14b, N14c)
alındı. Tek red beklenen: N14c ferry, "four crew members and about a dozen passengers" = 16.
Gerçek API çağrısı yapılmaz.
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.creative_engine import DOMAIN_CAST_RANGES, ENV_CENTRIC_DOMAINS, get_creative_catalyst
from core.prompt_generator import validate_cast_size

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "cast_scenarios.json")

WORDS = "zero one two three four five six seven eight nine ten eleven twelve".split()


def sc(start, move="The deck lurches violently.", cons="Water keeps surging across the deck."):
    return {"visible_start": start, "physical_movement": move, "visible_consequence": cons}


class TestRealScenarios(unittest.TestCase):
    def test_post_cast_table_dry_runs(self):
        rows = json.load(open(FIXTURE, encoding="utf-8"))
        self.assertEqual(len(rows), 12)
        for r in rows:
            with self.subTest(run=r["run"], domain=r["domain"], start=r["visible_start"][:50]):
                ok, failures = validate_cast_size(r, r["domain"])
                self.assertEqual(ok, r["expect_ok"], failures)

    def test_n14c_ferry_sums_groups(self):
        ok, failures = validate_cast_size(sc(
            "Water gushes onto the open vehicle deck where four crew members in high-visibility "
            "coveralls and about a dozen passengers are quickly stepping away."), "ferry_operations")
        self.assertFalse(ok)
        self.assertIn("16 kişi", failures[0])


class TestRangeBounds(unittest.TestCase):
    def test_each_domain_exact_bounds(self):
        for d, (lo, hi) in DOMAIN_CAST_RANGES.items():
            for n, expected in ((lo - 1, False), (lo, True), (hi, True), (hi + 1, False)):
                start = f"{n} workers brace as a wave slams the hull."
                with self.subTest(domain=d, n=n):
                    self.assertEqual(validate_cast_size(sc(start), d)[0], expected)

    def test_hedge_tolerance(self):
        # ferry 2-5: hedge'li üstte +1 (5'in %20'si), altta -1
        ferry = "ferry_operations"
        self.assertTrue(validate_cast_size(sc("About six deckhands scramble as cars slide."), ferry)[0])
        self.assertFalse(validate_cast_size(sc("About seven deckhands scramble as cars slide."), ferry)[0])
        self.assertFalse(validate_cast_size(sc("Six deckhands scramble as cars slide."), ferry)[0])
        self.assertTrue(validate_cast_size(sc("Roughly one deckhand scrambles as cars slide."), ferry)[0])
        # cruise 8-25: üstte +5
        self.assertTrue(validate_cast_size(sc("About thirty passengers scatter as a wave hits."), "cruise_ship_operations")[0])
        self.assertFalse(validate_cast_size(sc("About thirty-one passengers scatter as a wave hits."), "cruise_ship_operations")[0])

    def test_number_forms(self):
        cases = {
            "A dozen passengers scatter as the wave hits.": 12,
            "Twenty-two passengers scatter as the wave hits.": 22,
            "14 passengers scatter as the wave hits.": 14,
        }
        for start, n in cases.items():
            with self.subTest(start=start):
                ok, failures = validate_cast_size(sc(start), "cruise_ship_operations")
                self.assertTrue(ok, failures)
        self.assertTrue(validate_cast_size(sc("A couple of deckhands grab the rail as cars slide."), "ferry_operations")[0])
        self.assertTrue(validate_cast_size(sc("Half a dozen guests duck as the line snaps."), "marina_and_yacht_operations")[0])


class TestVagueAndMissing(unittest.TestCase):
    def test_vague_terms_rejected(self):
        for start in ("Several deckhands scramble as cars slide.",
                      "A few crew members scramble as cars slide.",
                      "A group of passengers scatter as cars slide.",
                      "Dozens of passengers scatter as cars slide."):
            with self.subTest(start=start):
                ok, failures = validate_cast_size(sc(start), "ferry_operations")
                self.assertFalse(ok)
                self.assertIn("belirsiz", failures[0])

    def test_people_without_number_rejected(self):
        ok, failures = validate_cast_size(sc("Crew members scramble as cars slide."), "ferry_operations")
        self.assertFalse(ok)
        self.assertIn("sayı yok", failures[0])

    def test_no_people_rejected(self):
        ok, failures = validate_cast_size(sc("Cars slide violently across the flooded deck."), "ferry_operations")
        self.assertFalse(ok)
        self.assertIn("tanınan sayılı kişi ifadesi yok", failures[0])


class TestAcrossBeats(unittest.TestCase):
    D = "shipyard_and_drydock_engineering"  # 2-5

    def test_more_people_later_rejected(self):
        ok, failures = validate_cast_size(sc(
            "Three workers step back as the hull slides.",
            cons="Five workers are still running as the hull keeps sliding."), self.D)
        self.assertFalse(ok)
        self.assertIn("Beat 3", failures[0])

    def test_same_or_fewer_later_accepted(self):
        for cons in ("The three workers are still running as the hull keeps sliding.",
                     "Two workers are still running as the hull keeps sliding.",
                     "One of the workers keeps waving as the hull slides."):
            with self.subTest(cons=cons):
                self.assertTrue(validate_cast_size(sc("Three workers step back as the hull slides.", cons=cons), self.D)[0])

    def test_subset_not_added_in_beat1(self):
        ok, failures = validate_cast_size(sc("Three workers step back as one of the workers slips."), self.D)
        self.assertTrue(ok, failures)


class TestFalsePositives(unittest.TestCase):
    def test_non_person_numbers_ignored(self):
        ok, failures = validate_cast_size(sc(
            "Two deckhands grab the rail as at least two cars slide.",
            move="Two cars slide as deckhands brace, three chairs tumble.",
            cons="Four cars keep sliding toward the rail."), "ferry_operations")
        self.assertTrue(ok, failures)

    def test_beat_labels_stripped(self):
        ok, failures = validate_cast_size(sc(
            "BEAT 1: Three workers step back as the hull slides.",
            move="BEAT 2 (1-8s): The hull slams the rails.",
            cons="BEAT 3 (9-15s): The hull keeps sliding."), "shipyard_and_drydock_engineering")
        self.assertTrue(ok, failures)


class TestEnvCentricSkipped(unittest.TestCase):
    def test_env_centric_domains(self):
        for d in ENV_CENTRIC_DOMAINS:
            with self.subTest(domain=d):
                self.assertEqual(validate_cast_size(sc("A massive wave crashes onto the beach."), d), (True, []))


class TestRotationOnlyValidCombos(unittest.TestCase):
    VALID = [  # 6 geçerli domain, eskiden yeniye; pencere 6 (7 domain - 1)
        "cruise_ship_operations|mega cruise ship|bow thruster docking failure|open-air pool deck|fixed_cctv",
        "ferry_operations|passenger car ferry|secured vehicles breaking loose|island crossing route|chase_pov",
        "marina_and_yacht_operations|runaway powerboat|wake collision|marina fairway|bystander_handheld",
        "shipyard_and_drydock_engineering|sailing yacht|drydock flooding instability|shipyard basin|fixed_cctv",
        "coastal_tornado_landfall|sailing yacht|tornado landfall|harbor area|bystander_handheld",
        "urban_city_disasters|none|skyscraper glass failure|downtown street|fixed_cctv",
    ]
    TEST_LINE = "TEST — 2026-09-23 03:38 | cruise_ship_operations | fixed_cctv | As a mega cruise ship attempts to dock"

    def _choices(self, history):
        return {get_creative_catalyst(recent_history=history)["domain_id"] for _ in range(60)}

    def test_pipe_topic_line_does_not_take_rotation_slot(self):
        # Eski kod TEST satırını (4 parça) domain sayıyordu: pencere v2..v6+TEST olur, en eski
        # geçerli domain (cruise) dışlanmaz ve tekrar seçilebilirdi.
        self.assertEqual(self._choices(self.VALID + [self.TEST_LINE]), {"open_beach_coastal_events"})

    def test_old_format_lines_ignored(self):
        old = ["harbor_pilotage_and_berthing|harbor tugboat|tugboat loses mooring line",
               "arctic_ice_navigation|arctic lng carrier|ice floe collision|frozen pack ice|chase_pov"]
        self.assertEqual(self._choices(self.VALID + old), {"open_beach_coastal_events"})


if __name__ == "__main__":
    unittest.main()
