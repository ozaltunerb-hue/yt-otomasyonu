#!/usr/bin/env python3
"""
TUR 16 (2026-09-24): her videoda en az bir insan. Env-centric'te sayı serbest ama 0 insan red
(senaryo kapısı + simplifier H). Gemi domainlerinde DOMAIN_CAST_RANGES davranışı aynen. Gerçek API yok.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.creative_engine import (
    DOMAIN_CAST_RANGES,
    ENV_CENTRIC_DOMAINS,
    build_prompt_simplifier_system,
    build_scenario_writer_system,
)
from core.prompt_generator import validate_cast_size, validate_simplified_prompt

H = "Simplifier: insan yok"


def h(prompt, domain, ship=""):
    return [f for f in validate_simplified_prompt(prompt, {}, domain, ship)[1] if f.startswith(H)]


class TestRules(unittest.TestCase):
    def test_writer_env_requires_human(self):
        for d in ENV_CENTRIC_DOMAINS:
            with self.subTest(domain=d):
                s = build_scenario_writer_system(15, d)
                self.assertIn("at least one human must be visible and explicitly named", s)
                self.assertIn("Never a zero-human scene", s)
                self.assertIn("hi-vis hero charging toward the danger is forbidden", s)
                self.assertNotIn("CAST OPTIONAL", s)

    def test_writer_vessel_unchanged(self):
        for d, (lo, hi) in DOMAIN_CAST_RANGES.items():
            with self.subTest(domain=d):
                s = build_scenario_writer_system(15, d)
                self.assertIn(f"approximately {lo}-{hi} people", s)
                self.assertNotIn("Never a zero-human scene", s)

    def test_simplifier_env_keeps_humans(self):
        for d in ENV_CENTRIC_DOMAINS:
            self.assertIn("never drop all humans", build_prompt_simplifier_system(15, d))


class TestGateH(unittest.TestCase):
    def test_zero_humans_rejected(self):
        for d in ENV_CENTRIC_DOMAINS:
            with self.subTest(domain=d):
                self.assertTrue(h("A tornado tears across the beach, flinging chairs. Debris keeps swirling.", d))

    def test_background_humans_pass(self):
        for phrase in ["rooftop watchers stare", "sidewalk bystanders scatter", "distant figures run",
                       "a crowd gathers", "pedestrians flee", "observers film it"]:
            with self.subTest(phrase=phrase):
                p = f"A tsunami surges up the avenue as {phrase}. Water keeps rising."
                self.assertFalse(h(p, "urban_city_disasters"))

    def test_tornado_marina(self):
        self.assertTrue(h("A tornado spins toward the marina, lifting the sailing yacht. It keeps spinning.",
                          "coastal_tornado_landfall", "Sailing Yacht"))
        self.assertFalse(h("A tornado spins toward the marina as dock onlookers run. The yacht keeps spinning.",
                           "coastal_tornado_landfall", "Sailing Yacht"))

    def test_vessel_domains_not_affected(self):
        # Gemi domainlerinde H yok; kişi kontrolü E (sayı sadakati) ile yapılır
        for d in DOMAIN_CAST_RANGES:
            with self.subTest(domain=d):
                self.assertFalse(h("The passenger car ferry rolls hard. Cars keep sliding.", d, "Passenger Car Ferry"))

    def test_false_friends_not_people(self):
        self.assertTrue(h("A tsunami floods the passenger ferry terminal and guard rails. Water keeps rising.",
                          "urban_city_disasters"))


class TestScenarioGate(unittest.TestCase):
    def test_vessel_range_unchanged(self):
        ok, failures = validate_cast_size({"visible_start": "The ferry rolls as nine deckhands grab the rail."},
                                          "ferry_operations")
        self.assertFalse(ok)
        self.assertIn("üst sınır 5", failures[0])


if __name__ == "__main__":
    unittest.main()
